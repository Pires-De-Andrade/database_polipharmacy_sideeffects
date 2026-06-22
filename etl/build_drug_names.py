"""
Gera o mapa estático de nomes de medicamentos (STITCH ID → nome legível).

Os CSVs do DECAGON só fornecem o identificador STITCH (ex: CID000002173), que
corresponde ao PubChem Compound ID (CID 2173). Este script resolve os ~645 IDs
distintos via API pública PubChem PUG-REST (gratuita) e grava o resultado em
`app/data/drug_names.json`.

O JSON é consumido em runtime pela app Streamlit (selector.py) para rotular os
dropdowns — sem nunca tocar na coluna `drug.name` do banco. Como o arquivo é
commitado no repo, a app funciona offline e serve tanto o banco local quanto o
oficial na nuvem.

Uso (uma única vez, ou para atualizar):
    python etl/build_drug_names.py
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT = PROJECT_ROOT / "app" / "data" / "drug_names.json"

TITLE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids}/property/Title/JSON"
SYNONYM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
BATCH_SIZE = 100          # PUG-REST aceita muitos CIDs por requisição
RATE_LIMIT_SLEEP = 0.25   # PubChem permite ~5 req/s; folga de segurança

# Tag de Denominação Comum Internacional em inglês: "BUPROPION [INN]".
# É o único sinônimo confiável; os demais incluem códigos e nomes comerciais.
INN_RE = re.compile(r"\s*\[INN\]\s*$")


def collect_stitch_ids() -> list[str]:
    """Lê os STITCH IDs distintos dos CSVs do DECAGON (sem depender do banco)."""
    ids: set[str] = set()
    sources = [
        ("bio-decagon-combo.csv", (0, 1)),   # STITCH 1, STITCH 2
        ("bio-decagon-mono.csv", (0,)),      # STITCH
        ("bio-decagon-targets.csv", (0,)),   # STITCH
    ]
    for filename, cols in sources:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  aviso: {filename} não encontrado, ignorando.", file=sys.stderr)
            continue
        with path.open(encoding="utf-8") as fh:
            next(fh, None)  # pular cabeçalho
            for line in fh:
                parts = line.rstrip("\n").split(",")
                for c in cols:
                    if c < len(parts) and parts[c].startswith("CID"):
                        ids.add(parts[c])
    return sorted(ids)


def stitch_to_cid(stitch_id: str) -> int:
    """CID000002173 → 2173 (remove prefixo, flag e zero-padding)."""
    digits = re.sub(r"\D", "", stitch_id)
    return int(digits)


def fetch_titles(cids: list[int]) -> dict[int, str]:
    """Busca o Title de uma lista de CIDs em lotes via PubChem."""
    titles: dict[int, str] = {}
    for start in range(0, len(cids), BATCH_SIZE):
        batch = cids[start:start + BATCH_SIZE]
        url = TITLE_URL.format(cids=",".join(str(c) for c in batch))
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            props = resp.json().get("PropertyTable", {}).get("Properties", [])
            for p in props:
                if "CID" in p and p.get("Title"):
                    titles[p["CID"]] = p["Title"]
        except Exception as e:
            print(f"  erro no lote {start}-{start + len(batch)}: {e}", file=sys.stderr)
        done = min(start + BATCH_SIZE, len(cids))
        print(f"  resolvidos {done}/{len(cids)} títulos…", file=sys.stderr)
        time.sleep(RATE_LIMIT_SLEEP)
    return titles


def is_systematic(title: str) -> bool:
    """Heurística: nomes IUPAC/sistemáticos contêm dígitos; nomes comuns não."""
    return any(ch.isdigit() for ch in title)


def fetch_inn(cid: int) -> str | None:
    """Retorna o nome INN inglês (sem a tag) se existir nos sinônimos do CID."""
    url = SYNONYM_URL.format(cid=cid)
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        info = resp.json().get("InformationList", {}).get("Information", [{}])[0]
        for syn in info.get("Synonym", []):
            if INN_RE.search(syn):
                name = INN_RE.sub("", syn).strip()
                # PubChem costuma gravar o INN em CAIXA ALTA; normaliza p/ Título.
                return name.title() if name.isupper() else name
    except Exception:
        pass
    return None


def main() -> None:
    print("Coletando STITCH IDs dos CSVs…", file=sys.stderr)
    stitch_ids = collect_stitch_ids()
    if not stitch_ids:
        print("Nenhum STITCH ID encontrado em data/. Abortando.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(stitch_ids)} medicamentos distintos.", file=sys.stderr)

    cid_to_stitch = {stitch_to_cid(s): s for s in stitch_ids}
    all_cids = sorted(cid_to_stitch)

    print("Consultando títulos na PubChem…", file=sys.stderr)
    titles_by_cid = fetch_titles(all_cids)

    name_map = {
        cid_to_stitch[cid]: title
        for cid, title in titles_by_cid.items()
        if cid in cid_to_stitch
    }

    # Fallback INN: para títulos sistemáticos (com dígitos) ou CIDs sem título,
    # tenta o nome INN inglês — único sinônimo confiável. Mantém o Title se não houver.
    candidates = [
        cid for cid in all_cids
        if cid not in titles_by_cid or is_systematic(titles_by_cid[cid])
    ]
    print(f"Buscando INN para {len(candidates)} nomes sistemáticos/ausentes…",
          file=sys.stderr)
    inn_hits = 0
    for i, cid in enumerate(candidates, 1):
        inn = fetch_inn(cid)
        if inn:
            name_map[cid_to_stitch[cid]] = inn
            inn_hits += 1
        if i % 50 == 0 or i == len(candidates):
            print(f"  {i}/{len(candidates)} (INN encontrados: {inn_hits})",
                  file=sys.stderr)
        time.sleep(RATE_LIMIT_SLEEP)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(name_map, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    covered = len(name_map)
    total = len(stitch_ids)
    print(
        f"OK: {covered}/{total} nomes resolvidos "
        f"({covered / total:.0%}) → {OUTPUT.relative_to(PROJECT_ROOT)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
