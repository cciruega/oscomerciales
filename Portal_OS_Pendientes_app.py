# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import re
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
    from procesador_os import ETAPAS_VALIDAS, REGIONES, UMBRAL_HORAS, VERSION_LECTOR, procesar_archivo
except Exception as exc:
    st.title("Órdenes Comerciales Pendientes")
    st.error("No se pudo cargar el módulo procesador_os.py.")
    st.markdown(
        "Verifica que **procesador_os.py** esté en la misma carpeta de GitHub que **app.py** "
        "y que el archivo se llame exactamente `procesador_os.py` (no `procesador_os_integracion_corregida.py`)."
    )
    st.code(f"{type(exc).__name__}: {exc}")
    st.stop()


# Excel/OpenXML no admite ciertos caracteres de control en las celdas.
# Se eliminan solo esos caracteres, nunca filas ni columnas.
_CARACTERES_NO_VALIDOS_EXCEL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

def _preparar_dataframe_excel(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    seguro = df.copy()
    eliminados = 0
    columnas = []
    for nombre in seguro.columns:
        limpio, n = _CARACTERES_NO_VALIDOS_EXCEL.subn("", str(nombre))
        columnas.append(limpio)
        eliminados += n
    seguro.columns = columnas
    for nombre in seguro.columns:
        serie = seguro[nombre]
        if pd.api.types.is_object_dtype(serie.dtype) or pd.api.types.is_string_dtype(serie.dtype):
            texto = serie.astype("string")
            eliminados += int(texto.str.count(_CARACTERES_NO_VALIDOS_EXCEL).fillna(0).sum())
            seguro[nombre] = texto.str.replace(_CARACTERES_NO_VALIDOS_EXCEL, "", regex=True).fillna("")
    return seguro, eliminados

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
st.caption("Carga cada sábana TXT por separado. Las tablas y el Excel integrado incluyen únicamente folios con etapa válida y dilación desde la hora 5.")

@st.cache_data(show_spinner=False, max_entries=6)
def procesar_en_cache(contenido: bytes, region: str, version_lector: str):
    # version_lector cambia la clave de caché cuando se corrige el parser, para
    # no reutilizar un resultado anterior calculado con una versión defectuosa.
    return procesar_archivo(contenido, region)

resultados = {}

for idx, region in enumerate(REGIONES, start=1):
    st.markdown('<div class="region-title">{}</div>'.format(region), unsafe_allow_html=True)
    st.markdown('<div class="region-subtitle">Folios mayores a 5 hrs (desde hora 5)</div>'.format(UMBRAL_HORAS), unsafe_allow_html=True)
    archivo = st.file_uploader(
        f"Subir sábana TXT de {region.title()}",
        type=["txt", "csv"],
        key=f"archivo_{idx}",
        help="Selecciona el archivo descargado de la intranet. Debe ser una sábana delimitada por el carácter |.",
    )
    if archivo is not None:
        try:
            with st.spinner(f"Procesando {region}…"):
                resultado = procesar_en_cache(archivo.getvalue(), region, VERSION_LECTOR)
            resultados[region] = resultado
            m = resultado["metricas"]
            st.markdown(
                f'<div class="small-meta">Registros leídos: <b>{m["filas_leidas"]:,}</b> '
                f'&nbsp;·&nbsp; Etapas válidas: <b>{m["etapas_validas"]:,}</b> '
                f'&nbsp;·&nbsp; Folios desde hora 5: <b>{m["folios_5_mas"]:,}</b></div>',
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
                        {"selector": "tbody td", "props": [("border", "1px solid #d8e4e8"), ("font-size", "12px"), ("padding", "3px 7px"), ("white-space", "nowrap")]},
                        {"selector": "tbody tr:last-child td", "props": [("background-color", "#d7eef6"), ("font-weight", "bold")]},
                    ])
                    .hide(axis="index")
                )
                st.markdown(
                    f'<div class="summary-table-wrap">{styler.to_html()}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("No se encontraron folios que cumplan simultáneamente las etapas válidas y la dilación desde la hora 5.")
            with st.expander(f"Detalle de lectura y asignación — {region}"):
                st.write(f"**Columna de etapa detectada:** `{m['columna_etapa']}`")
                st.write(f"**Columna de dilación detectada:** `{m['columna_dilacion']}`" + (" (respaldo por posición BQ)" if m["dilacion_por_posicion"] else ""))
                st.write(f"**Codificación leída:** `{m['encoding']}` · **Tamaño:** {m['bytes'] / (1024*1024):.2f} MB")
                st.write("**Etapas consideradas:** " + ", ".join(ETAPAS_VALIDAS))
                if not resultado["detalle"].empty:
                    # La vista previa usa el detalle completo, no un recorte de 100 filas.
                    # Streamlit permite recorrer todo el conjunto dentro de la tabla.
                    st.dataframe(
                        resultado["detalle"],
                        use_container_width=True,
                        hide_index=True,
                        height=520,
                    )
                    st.caption(
                        f"Vista completa: {len(resultado['detalle']):,} folios pendientes. "
                        "Puedes recorrer todos los registros en la tabla; el Excel también incluye la totalidad."
                    )
        except Exception as exc:
            st.error(f"No se pudo procesar {region}: {exc}")
            st.info("Verifica que el archivo corresponda a esa región, que la descarga esté completa y que incluya los encabezados Etapa PISA y DilacionHorasEtapa.")
    else:
        st.caption("Selecciona el TXT de esta región para generar su tabla.")
    st.markdown("<hr>", unsafe_allow_html=True)

# Comparar volúmenes de regiones cargadas para detectar una sábana truncada.
integridad_sospechosa = any(v["metricas"]["filas_leidas"] < 10_000 for v in resultados.values())
if resultados:
    conteos = {r: v["metricas"]["filas_leidas"] for r, v in resultados.items()}
    valores = sorted(conteos.values())
    mediana = valores[len(valores) // 2]
    sospechosas = []
    for r, n in conteos.items():
        if n < 10_000 or (mediana and n < mediana * 0.25):
            sospechosas.append((r, n))
            integridad_sospechosa = True
    if sospechosas:
        detalle = "; ".join(f"{r}: {n:,} registros" for r, n in sospechosas)
        st.error("Revisión de integridad: el volumen de una o más sábanas es muy inferior al esperado. Revisa el TXT antes de confiar en el reporte. " + detalle)

if len(resultados) < len(REGIONES):
    st.info(f"Tablas mostradas: {len(resultados)} de {len(REGIONES)}. Carga las tres sábanas para habilitar la descarga del Excel integrado.")
elif integridad_sospechosa:
    st.error("La descarga del Excel integrado está bloqueada porque al menos una sábana parece incompleta. Corrige o vuelve a descargar ese TXT y cárgalo nuevamente.")
else:
    # Verificación cruzada: el detalle exportado debe contener exactamente las
    # filas contadas como folios desde la hora 5, y el resumen debe sumar lo mismo.
    errores_integracion = []
    for region in REGIONES:
        resultado = resultados[region]
        m = resultado["metricas"]
        filas_detalle = len(resultado["detalle"])
        if filas_detalle != m["folios_5_mas"]:
            errores_integracion.append(
                f"{region}: detalle={filas_detalle:,}, métrica >=5 h={m['folios_5_mas']:,}"
            )
        if not resultado["resumen"].empty and "Total general" in resultado["resumen"].columns:
            total_resumen = int(pd.to_numeric(resultado["resumen"]["Total general"], errors="coerce").fillna(0).iloc[-1])
            if total_resumen != m["folios_5_mas"]:
                errores_integracion.append(
                    f"{region}: resumen={total_resumen:,}, métrica >=5 h={m['folios_5_mas']:,}"
                )
        elif m["folios_5_mas"] != 0:
            errores_integracion.append(
                f"{region}: el resumen está vacío aunque se detectaron {m['folios_5_mas']:,} folios >=5 h"
            )

    if errores_integracion:
        st.error("Se bloqueó la integración porque los conteos de resumen y detalle no coinciden: " + "; ".join(errores_integracion))
    else:
        st.markdown("### Exportar resultados")
        st.caption("El Excel incluye un resumen por región, todos los folios pendientes (etapa válida y dilación ≥ 5 h) y una hoja de control. Los caracteres de control no admitidos por Excel se limpian sin eliminar registros.")
        buffer = io.BytesIO()
        caracteres_control_limpiados_excel = 0
        try:
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                control = []

                # Una pestaña consolidada con los folios pendientes de las tres regiones.
                detalle_integrado = pd.concat(
                    [resultados[region]["detalle"] for region in REGIONES],
                    ignore_index=True,
                )
                total_pendientes_esperado = sum(
                    int(resultados[region]["metricas"]["folios_5_mas"]) for region in REGIONES
                )
                if len(detalle_integrado) != total_pendientes_esperado:
                    raise ValueError(
                        f"Detalle Integrado contiene {len(detalle_integrado):,} filas, "
                        f"pero el control calcula {total_pendientes_esperado:,} folios pendientes."
                    )
                detalle_integrado_excel, n_limpios = _preparar_dataframe_excel(detalle_integrado)
                caracteres_control_limpiados_excel += n_limpios
                detalle_integrado_excel.to_excel(writer, sheet_name="Detalle Integrado", index=False)

                for region in REGIONES:
                    resultado = resultados[region]
                    m = resultado["metricas"]
                    sufijo = region.replace("MONTERREY ", "MTY ")
                    resumen_excel, n_limpios_resumen = _preparar_dataframe_excel(resultado["resumen"])
                    detalle_excel, n_limpios_detalle = _preparar_dataframe_excel(resultado["detalle"])
                    caracteres_control_limpiados_excel += n_limpios_resumen + n_limpios_detalle
                    resumen_excel.to_excel(writer, sheet_name=f"Resumen {sufijo}"[:31], index=False)
                    detalle_excel.to_excel(writer, sheet_name=f"Detalle {sufijo}"[:31], index=False)
                    control.append({
                        "Área": region,
                        "Registros leídos": m["filas_leidas"],
                        "Etapas válidas": m["etapas_validas"],
                        "Folios desde hora 5": m["folios_5_mas"],
                        "Filas exportadas en detalle": len(resultado["detalle"]),
                        "Diferencia detalle vs folios pendientes": len(resultado["detalle"]) - m["folios_5_mas"],
                        "Sin tienda asignada": m["sin_asignar"],
                        "Dilación vacía/no numérica": m["horas_invalidas"],
                        "Nombre columna etapa": m["columna_etapa"],
                        "Nombre columna dilación": m["columna_dilacion"],
                    })
                control.append({
                    "Área": "TOTAL TRES REGIONES",
                    "Registros leídos": sum(int(resultados[r]["metricas"]["filas_leidas"]) for r in REGIONES),
                    "Etapas válidas": sum(int(resultados[r]["metricas"]["etapas_validas"]) for r in REGIONES),
                    "Folios desde hora 5": total_pendientes_esperado,
                    "Filas exportadas en detalle": len(detalle_integrado),
                    "Diferencia detalle vs folios pendientes": len(detalle_integrado) - total_pendientes_esperado,
                    "Sin tienda asignada": sum(int(resultados[r]["metricas"]["sin_asignar"]) for r in REGIONES),
                    "Dilación vacía/no numérica": sum(int(resultados[r]["metricas"]["horas_invalidas"]) for r in REGIONES),
                    "Nombre columna etapa": "—",
                    "Nombre columna dilación": "—",
                })
                control_excel, n_limpios_control = _preparar_dataframe_excel(pd.DataFrame(control))
                caracteres_control_limpiados_excel += n_limpios_control
                control_excel.to_excel(writer, sheet_name="Control", index=False)
                for ws in writer.book.worksheets:
                    ws.freeze_panes = "A2"
                    ws.auto_filter.ref = ws.dimensions
                    for col_cells in ws.columns:
                        max_len = max((len(str(c.value or "")) for c in list(col_cells)[:300]), default=10)
                        ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 38)
            excel_bytes = buffer.getvalue()
            if caracteres_control_limpiados_excel:
                st.warning(
                    f"Para generar Excel se limpiaron {caracteres_control_limpiados_excel:,} caracteres de control "
                    "no admitidos por el formato. No se eliminaron folios, filas ni columnas."
                )
            st.download_button(
                "Descargar Excel integrado",
                data=excel_bytes,
                file_name=f"Ordenes_Comerciales_Pendientes_{datetime.now():%Y%m%d_%H%M}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
        except Exception as exc:
            st.error(f"No se pudo preparar el Excel: {exc}")

st.caption("El portal procesa los archivos que cargues en la instancia de Streamlit; al ejecutarlo en tu PC, los archivos se procesan en tu equipo. No descarga automáticamente de la intranet ni elimina los TXT originales.")
st.caption(f"Versión del lector de TXT: `{VERSION_LECTOR}`")
