                st.write("**Etapas consideradas:** " + ", ".join(ETAPAS_VALIDAS))
                if not resultado["detalle"].empty:
                    st.dataframe(resultado["detalle"].head(100), use_container_width=True, hide_index=True)
                    st.caption("Vista previa de hasta 100 folios pendientes exportados: etapa válida y dilación desde la hora 25.")
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
    # filas contadas como folios desde la hora 25, y el resumen debe sumar lo mismo.
    errores_integracion = []
    for region in REGIONES:
        resultado = resultados[region]
        m = resultado["metricas"]
        filas_detalle = len(resultado["detalle"])
        if filas_detalle != m["folios_25_mas"]:
            errores_integracion.append(
                f"{region}: detalle={filas_detalle:,}, métrica >=25 h={m['folios_25_mas']:,}"
            )
        if not resultado["resumen"].empty and "Total general" in resultado["resumen"].columns:
            total_resumen = int(pd.to_numeric(resultado["resumen"]["Total general"], errors="coerce").fillna(0).iloc[-1])
            if total_resumen != m["folios_25_mas"]:
                errores_integracion.append(
                    f"{region}: resumen={total_resumen:,}, métrica >=25 h={m['folios_25_mas']:,}"
                )
        elif m["folios_25_mas"] != 0:
            errores_integracion.append(
                f"{region}: el resumen está vacío aunque se detectaron {m['folios_25_mas']:,} folios >=25 h"
            )

    if errores_integracion:
        st.error("Se bloqueó la integración porque los conteos de resumen y detalle no coinciden: " + "; ".join(errores_integracion))
    else:
        st.markdown("### Exportar resultados")
        st.caption("El Excel incluye un resumen por región, el detalle completo de folios pendientes (etapa válida y dilación ≥ 25 h) y una hoja de control con conteos comparables.")
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                control = []

                # Una pestaña consolidada con los folios pendientes de las tres regiones.
                detalle_integrado = pd.concat(
                    [resultados[region]["detalle"] for region in REGIONES],
                    ignore_index=True,
                )
                total_pendientes_esperado = sum(
                    int(resultados[region]["metricas"]["folios_25_mas"]) for region in REGIONES
                )
                if len(detalle_integrado) != total_pendientes_esperado:
                    raise ValueError(
                        f"Detalle Integrado contiene {len(detalle_integrado):,} filas, "
                        f"pero el control calcula {total_pendientes_esperado:,} folios pendientes."
                    )
                detalle_integrado.to_excel(writer, sheet_name="Detalle Integrado", index=False)

                for region in REGIONES:
                    resultado = resultados[region]
                    m = resultado["metricas"]
                    sufijo = region.replace("MONTERREY ", "MTY ")
                    resultado["resumen"].to_excel(writer, sheet_name=f"Resumen {sufijo}"[:31], index=False)
                    resultado["detalle"].to_excel(writer, sheet_name=f"Detalle {sufijo}"[:31], index=False)
                    control.append({
                        "Área": region,
                        "Registros leídos": m["filas_leidas"],
                        "Etapas válidas": m["etapas_validas"],
                        "Folios desde hora 25": m["folios_25_mas"],
                        "Filas exportadas en detalle": len(resultado["detalle"]),
                        "Diferencia detalle vs folios pendientes": len(resultado["detalle"]) - m["folios_25_mas"],
                        "Sin tienda asignada": m["sin_asignar"],
                        "Dilación vacía/no numérica": m["horas_invalidas"],
                        "Nombre columna etapa": m["columna_etapa"],
                        "Nombre columna dilación": m["columna_dilacion"],
                    })
                control.append({
                    "Área": "TOTAL TRES REGIONES",
                    "Registros leídos": sum(int(resultados[r]["metricas"]["filas_leidas"]) for r in REGIONES),
                    "Etapas válidas": sum(int(resultados[r]["metricas"]["etapas_validas"]) for r in REGIONES),
                    "Folios desde hora 25": total_pendientes_esperado,
                    "Filas exportadas en detalle": len(detalle_integrado),
                    "Diferencia detalle vs folios pendientes": len(detalle_integrado) - total_pendientes_esperado,
                    "Sin tienda asignada": sum(int(resultados[r]["metricas"]["sin_asignar"]) for r in REGIONES),
                    "Dilación vacía/no numérica": sum(int(resultados[r]["metricas"]["horas_invalidas"]) for r in REGIONES),
                    "Nombre columna etapa": "—",
                    "Nombre columna dilación": "—",
                })
                pd.DataFrame(control).to_excel(writer, sheet_name="Control", index=False)
                for ws in writer.book.worksheets:
                    ws.freeze_panes = "A2"
                    ws.auto_filter.ref = ws.dimensions
                    for col_cells in ws.columns:
                        max_len = max((len(str(c.value or "")) for c in list(col_cells)[:300]), default=10)
                        ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 10), 38)
            excel_bytes = buffer.getvalue()
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
