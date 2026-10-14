# -*- coding: utf-8 -*-
"""Funciones de procesamiento para el Portal de Órdenes Comerciales Pendientes."""
from __future__ import annotations

import csv
import io
import math
import re
import unicodedata
from typing import Any

import pandas as pd

ETAPAS_VALIDAS = ["C8", "CD", "CL", "CO", "CP", "CW", "OQ", "SN", "TL", "PP"]
UMBRAL_HORAS = 25  # Hora 25 en adelante
REGIONES = ["MONTERREY 1", "MONTERREY 2", "MONTERREY 3"]

CENTRAL_MAP = {
    '95L': 'CAT GES',
    'AAB': 'CAT ALL',
    'ACE': 'CAT GPE',
    'AFO': 'CAT BRI',
    'AIG': 'CAT SCA',
    'AKA': 'CAT LIN',
    'ALL': 'CAT ALL',
    'AMB': 'CAT STD',
    'ANA': 'CAT PUN',
    'AOQ': 'CAT STD',
    'APO': 'CAT STD',
    'AUU': 'CAT BRI',
    'BDA': 'CAT GES',
    'BES': 'CAT GES',
    'BIT': 'CAT CAD',
    'BKL': 'CAT ECE',
    'BLN': 'CAT SFE',
    'BLX': 'CAT LIN',
    'BQN': 'CAT BRI',
    'BQS': 'CAT CAD',
    'BRI': 'CAT BRI',
    'BSD': 'CAT STD',
    'CAD': 'CAT CAD',
    'CAR': 'CAT CUA',
    'CBT': 'CAT VVE',
    'CEX': 'CAT GPE',
    'CGL': 'CAT MOM',
    'CHN': 'CAT CAD',
    'CIE': 'CAT STD',
    'CMT': 'CAT SCA',
    'CPI': 'CAT GES',
    'CPQ': 'CAT VAE',
    'CRB': 'CAT SFE',
    'CRV': 'CAT SCA',
    'CTB': 'CAT GES',
    'CUA': 'CAT CUA',
    'CVY': 'CAT SCA',
    'DAG': 'CAT BRI',
    'DEC': 'CAT PUN',
    'DGA': 'CAT BRI',
    'DOT': 'CAT GZL',
    'DRG': 'CAT BRI',
    'DRL': 'CAT BRI',
    'DRS': 'CAT LAS',
    'DUL': 'CAT STD',
    'EAS': 'CAT PUN',
    'EBD': 'CAT GES',
    'ECA': 'CAT STD',
    'ECE': 'CAT ECE',
    'ELB': 'CAT ECE',
    'EOW': 'CAT SCA',
    'ESM': 'CAT VVE',
    'ETD': 'CAT CAD',
    'ETV': 'CAT BRI',
    'EVO': 'CAT LAS',
    'EZL': 'CAT BRI',
    'FAL': 'CAT VVE',
    'FOY': 'CAT VVE',
    'FRL': 'CAT VVE',
    'FTR': 'CAT CON',
    'GAL': 'CAT LIN',
    'GBR': 'CAT CAD',
    'GDX': 'CAT BRI',
    'GDY': 'CAT BRI',
    'GEE': 'CAT BRI',
    'GES': 'CAT GES',
    'GID': 'CAT BRI',
    'GPE': 'CAT GPE',
    'GTE': 'CAT MOM',
    'GZU': 'CAT STD',
    'HCC': 'CAT PUN',
    'HCE': 'CAT STD',
    'HHS': 'CAT LIN',
    'HIA': 'CAT STD',
    'HKM': 'CAT STD',
    'HLR': 'CAT CAD',
    'HOD': 'CAT ALL',
    'HOT': 'CAT PUN',
    'HSJ': 'CAT STD',
    'IDV': 'CAT SFE',
    'IMX': 'CAT CAD',
    'INA': 'CAT STD',
    'INC': 'CAT BRI',
    'INM': 'CAT STD',
    'INP': 'CAT GZL',
    'IOS': 'CAT CAD',
    'ISO': 'CAT STD',
    'IST': 'CAT STD',
    'ITE': 'CAT STD',
    'JDS': 'CAT LAS',
    'JOY': 'CAT GPE',
    'LAE': 'CAT PUN',
    'LAP': 'CAT BRI',
    'LAS': 'CAT LAS',
    'LBN': 'CAT GZL',
    'LDE': 'CAT STD',
    'LEB': 'CAT STD',
    'LEO': 'CAT VVE',
    'LFA': 'CAT GZL',
    'LFQ': 'CAT GPE',
    'LFS': 'CAT STD',
    'LIN': 'CAT LIN',
    'LJM': 'CAT BRI',
    'LLB': 'CAT VVE',
    'LMD': 'CAT CAD',
    'LNE': 'CAT ECE',
    'LNO': 'CAT STD',
    'LNP': 'CAT CAD',
    'LOP': 'CAT GES',
    'LRO': 'CAT STD',
    'LSC': 'CAT SCA',
    'LVM': 'CAT BRI',
    'LVZ': 'CAT ECE',
    'LYX': 'CAT GES',
    'LZI': 'CAT ALL',
    'MAY': 'CAT CON',
    'MER': 'CAT STD',
    'MHK': 'CAT GZL',
    'MIT': 'CAT GZL',
    'MJS': 'CAT STD',
    'MLE': 'CAT ECE',
    'MLU': 'CAT SCA',
    'MOM': 'CAT MOM',
    'MQU': 'CAT STD',
    'MRI': 'CAT STD',
    'MRL': 'CAT PUN',
    'MSF': 'CAT LAS',
    'MSH': 'CAT STD',
    'MSK': 'CAT SCA',
    'MTB': 'CAT CAD',
    'MUF': 'CAT STD',
    'NAL': 'CAT CUA',
    'NEK': 'CAT SCA',
    'NNA': 'CAT STD',
    'NRP': 'CAT VAE',
    'NRS': 'CAT STD',
    'NRT': 'CAT VVE',
    'NSM': 'CAT SFE',
    'NSY': 'CAT CAD',
    'NVG': 'CAT VVE',
    'NVZ': 'CAT VVE',
    'OBI': 'CAT GZL',
    'OGW': 'CAT CON',
    'OIC': 'CAT CAD',
    'OIL': 'CAT VAE',
    'ONO': 'CAT GPE',
    'OOE': 'CAT VAE',
    'ORN': 'CAT SCA',
    'ORQ': 'CAT GPE',
    'OSJ': 'CAT CAD',
    'OSY': 'CAT VAE',
    'PBV': 'CAT STD',
    'PEV': 'CAT BRI',
    'PFS': 'CAT GES',
    'PGI': 'CAT BRI',
    'PGX': 'CAT BRI',
    'PMD': 'CAT PUN',
    'PMK': 'CAT STD',
    'PNQ': 'CAT STD',
    'PPD': 'CAT STD',
    'PPQ': 'CAT STD',
    'PPU': 'CAT GES',
    'PQD': 'CAT LIN',
    'PQG': 'CAT SCA',
    'PQO': 'CAT STD',
    'PQP': 'CAT SCA',
    'PQX': 'CAT STD',
    'PQZ': 'CAT STD',
    'PSL': 'CAT GES',
    'PSQ': 'CAT STD',
    'PUF': 'CAT GES',
    'PUN': 'CAT PUN',
    'PVN': 'CAT GES',
    'PVV': 'CAT SCA',
    'PWR': 'CAT SCA',
    'PXS': 'CAT BRI',
    'PXZ': 'CAT GES',
    'RBT': 'CAT BRI',
    'RCI': 'CAT BRI',
    'RCK': 'CAT VVE',
    'RCU': 'CAT VVE',
    'RDH': 'CAT PUN',
    'RGJ': 'CAT BRI',
    'RLO': 'CAT VVE',
    'RMS': 'CAT SFE',
    'RNJ': 'CAT STD',
    'ROB': 'CAT VVE',
    'RPG': 'CAT BRI',
    'RVA': 'CAT BRI',
    'SAS': 'CAT VAE',
    'SBR': 'CAT VVE',
    'SCA': 'CAT SCA',
    'SCZ': 'CAT LAS',
    'SDS': 'CAT STD',
    'SFE': 'CAT SFE',
    'SGE': 'CAT VAE',
    'SGL': 'CAT SCA',
    'SII': 'CAT VAE',
    'SJM': 'CAT GZL',
    'SNP': 'CAT VAE',
    'SPW': 'CAT VAE',
    'SRF': 'CAT SFE',
    'SSF': 'CAT CAD',
    'STD': 'CAT PUN',
    'SVI': 'CAT STD',
    'SWW': 'CAT PUN',
    'TEC': 'CAT BRI',
    'TOO': 'CAT VVE',
    'TPK': 'CAT STD',
    'UBR': 'CAT VVE',
    'UDE': 'CAT CAD',
    'UGN': 'CAT GZL',
    'UHK': 'CAT GZL',
    'UID': 'CAT VVE',
    'UMO': 'CAT VVE',
    'UOL': 'CAT ECE',
    'UPE': 'CAT VVE',
    'UPI': 'CAT LAS',
    'URK': 'CAT ECE',
    'VAF': 'CAT SCA',
    'VAL': 'CAT VAE',
    'VEP': 'CAT GES',
    'VGA': 'CAT SCA',
    'VJU': 'CAT CAD',
    'VLB': 'CAT STD',
    'VLC': 'CAT STD',
    'VMT': 'CAT VVE',
    'VNE': 'CAT VAE',
    'VPP': 'CAT GZL',
    'VSD': 'CAT SFE',
    'VSE': 'CAT STD',
    'VSK': 'CAT CAD',
    'VSQ': 'CAT SFE',
    'VVE': 'CAT VVE',
    'VYD': 'CAT CAD',
    'VYG': 'CAT VAE',
    'XEP': 'CAT CAD',
    'YES': 'CAT CAD',
    'ZNL': 'CAT VVE',
    'ZOZ': 'CAT SFE',
    'EFA': 'CAT ALL',
    'LXE': 'CAT ALL',
    'NA5': 'CAT ALL',
    'NA6': 'CAT ALL',
    'NA7': 'CAT ALL',
    'NA8': 'CAT ALL',
    'NA9': 'CAT ALL',
    'BRQ': 'CAT CAD',
    'CH2': 'CAT CAD',
    'CH4': 'CAT CAD',
    'CYD': 'CAT CAD',
    'DCO': 'CAT CAD',
    'GAG': 'CAT CAD',
    'GPY': 'CAT CAD',
    'GTA': 'CAT CAD',
    'LHE': 'CAT CAD',
    'LRA': 'CAT CAD',
    'NB1': 'CAT CAD',
    'NB3': 'CAT CAD',
    'NB5': 'CAT CAD',
    'NB6': 'CAT CAD',
    'NB7': 'CAT CAD',
    'NB8': 'CAT CAD',
    'NB9': 'CAT CAD',
    'ND6': 'CAT CAD',
    'ND7': 'CAT CAD',
    'RXY': 'CAT CAD',
    'SNJ': 'CAT CAD',
    'YGO': 'CAT CAD',
    'YGP': 'CAT CAD',
    'ROP': 'CAT CON',
    'RTZ': 'CAT CON',
    'RBF': 'CAT ECE',
    'AHF': 'CAT GES',
    'DGN': 'CAT GES',
    'HIS': 'CAT GES',
    'HDN': 'CAT LAS',
    'HZI': 'CAT LAS',
    'YRE': 'CAT LAS',
    'AAM': 'CAT LIN',
    'CH5': 'CAT LIN',
    'CH6': 'CAT LIN',
    'EL9': 'CAT LIN',
    'GBD': 'CAT LIN',
    'GDE': 'CAT LIN',
    'GNZ': 'CAT LIN',
    'ITR': 'CAT LIN',
    'KS4': 'CAT LIN',
    'KS5': 'CAT LIN',
    'KS6': 'CAT LIN',
    'KS7': 'CAT LIN',
    'LAI': 'CAT LIN',
    'MGU': 'CAT LIN',
    'NC7': 'CAT LIN',
    'NC8': 'CAT LIN',
    'ND8': 'CAT LIN',
    'ND9': 'CAT LIN',
    'NE0': 'CAT LIN',
    'NE1': 'CAT LIN',
    'NE2': 'CAT LIN',
    'NRI': 'CAT LIN',
    'OOS': 'CAT LIN',
    'OWP': 'CAT LIN',
    'QA4': 'CAT LIN',
    'QN2': 'CAT LIN',
    'QN3': 'CAT LIN',
    'QN4': 'CAT LIN',
    'QN5': 'CAT LIN',
    'QN6': 'CAT LIN',
    'QN7': 'CAT LIN',
    'QN8': 'CAT LIN',
    'QN9': 'CAT LIN',
    'QO0': 'CAT LIN',
    'QO1': 'CAT LIN',
    'QO2': 'CAT LIN',
    'QO3': 'CAT LIN',
    'QO4': 'CAT LIN',
    'QO5': 'CAT LIN',
    'QO6': 'CAT LIN',
    'QO7': 'CAT LIN',
    'QO8': 'CAT LIN',
    'QO9': 'CAT LIN',
    'QP0': 'CAT LIN',
    'QP1': 'CAT LIN',
    'QP2': 'CAT LIN',
    'QP3': 'CAT LIN',
    'QP4': 'CAT LIN',
    'QP5': 'CAT LIN',
    'QP6': 'CAT LIN',
    'QP7': 'CAT LIN',
    'QP8': 'CAT LIN',
    'QP9': 'CAT LIN',
    'QQ0': 'CAT LIN',
    'QQ1': 'CAT LIN',
    'QQ2': 'CAT LIN',
    'QQ3': 'CAT LIN',
    'QQ4': 'CAT LIN',
    'RFA': 'CAT LIN',
    'RFY': 'CAT LIN',
    'RJW': 'CAT LIN',
    'RNX': 'CAT LIN',
    'S6D': 'CAT LIN',
    'S6F': 'CAT LIN',
    'SM9': 'CAT LIN',
    'SN0': 'CAT LIN',
    'SN2': 'CAT LIN',
    'SN5': 'CAT LIN',
    'SN7': 'CAT LIN',
    'SN8': 'CAT LIN',
    'SN9': 'CAT LIN',
    'SO0': 'CAT LIN',
    'SO1': 'CAT LIN',
    'SO2': 'CAT LIN',
    'SO3': 'CAT LIN',
    'SO4': 'CAT LIN',
    'SO6': 'CAT LIN',
    'SO7': 'CAT LIN',
    'SO9': 'CAT LIN',
    'VF5': 'CAT LIN',
    'VH2': 'CAT LIN',
    'VMI': 'CAT LIN',
    'VX0': 'CAT LIN',
    'VX1': 'CAT LIN',
    'VX2': 'CAT LIN',
    'VX4': 'CAT LIN',
    'VX5': 'CAT LIN',
    'VX6': 'CAT LIN',
    'GTN': 'CAT MOM',
    'MMF': 'CAT MOM',
    'NC1': 'CAT MOM',
    'NC2': 'CAT MOM',
    'NC3': 'CAT MOM',
    'NC4': 'CAT MOM',
    'NC5': 'CAT MOM',
    'NC6': 'CAT MOM',
    'NC9': 'CAT MOM',
    'ND0': 'CAT MOM',
    'ND1': 'CAT MOM',
    'ND2': 'CAT MOM',
    'ND3': 'CAT MOM',
    'ND4': 'CAT MOM',
    'ND5': 'CAT MOM',
    'QB4': 'CAT MOM',
    'RYS': 'CAT MOM',
    'EOX': 'CAT SCA',
    'JCK': 'CAT SCA',
    'RGQ': 'CAT SFE',
    'SOI': 'CAT VVE',
    'ZPJ': 'CAT CAD',
}

COPE_MAP_RAW = {
    'CT MONTEMORELOS': 'CAT MOM',
    'CT APODACA': 'CAT STD',
    'CT GENERAL ESCOBEDO (BRISAS)': 'CAT STD',
    'CT CADEREYTA': 'CAT CAD',
    'CT LINARES': 'CAT LIN',
    'CT GONZALITOS': 'CAT CON',
    'CT LINCOLN': 'CAT VVE',
    'CT REVOLUCION': 'CAT BRI',
    'CT SAN PEDRO': 'CAT VAE',
    'CT COLON': 'CAT CUA',
    'CT SANTA CATARINA': 'CAT SCA',
    'CT PUENTES': 'CAT PUN',
    'CT SANTA FE [MTY]': 'CAT SFE',
    'CT LA SILLA': 'CAT LAS',
    'CT UNIVERSIDAD (NL)': 'CAT GES',
}

def normalizar_texto(valor: Any) -> str:
    """Quita acentos y caracteres no alfanuméricos, y devuelve mayúsculas."""
    if valor is None:
        return ""
    texto = unicodedata.normalize("NFKD", str(valor).replace("\ufeff", ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]", "", texto).upper()


COPE_MAP = {normalizar_texto(k): v for k, v in COPE_MAP_RAW.items()}


def _leer_txt(contenido: bytes) -> tuple[pd.DataFrame, str]:
    """Lee una sábana separada por | sin dejar que comillas anómalas traguen columnas.

    En algunas sábanas existe una comilla suelta en un campo de texto (por ejemplo,
    cerca de AJ). Como | sigue siendo el delimitador real de la sábana, primero
    tratamos las comillas como caracteres ordinarios. Si una fila no coincide con
    el número de columnas del encabezado, probamos interpretar comillas CSV válidas
    solo para esa fila. Nunca omitimos filas silenciosamente.
    """
    errores_decode: list[str] = []
    candidatos: list[tuple[str, str]] = []

    # Probar codificaciones comunes. cp1252 puede fallar con el byte 0x90;
    # por eso hay una segunda variante que reemplaza únicamente bytes inválidos.
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            candidatos.append((contenido.decode(encoding), encoding))
        except UnicodeDecodeError as exc:
            errores_decode.append(f"{encoding}: byte no válido en posición {exc.start}")

    try:
        candidatos.append((contenido.decode("cp1252", errors="replace"),
                           "cp1252 (caracteres inválidos reemplazados)"))
    except Exception as exc:  # pragma: no cover - solo protección adicional
        errores_decode.append(f"cp1252 con reemplazo: {exc}")
    candidatos.append((contenido.decode("latin-1"), "latin-1"))

    errores_parseo: list[str] = []
    for texto, encoding in candidatos:
        # La sábana es registro por línea. Usamos QUOTE_NONE para que una comilla
        # sin escapar dentro de un campo no haga que los | siguientes se ignoren.
        lineas = texto.splitlines()
        idx_encabezado = next((i for i, linea in enumerate(lineas) if linea.strip()), None)
        if idx_encabezado is None:
            errores_parseo.append(f"{encoding}: archivo vacío")
            continue

        try:
            encabezado = next(csv.reader(
                [lineas[idx_encabezado]], delimiter="|", quoting=csv.QUOTE_NONE,
                skipinitialspace=False,
            ))
            encabezado = [c.lstrip("\ufeff") for c in encabezado]
            columnas_esperadas = len(encabezado)
            if columnas_esperadas < 2:
                raise ValueError("el archivo no parece estar delimitado por |")

            filas: list[list[str]] = []
            filas_malas: list[str] = []
            for num_linea, linea in enumerate(lineas[idx_encabezado + 1:], start=idx_encabezado + 2):
                if not linea.strip():
                    continue

                # Primera opción: todas las | son delimitadores, las comillas son texto.
                campos = next(csv.reader(
                    [linea], delimiter="|", quoting=csv.QUOTE_NONE,
                    skipinitialspace=False,
                ))

                if len(campos) != columnas_esperadas:
                    # Respaldo para filas legítimas con un campo entrecomillado que
                    # contenga |. Solo se acepta si coincide exactamente con el header.
                    try:
                        campos_csv = next(csv.reader(
                            [linea], delimiter="|", quotechar='"',
                            quoting=csv.QUOTE_MINIMAL, strict=True,
                        ))
                    except csv.Error:
                        campos_csv = []
                    if len(campos_csv) == columnas_esperadas:
                        campos = campos_csv
                    else:
                        filas_malas.append(
                            f"línea {num_linea}: {len(campos)} columnas (se esperaban {columnas_esperadas})"
                        )
                        continue
                filas.append(campos)

            if filas_malas:
                muestra = "; ".join(filas_malas[:5])
                mas = f"; y {len(filas_malas) - 5} filas adicionales" if len(filas_malas) > 5 else ""
                raise ValueError(f"no coinciden las columnas en {len(filas_malas)} filas: {muestra}{mas}")

            if not filas:
                raise ValueError("no se encontraron filas de datos después del encabezado")

            df = pd.DataFrame(filas, columns=encabezado, dtype=str).fillna("")
            return df, encoding + " (comillas tratadas como texto; delimitación por | y validación de columnas)"

        except (csv.Error, ValueError, IndexError) as exc:
            errores_parseo.append(f"{encoding}: {exc}")

    detalle = " / ".join((errores_decode + errores_parseo)[-5:])
    raise ValueError(
        "No se pudo leer la sábana sin perder columnas. Se intentó tratar las comillas "
        "como texto y validar el número de campos por fila. "
        f"Detalle: {detalle}"
    )


def _buscar_columna(df: pd.DataFrame, objetivo: str) -> str | None:
    """Encuentra encabezados incluso si tienen acentos, espacios o diferencias de mayúsculas."""
    normalizados = [(c, normalizar_texto(c)) for c in df.columns]
    exactos = [c for c, n in normalizados if n == objetivo]
    if exactos:
        return exactos[0]
    parciales = [c for c, n in normalizados if objetivo in n]
    return parciales[0] if parciales else None


def _a_horas(valor: Any) -> float:
    if valor is None:
        return float("nan")
    s = str(valor).strip().replace("\u00a0", "")
    if not s:
        return float("nan")
    s = re.sub(r"\s+", "", s)
    # La columna suele traer horas enteras o decimales con punto/coma.
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "," in s and "." in s:
        # 1.234,5 => decimal con coma; 1,234.5 => separador de miles con coma.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def _asignar_tienda(df: pd.DataFrame) -> pd.Series:
    col_central = _buscar_columna(df, "CENTRAL")
    col_cope = _buscar_columna(df, "CATDESCCOPE")
    central_asignada = pd.Series(index=df.index, dtype="object")
    cope_asignada = pd.Series(index=df.index, dtype="object")
    if col_central is not None:
        central_norm = df[col_central].map(normalizar_texto)
        central_asignada = central_norm.map(CENTRAL_MAP)
    if col_cope is not None:
        cope_norm = df[col_cope].map(normalizar_texto)
        cope_asignada = cope_norm.map(COPE_MAP)
    tienda = central_asignada.where(central_asignada.notna(), cope_asignada)
    return tienda.fillna("SIN ASIGNAR").astype(str)


def construir_resumen(registros_filtrados: pd.DataFrame) -> pd.DataFrame:
    """Construye la tabla compacta tipo tabla dinámica mostrada en la referencia."""
    columnas_finales = ["Etiquetas de fila"]
    if registros_filtrados.empty:
        return pd.DataFrame(columns=columnas_finales)

    vista = registros_filtrados.copy()
    vista["Tienda visible"] = vista["Tienda asignada"].str.replace(r"^CAT\s+", "", regex=True)
    pivot = pd.crosstab(vista["Tienda visible"], vista["Etapa normalizada"])
    etapas_presentes = [e for e in ETAPAS_VALIDAS if e in pivot.columns and int(pivot[e].sum()) > 0]
    if not etapas_presentes:
        return pd.DataFrame(columns=columnas_finales)
    pivot = pivot.reindex(columns=etapas_presentes, fill_value=0).sort_index()
    pivot["Total general"] = pivot.sum(axis=1).astype(int)
    pivot = pivot.reset_index().rename(columns={"Tienda visible": "Etiquetas de fila"})
    columnas = ["Etiquetas de fila"] + etapas_presentes + ["Total general"]
    total = {c: int(pivot[c].sum()) if c != "Etiquetas de fila" else "Total general" for c in columnas}
    pivot = pivot[columnas]
    pivot.loc[len(pivot)] = total
    return pivot


def procesar_archivo(contenido: bytes, region: str) -> dict[str, Any]:
    """Procesa una sábana de una sola región; conserva las reglas originales del PowerShell."""
    if not contenido:
        raise ValueError("El archivo está vacío.")
    df, encoding = _leer_txt(contenido)
    if df.empty:
        raise ValueError("El archivo se leyó, pero no contiene registros de datos.")

    col_etapa = _buscar_columna(df, "ETAPAPISA")
    col_dilacion = _buscar_columna(df, "DILACIONHORASETAPA")
    if col_dilacion is None and len(df.columns) >= 69:
        # Respaldo compatible con la versión PowerShell: columna BQ, índice cero-based 68.
        col_dilacion = df.columns[68]
        dilacion_por_posicion = True
    else:
        dilacion_por_posicion = False
    if col_etapa is None:
        raise ValueError("No se encontró la columna 'Etapa PISA'. Revisa los encabezados de la sábana.")
    if col_dilacion is None:
        raise ValueError("No se encontró 'DilacionHorasEtapa' ni una columna BQ disponible. No se puede calcular la dilación.")

    etapas = df[col_etapa].astype(str).str.strip().str.replace(r"[^A-Za-z0-9]", "", regex=True).str.upper()
    mascara_etapa = etapas.isin(ETAPAS_VALIDAS)
    horas = df[col_dilacion].map(_a_horas)
    mascara_mayor = mascara_etapa & horas.ge(UMBRAL_HORAS)

    tiendas = _asignar_tienda(df)
    validos = df.loc[mascara_etapa].copy()
    validos.insert(0, "Area procesada", region)
    validos.insert(1, "Tienda asignada", tiendas.loc[mascara_etapa].values)
    validos["Etapa normalizada"] = etapas.loc[mascara_etapa].values
    validos["DilacionHorasEtapa numerica"] = horas.loc[mascara_etapa].values

    resumen_datos = pd.DataFrame({
        "Tienda asignada": tiendas.loc[mascara_mayor].values,
        "Etapa normalizada": etapas.loc[mascara_mayor].values,
    })
    resumen = construir_resumen(resumen_datos)

    col_central = _buscar_columna(df, "CENTRAL")
    col_cope = _buscar_columna(df, "CATDESCCOPE")
    no_asignadas = int((tiendas.loc[mascara_etapa] == "SIN ASIGNAR").sum())
    horas_invalidas = int((mascara_etapa & horas.isna()).sum())
    advertencias = []
    if col_central is None:
        advertencias.append("No se detectó la columna Central; se intentará asignar tienda mediante catDescCope.")
    if col_cope is None:
        advertencias.append("No se detectó la columna catDescCope; las filas sin código Central quedarán como SIN ASIGNAR.")
    if no_asignadas:
        advertencias.append(f"{no_asignadas:,} registros de etapas válidas no pudieron asociarse a una tienda.")
    if "caracteres inválidos reemplazados" in encoding:
        advertencias.append(
            "El TXT contiene uno o más bytes no válidos en Windows-1252; se reemplazaron esos caracteres para poder leer el resto del archivo."
        )
    if "comillas tratadas como texto" in encoding:
        advertencias.append(
            "La lectura CSV estándar detectó comillas sin cerrar. Se releyó tratando las comillas como texto para conservar las filas. "
            "Si algún campo de texto contiene el delimitador |, revisa la sábana original."
        )
    if horas_invalidas:
        advertencias.append(f"{horas_invalidas:,} registros de etapas válidas tienen dilación vacía o no numérica y no entran al resumen.")
    if len(df) < 10_000:
        advertencias.append(f"El archivo tiene solo {len(df):,} registros; parece incompleto para una sábana de esta región. Verifica la descarga antes de confiar en la tabla.")

    metrics = {
        "region": region,
        "filas_leidas": int(len(df)),
        "etapas_validas": int(mascara_etapa.sum()),
        "folios_25_mas": int(mascara_mayor.sum()),
        "sin_asignar": no_asignadas,
        "horas_invalidas": horas_invalidas,
        "columna_etapa": str(col_etapa),
        "columna_dilacion": str(col_dilacion),
        "dilacion_por_posicion": dilacion_por_posicion,
        "encoding": encoding,
        "bytes": len(contenido),
        "advertencias": advertencias,
    }
    # Guardar la sábana entera solo en memoria de sesión si se requiere auditoría local; el detalle exportado incluye etapas válidas.
    return {"resumen": resumen, "detalle": validos, "metricas": metrics}
