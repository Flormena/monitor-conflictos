"""
analyzer.py — Detecta palabras clave en titulares y genera conflictos.csv.
Lee datos/crudos/{semana}/titulares.csv, escribe acumulativo y snapshot.
Responsabilidad única: detección y registro. NO normaliza por densidad.
"""

import argparse
import csv
import logging
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

# ════ PARÁMETROS EDITABLES ════
RAIZ = Path(__file__).resolve().parent.parent
RUTA_PALABRAS_CLAVE = RAIZ / "config" / "palabras_clave.csv"
RUTA_CONFLICTOS_ACUMULATIVO = RAIZ / "datos" / "procesados" / "conflictos.csv"
RUTA_SNAPSHOTS = RAIZ / "datos" / "snapshots"
RUTA_DATOS_CRUDOS = RAIZ / "datos" / "crudos"
# La ruta del titulares.csv se construye como:
#   RUTA_DATOS_CRUDOS / {semana} / "titulares.csv"
# ═══════════════════════════════

COLUMNAS_SALIDA = [
    "fecha", "semana_iso", "corpus", "diario", "provincia",
    "region", "ciudad_origen", "url_medio", "titular",
    "palabras_encontradas", "cantidad_palabras",
]


def semana_iso() -> str:
    hoy = date.today()
    año, semana, _ = hoy.isocalendar()
    return f"{año}-W{semana:02d}"


def configurar_logging(semana: str) -> None:
    log_path = RUTA_DATOS_CRUDOS / semana / "analyzer.log"
    formato = "%(asctime)s %(levelname)-8s %(message)s"
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format=formato,
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def normalizar_para_matching(texto: str) -> str:
    # DECISIÓN METODOLÓGICA: ver METODOLOGIA.md §3.3
    # 1) Quitar tildes; 2) lowercase; 3) reemplazar no-alfanuméricos con espacio.
    # El titular se guarda siempre en su forma original; esta función solo se usa
    # para la detección. "movilización" matchea "movilizacion" y viceversa.
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return texto


def cargar_palabras_clave() -> list[str]:
    if not RUTA_PALABRAS_CLAVE.exists():
        print(f"Error: no se encontró {RUTA_PALABRAS_CLAVE}")
        sys.exit(1)
    try:
        with open(RUTA_PALABRAS_CLAVE, newline="", encoding="utf-8-sig") as f:
            palabras = [fila["palabra"].strip() for fila in csv.DictReader(f) if fila["palabra"].strip()]
    except KeyError:
        print(f"Error: {RUTA_PALABRAS_CLAVE} no tiene columna 'palabra'")
        sys.exit(1)
    if not palabras:
        print(f"Error: {RUTA_PALABRAS_CLAVE} está vacío")
        sys.exit(1)
    return palabras


def cargar_titulares(semana: str) -> list[dict]:
    ruta = RUTA_DATOS_CRUDOS / semana / "titulares.csv"
    if not ruta.exists():
        print(f"Error: no se encontró {ruta}. ¿Corriste el scraper primero?")
        sys.exit(1)
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def detectar_palabras(titular: str, palabras: list[str]) -> list[str]:
    # DECISIÓN METODOLÓGICA: ver METODOLOGIA.md §3.3 y §5.1
    # Matching por palabra completa (\b...\b) sobre el texto normalizado.
    # "movilización" no matchea "automovilización" ni "desmovilización".
    # DEDUPLICACIÓN y FALSOS POSITIVOS: no implementados (§8.6 y §8.2 pendientes).
    titular_norm = normalizar_para_matching(titular)
    encontradas = []
    for palabra in palabras:
        patron = r"\b" + re.escape(normalizar_para_matching(palabra)) + r"\b"
        if re.search(patron, titular_norm):
            encontradas.append(palabra)
    return encontradas


def analizar(titulares: list[dict], palabras: list[str]) -> list[dict]:
    # DECISIÓN METODOLÓGICA: ver METODOLOGIA.md §5.2 y §8.5
    # 1 fila por titular con ≥1 match; si tiene varias palabras se listan en
    # "palabras_encontradas". La suma por palabra ≠ total de titulares (correcto).
    matches = []
    for fila in titulares:
        encontradas = detectar_palabras(fila["titular"], palabras)
        if encontradas:
            matches.append({
                "fecha": fila["fecha"],
                "semana_iso": fila["semana_iso"],
                "corpus": fila["corpus"],
                "diario": fila["diario"],
                "provincia": fila["provincia"],
                "region": fila["region"],
                "ciudad_origen": fila["ciudad_origen"],
                "url_medio": fila["url_medio"],
                "titular": fila["titular"],
                "palabras_encontradas": ", ".join(encontradas),
                "cantidad_palabras": len(encontradas),
            })
    return matches


def guardar_snapshot(matches: list[dict], semana: str) -> None:
    RUTA_SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    ruta = RUTA_SNAPSHOTS / f"{semana}.csv"
    with open(ruta, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_SALIDA)
        writer.writeheader()
        writer.writerows(matches)
    logging.info(f"Snapshot → {ruta} ({len(matches)} filas)")


def guardar_acumulativo(matches: list[dict], semana: str) -> None:
    # Si la semana ya está en el acumulativo, se eliminan sus filas antes de
    # agregar las nuevas. Permite reprocesar una semana sin duplicar datos.
    filas_previas: list[dict] = []
    if RUTA_CONFLICTOS_ACUMULATIVO.exists():
        with open(RUTA_CONFLICTOS_ACUMULATIVO, newline="", encoding="utf-8-sig") as f:
            filas_previas = [
                fila for fila in csv.DictReader(f)
                if fila.get("semana_iso") != semana
            ]

    RUTA_CONFLICTOS_ACUMULATIVO.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_CONFLICTOS_ACUMULATIVO, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_SALIDA)
        writer.writeheader()
        writer.writerows(filas_previas)
        writer.writerows(matches)

    total = len(filas_previas) + len(matches)
    logging.info(
        f"Acumulativo → {RUTA_CONFLICTOS_ACUMULATIVO} "
        f"({total} filas totales, {len(matches)} de esta semana)"
    )


def loggear_resumen(titulares: list[dict], matches: list[dict]) -> None:
    tasa = len(matches) / len(titulares) * 100 if titulares else 0

    logging.info("=" * 60)
    logging.info(f"Titulares leídos:  {len(titulares)}")
    logging.info(f"Matches totales:   {len(matches)}  ({tasa:.1f}% de detección)")

    logging.info("─" * 40)
    logging.info("Menciones por palabra clave:")
    conteo_palabras: Counter = Counter()
    for m in matches:
        for p in m["palabras_encontradas"].split(", "):
            conteo_palabras[p.strip()] += 1
    for palabra, count in sorted(conteo_palabras.items(), key=lambda x: -x[1]):
        logging.info(f"  {palabra:<15} {count:>4}")

    logging.info("─" * 40)
    logging.info("Menciones por corpus:")
    for corpus, count in Counter(m["corpus"] for m in matches).most_common():
        logging.info(f"  {corpus:<15} {count:>4}")

    logging.info("─" * 40)
    logging.info("Top 5 medios con más menciones:")
    for diario, count in Counter(m["diario"] for m in matches).most_common(5):
        logging.info(f"  {count:>3}  {diario}")

    logging.info("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyzer del Monitor de Conflictos — detecta palabras clave en titulares"
    )
    parser.add_argument(
        "--semana", metavar="YYYY-Www",
        help="Semana a procesar (ej: 2026-W18). Por defecto: semana en curso.",
    )
    args = parser.parse_args()

    semana = args.semana if args.semana else semana_iso()

    # Validar existencia antes de configurar el logger (que escribe en esa carpeta)
    ruta_titulares = RUTA_DATOS_CRUDOS / semana / "titulares.csv"
    if not ruta_titulares.exists():
        print(f"Error: no se encontró {ruta_titulares}. ¿Corriste el scraper primero?")
        sys.exit(1)

    configurar_logging(semana)
    logging.info(f"Analizando semana: {semana}")

    palabras = cargar_palabras_clave()
    logging.info(f"Palabras clave: {', '.join(palabras)}")

    titulares = cargar_titulares(semana)
    logging.info(f"Titulares cargados: {len(titulares)}")

    matches = analizar(titulares, palabras)

    guardar_snapshot(matches, semana)
    guardar_acumulativo(matches, semana)
    loggear_resumen(titulares, matches)


if __name__ == "__main__":
    main()
