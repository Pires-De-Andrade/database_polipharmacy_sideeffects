"""
Layout e estilos CSS da aplicação Streamlit.

Injeta CSS personalizado para criar uma paleta clínica profissional,
afastando-se do aspecto padrão do Streamlit.
"""
import streamlit as st


def inject_css():
    """Injeta o CSS customizado da aplicação."""
    st.markdown("""
    <style>
    /* ── Google Fonts ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Base ─────────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* ── Header ───────────────────────────────────────────────────────── */
    .app-header {
        background: linear-gradient(135deg, #1B3A5C 0%, #2C5F8A 100%);
        padding: 1.8rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .app-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.85;
        font-weight: 300;
    }

    /* ── Métricas ─────────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #f0f4f8;
        border-left: 4px solid #1B3A5C;
        padding: 0.8rem 1rem;
        border-radius: 6px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem;
        font-weight: 500;
        color: #5a6d7e;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1B3A5C;
    }

    /* ── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid #e0e5ec;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.7rem 1.5rem;
        font-weight: 500;
        font-size: 0.88rem;
        color: #5a6d7e;
        border-bottom: 3px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #1B3A5C;
        border-bottom-color: #1B3A5C;
        font-weight: 600;
    }

    /* ── Botão de análise ─────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1B3A5C 0%, #2C5F8A 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 0.9rem;
        border-radius: 8px;
        transition: opacity 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        opacity: 0.9;
        color: white;
    }

    /* ── DataFrames ───────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* ── Blocos de código ─────────────────────────────────────────────── */
    .stCodeBlock {
        border-radius: 8px;
    }

    /* ── Separador e rodapé de query ──────────────────────────────────── */
    .query-footer {
        text-align: right;
        font-size: 0.78rem;
        color: #8899aa;
        margin-top: 0.8rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e8ecf0;
        font-style: italic;
    }

    /* ── Painel de interpretação ──────────────────────────────────────── */
    .interpretation-panel {
        background: #f7f9fb;
        border-left: 4px solid #2C5F8A;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
        line-height: 1.6;
        color: #2d3e50;
    }

    /* ── Painel não encontrado ────────────────────────────────────────── */
    .not-found-panel {
        background: #fef9e7;
        border-left: 4px solid #d4a017;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #6b5b00;
    }

    /* ── Status de conexão ────────────────────────────────────────────── */
    .conn-status {
        font-size: 0.75rem;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        display: inline-block;
        margin-right: 0.5rem;
    }
    .conn-ok {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .conn-err {
        background: #fce4ec;
        color: #c62828;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Renderiza o header principal da aplicação."""
    st.markdown("""
    <div class="app-header">
        <h1>Sistema de Consulta de Risco Farmacológico</h1>
        <p>Avaliação de combinações medicamentosas com base em dados observacionais — Projeto DECAGON / SNAP Stanford</p>
    </div>
    """, unsafe_allow_html=True)


def render_query_footer(label: str, time_ms: float):
    """Renderiza o rodapé com tempo de execução de uma query."""
    st.markdown(
        f'<div class="query-footer">Query {label} executada em {time_ms:.1f}ms</div>',
        unsafe_allow_html=True,
    )
