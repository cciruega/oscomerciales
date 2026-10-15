# -*- coding: utf-8 -*-
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

# Configurar la página antes de ejecutar cualquier comando visual de Streamlit.
st.set_page_config(
    page_title="Órdenes Comerciales Pendientes",
    page_icon="📋",
    layout="centered",
)

# Si falta el módulo o tiene un error de importación, mostrar el motivo en la página
# en lugar de dejar una pantalla aparentemente en blanco.
try:
    from procesador_os import ETAPAS_VALIDAS, REGIONES, UMBRAL_HORAS, procesar_archivo
except Exception as exc:
    st.title("Órdenes Comerciales Pendientes")
    st.error("No se pudo cargar el módulo procesador_os.py.")
    st.markdown(
        "Verifica que **procesador_os.py** esté en la misma carpeta de GitHub que **app.py** "
        "y que el archivo se llame exactamente `procesador_os.py` (no `procesador_os_integracion_corregida.py`)."
    )
    st.code(f"{type(exc).__name__}: {exc}")
    st.stop()

st.markdown("""
<style>
    .block-container { max-width: 980px; padding-top: 1.25rem; padding-bottom: 2rem; }
    .portal-title { text-align: center; font-size: 1.65rem; line-height: 1.18; font-weight: 800; color: #111827; margin: 0 0 1.5rem 0; }
    .region-title { font-size: 1.22rem; font-weight: 800; letter-spacing: .01em; color: #111827; margin: .2rem 0 0 0; }
    .region-subtitle { font-size: .82rem; color: #374151; margin-top: .15rem; }
    .small-meta { font-size: .8rem; color: #4b5563; margin: .25rem 0 .55rem 0; }
    div[data-testid="stFileUploader"] section { padding: .45rem .65rem; }
    div[data-testid="stFileUploader"] section div[data-testid="stMarkdownContainer"] p { font-size: .82rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #b7d9e5; border-radius: 3px; }
    .summary-table-wrap { display: block; width: 100%; max-width: 100%; margin: 0; }
    .summary-table-wrap table.os-summary-table { width: max-content !important; max-width: 100%; table-layout: auto; border-collapse: collapse; margin: 0; }
    .summary-table-wrap table.os-summary-table th,
    .summary-table-wrap table.os-summary-table td { white-space: nowrap; }
    .summary-table-wrap table.os-summary-table th { text-align: left; }
    .summary-table-wrap table.os-summary-table td { text-align: right; }
    .summary-table-wrap table.os-summary-table td:first-child { text-align: left; }
    hr { margin: 1.05rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="portal-title">ORDENES COMERCIALES<br>PENDIENTES</div>', unsafe_allow_html=True)
st.caption("Carga cada sábana TXT por separado. Las tablas y el Excel integrado incluyen únicamente folios con etapa válida y dilación desde la hora 25.")

@st.cache_data(show_spinner=False, max_entries=6)
def procesar_en_cache(contenido: bytes, region: str, version_lector: str):
    # version_lector cambia la clave de caché cuando se corrige el parser, para
    # no reutilizar un resultado anterior calculado con una versión defectuosa.
    return procesar_archivo(contenido, region)

resultados = {}

for idx, region in enumerate(REGIONES, start=1):
    st.markdown('<div class="region-title">{}</div>'.format(region), unsafe_allow_html=True)
    st.markdown('<div class="region-subtitle">Folios mayores a 24 hrs (desde hora 25)</div>'.format(UMBRAL_HORAS), unsafe_allow_html=True)
    archivo = st.file_uploader(
        f"Subir sábana TXT de {region.title()}",
        type=["txt", "csv"],
        key=f"archivo_{idx}",
        help="Selecciona el archivo descargado de la intranet. Debe ser una sábana delimitada por el carácter |.",
    )
    if archivo is not None:
        try:
            with st.spinner(f"Procesando {region}…"):
                resultado = procesar_en_cache(archivo.getvalue(), region, "recuperacion-linea-aislada-v1")
            resultados[region] = resultado
            m = resultado["metricas"]
            st.markdown(
                f'<div class="small-meta">Registros leídos: <b>{m["filas_leidas"]:,}</b> '
                f'&nbsp;·&nbsp; Etapas válidas: <b>{m["etapas_validas"]:,}</b> '
                f'&nbsp;·&nbsp; Folios desde hora 25: <b>{m["folios_25_mas"]:,}</b></div>',
                unsafe_allow_html=True,
            )
            if m["advertencias"]:
                for aviso in m["advertencias"]:
                    st.warning(aviso)
            if not resultado["resumen"].empty:
                tabla = resultado["resumen"]
                # Render HTML estático para que las columnas se ajusten al contenido y al encabezado.
                # Esta tabla resumen tiene pocas columnas y no necesita scroll interactivo.
                styler = (
                    tabla.style
                    .set_table_attributes('class="os-summary-table"')
                    .set_table_styles([
                        {"selector": "table", "props": [("width", "max-content"), ("max-width", "100%"), ("table-layout", "auto"), ("border-collapse", "collapse")]},
                        {"selector": "thead th", "props": [("background-color", "#d7eef6"), ("color", "#111827"), ("font-weight", "bold"), ("border", "1px solid #a9cbd7"), ("font-size", "12px"), ("padding", "4px 7px"), ("white-space", "nowrap")]},
