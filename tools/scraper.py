"""
scraper.py — Descarga HTML y extrae titulares de los medios del corpus.
Responsabilidad única: obtener datos crudos. NO analiza palabras clave.
"""

import argparse
import csv
import logging
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

# ════ PARÁMETROS EDITABLES ════
# Valores por defecto; se sobreescriben con config/parametros.yaml al iniciar
TIMEOUT = 15
DELAY = 2
MAX_TITULARES = 50
LONGITUD_MIN_TITULAR = 15
LONGITUD_MAX_TITULAR = 300
# Selectores CSS evaluados en orden de prioridad; el primero que matchea gana
SELECTORES_TITULARES = [
    "h1", "h2", "h3",
    "[class*='title']", "[class*='titulo']", "[class*='headline']",
    "[class*='noticia']", "[class*='nota']", "[class*='news']",
]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
# ═══════════════════════════════

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_DIR = RAIZ / "config"
DATOS_CRUDOS = RAIZ / "datos" / "crudos"


def cargar_parametros_yaml() -> tuple[int, int, int]:
    ruta = CONFIG_DIR / "parametros.yaml"
    try:
        with open(ruta, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        s = config.get("scraping", {})
        return (
            int(s.get("TIMEOUT", TIMEOUT)),
            int(s.get("DELAY", DELAY)),
            int(s.get("MAX_TITULARES", MAX_TITULARES)),
        )
    except Exception as e:
        logging.warning(f"No se pudo leer {ruta}: {e}. Usando valores por defecto.")
        return TIMEOUT, DELAY, MAX_TITULARES


def configurar_logging(directorio_semana: Path) -> None:
    directorio_semana.mkdir(parents=True, exist_ok=True)
    log_path = directorio_semana / "scraping.log"
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


def semana_iso() -> str:
    hoy = date.today()
    año, semana, _ = hoy.isocalendar()
    return f"{año}-W{semana:02d}"


def slugificar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def cargar_medios_provinciales() -> list[dict]:
    ruta = CONFIG_DIR / "medios_provinciales.csv"
    medios = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f):
            if fila["activo"].strip().lower() in ("true", "1", "sí", "si"):
                medios.append({
                    "corpus": "provincial",
                    "diario": fila["diario"].strip(),
                    "provincia": fila["provincia"].strip(),
                    "region": fila["region"].strip(),
                    "ciudad_origen": fila["ciudad_origen"].strip(),
                    "url": fila["url"].strip(),
                })
    return medios


def cargar_medios_nacionales() -> list[dict]:
    ruta = CONFIG_DIR / "medios_nacionales.csv"
    medios = []
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        for fila in csv.DictReader(f):
            if fila["activo"].strip().lower() in ("true", "1", "sí", "si"):
                medios.append({
                    "corpus": "nacional",
                    "diario": fila["diario"].strip(),
                    "provincia": "Nacional",
                    "region": "Nacional",
                    "ciudad_origen": "Nacional",
                    "url": fila["url"].strip(),
                })
    return medios


def descargar_html(url: str, timeout: int) -> tuple[str | None, str]:
    headers = {"User-Agent": USER_AGENT}
    try:
        respuesta = requests.get(url, headers=headers, timeout=timeout)
        respuesta.raise_for_status()
        respuesta.encoding = respuesta.apparent_encoding
        return respuesta.text, "OK"
    except requests.exceptions.Timeout:
        return None, "TIMEOUT"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"FALLO ({type(e).__name__})"


def extraer_titulares(html: str, max_titulares: int) -> list[str]:
    # DECISIÓN METODOLÓGICA: ver METODOLOGIA.md §4.1 y §4.3
    # Solo home page; selectores priorizados; filtrado por longitud; dedup local
    soup = BeautifulSoup(html, "lxml")
    candidatos: list[str] = []
    vistos: set[str] = set()

    for selector in SELECTORES_TITULARES:
        for elemento in soup.select(selector):
            texto = " ".join(elemento.get_text(separator=" ", strip=True).split())
            if (
                LONGITUD_MIN_TITULAR <= len(texto) <= LONGITUD_MAX_TITULAR
                and texto not in vistos
            ):
                candidatos.append(texto)
                vistos.add(texto)
                if len(candidatos) >= max_titulares:
                    return candidatos

    return candidatos


def procesar_medio(
    medio: dict,
    directorio_semana: Path,
    timeout: int,
    max_titulares: int,
) -> list[dict]:
    corpus = medio["corpus"]
    nombre = medio["diario"]
    url = medio["url"]
    provincia = medio.get("provincia", "")

    # Incluir provincia en el slug para evitar colisiones entre medios homónimos
    # (ej. "EL DIARIO" existe en Córdoba, Entre Ríos y La Pampa)
    if provincia:
        slug = slugificar(f"{nombre}-{provincia}")
    else:
        slug = slugificar(nombre)

    logging.info(f"[{corpus.upper()}] {nombre}{' (' + provincia + ')' if provincia else ''} — {url}")

    html, estado = descargar_html(url, timeout)

    if html is None:
        logging.warning(f"  → {estado} | sin titulares")
        return []

    directorio_corpus = directorio_semana / corpus
    directorio_corpus.mkdir(parents=True, exist_ok=True)
    ruta_html = directorio_corpus / f"{slug}.html"
    ruta_html.write_text(html, encoding="utf-8", errors="replace")

    titulares = extraer_titulares(html, max_titulares)
    logging.info(f"  → {estado} | {len(titulares)} titulares extraídos")

    hoy = date.today().isoformat()
    semana = semana_iso()

    return [
        {
            "fecha": hoy,
            "semana_iso": semana,
            "corpus": corpus,
            "diario": nombre,
            "provincia": provincia,
            "region": medio.get("region", ""),
            "ciudad_origen": medio.get("ciudad_origen", ""),
            "url_medio": url,
            "titular": titular,
        }
        for titular in titulares
    ]


def guardar_titulares(filas: list[dict], directorio_semana: Path) -> None:
    ruta = directorio_semana / "titulares.csv"
    campos = [
        "fecha", "semana_iso", "corpus", "diario", "provincia",
        "region", "ciudad_origen", "url_medio", "titular",
    ]
    with open(ruta, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraper del Monitor de Conflictos — descarga HTML y extrae titulares"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Modo prueba: 3 medios de cada corpus",
    )
    parser.add_argument(
        "--provincia", metavar="PROVINCIA",
        help="Solo scrapear medios de una provincia (ej: 'Tucumán')",
    )
    parser.add_argument(
        "--corpus", choices=["provincial", "nacional"],
        help="Solo scrapear uno de los dos corpus",
    )
    args = parser.parse_args()

    semana = semana_iso()
    directorio_semana = DATOS_CRUDOS / semana
    configurar_logging(directorio_semana)

    timeout, delay, max_titulares = cargar_parametros_yaml()

    medios_prov = cargar_medios_provinciales()
    medios_nac = cargar_medios_nacionales()

    if args.corpus == "provincial":
        medios_nac = []
    elif args.corpus == "nacional":
        medios_prov = []

    if args.provincia:
        prov_norm = slugificar(args.provincia)
        medios_prov = [m for m in medios_prov if slugificar(m["provincia"]) == prov_norm]

    if args.test:
        medios_prov = medios_prov[:3]
        medios_nac = medios_nac[:3]
        logging.info("Modo --test activo: máximo 3 medios por corpus")

    medios = medios_prov + medios_nac

    if not medios:
        logging.error("No hay medios activos para procesar con los filtros indicados.")
        sys.exit(1)

    logging.info(f"Semana: {semana} | Medios a procesar: {len(medios)} "
                 f"({len(medios_prov)} prov. + {len(medios_nac)} nac.)")
    logging.info("=" * 60)

    todos_los_titulares: list[dict] = []
    exitosos = 0
    fallidos = 0

    for i, medio in enumerate(medios):
        if i > 0:
            time.sleep(delay)
        filas = procesar_medio(medio, directorio_semana, timeout, max_titulares)
        if filas:
            todos_los_titulares.extend(filas)
            exitosos += 1
        else:
            fallidos += 1

    if todos_los_titulares:
        guardar_titulares(todos_los_titulares, directorio_semana)

    logging.info("=" * 60)
    logging.info(
        f"Resumen: {len(medios)} medios procesados | "
        f"{exitosos} exitosos | {fallidos} fallidos | "
        f"{len(todos_los_titulares)} titulares totales"
    )
    if todos_los_titulares:
        logging.info(f"Titulares → {directorio_semana / 'titulares.csv'}")
    logging.info(f"HTML crudos → {directorio_semana}/")


if __name__ == "__main__":
    main()
