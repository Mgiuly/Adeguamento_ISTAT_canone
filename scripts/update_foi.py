#!/usr/bin/env python3
"""Aggiorna l'indice FOI (variazione annua, senza tabacchi) dall'API SDMX ufficiale ISTAT.

Scrive data/foi.json e riscrive il blocco FOI_DATA dentro Adeguamento_ISTAT_canone.html.
Esce con errore (e non modifica nulla) se i dati non sono raggiungibili o non passano i controlli.
Solo libreria standard: nessuna dipendenza da installare.
"""
import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "foi.json"
HTML_FILE = ROOT / "Adeguamento_ISTAT_canone.html"

BASE_URL = "https://esploradati.istat.it/SDMXWS/rest/data/"
# FOI mensili: fino al 2025 (basi 1995/2010/2015) e dal 2026 (base 2025)
FLOWS = [
    ("IT1,169_748_DF_DCSP_FOI1B2025_2", "2020-01", "2025-12"),
    ("IT1,169_748_DF_DCSP_FOI1B2025_1", "2026-01", None),
]
ECOICOP = "00ST"   # indice generale FOI al netto dei tabacchi
MEASURE = "7"      # variazione percentuale tendenziale (sullo stesso mese dell'anno precedente)
FIRST_MONTH = "2020-01"


def fetch(flow, start, end):
    url = f"{BASE_URL}{flow}/?startPeriod={start}" + (f"&endPeriod={end}" if end else "")
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.sdmx.data+csv;version=1.0.0",
        "User-Agent": "giuliatobattistin-foi-updater/1.0",
    })
    last_error = None
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(req, timeout=170) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            print(f"Tentativo {attempt} fallito per {flow}: {exc}", file=sys.stderr)
            time.sleep(20 * attempt)
    raise SystemExit(f"Impossibile leggere i dati ISTAT ({flow}): {last_error}")


def parse(text):
    out = {}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("REF_AREA") != "IT" or row.get("ECOICOP_2") != ECOICOP or row.get("MEASURE") != MEASURE:
            continue
        key, value = row["TIME_PERIOD"], row["OBS_VALUE"]
        if not re.fullmatch(r"\d{4}-\d{2}", key) or value == "":
            continue
        number = round(float(value), 1)
        if key in out and out[key] != number:
            raise SystemExit(f"Valori in conflitto per {key}: {out[key]} e {number}")
        out[key] = number
    return out


def month_add(key, n):
    y, m = map(int, key.split("-"))
    idx = y * 12 + (m - 1) + n
    return f"{idx // 12}-{idx % 12 + 1:02d}"


def validate(series):
    if len(series) < 24:
        raise SystemExit(f"Troppi pochi dati ({len(series)} mesi): aggiornamento annullato")
    keys = sorted(series)
    if keys[0] != FIRST_MONTH:
        raise SystemExit(f"Il primo mese è {keys[0]} invece di {FIRST_MONTH}: aggiornamento annullato")
    for a, b in zip(keys, keys[1:]):
        if month_add(a, 1) != b:
            raise SystemExit(f"Mesi non consecutivi tra {a} e {b}: aggiornamento annullato")
    bad = [k for k, v in series.items() if not -5 <= v <= 30]
    if bad:
        raise SystemExit(f"Valori fuori scala per {bad}: aggiornamento annullato")


def main():
    series = {}
    for flow, start, end in FLOWS:
        series.update(parse(fetch(flow, start, end)))
        time.sleep(15)   # l'API ISTAT limita le richieste ravvicinate
    validate(series)
    keys = sorted(series)
    old = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else None
    if old and old.get("last", "") > keys[-1]:
        raise SystemExit(f"I dati ISTAT arrivano a {keys[-1]}, prima di quelli già salvati ({old['last']}): aggiornamento annullato")

    new = {"first": keys[0], "last": keys[-1],
           "next_release": old.get("next_release") if old and old.get("last") == keys[-1] else None,
           "annual": {k: series[k] for k in keys}}
    if old and old.get("annual") == new["annual"] and old.get("first") == new["first"]:
        print("Nessun aggiornamento: dati già allineati a", keys[-1])
        return
    new_with_meta = dict(new, source="ISTAT - indice FOI senza tabacchi, variazione tendenziale (SDMX esploradati.istat.it)",
                         updated=date.today().isoformat())
    DATA_FILE.write_text(json.dumps(new_with_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    block = "const FOI_DATA = " + json.dumps(new, ensure_ascii=False) + ";"
    html = HTML_FILE.read_text(encoding="utf-8")
    pattern = re.compile(r"(/\*FOI_DATA_START\*/\n\s*)const FOI_DATA = .*?;(\n\s*/\*FOI_DATA_END\*/)", re.S)
    if not pattern.search(html):
        raise SystemExit("Blocco FOI_DATA non trovato nella pagina: aggiornamento annullato")
    HTML_FILE.write_text(pattern.sub(lambda m: m.group(1) + block + m.group(2), html, count=1), encoding="utf-8")
    print(f"Aggiornato: {keys[0]} - {keys[-1]} ({len(keys)} mesi). Ultimo dato {keys[-1]}: {series[keys[-1]]}%")


if __name__ == "__main__":
    main()
