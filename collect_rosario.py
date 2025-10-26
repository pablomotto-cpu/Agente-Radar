#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar Rosario – colector gratuito de titulares.
Versión básica: junta hasta 150 ítems únicos (últimas 24 h, o 36 h los lunes).
Usa RSS nativos y feeds de Google News.
"""

import os, json, hashlib
from datetime import datetime, timedelta, timezone
import feedparser

# Zona horaria Rosario (ART = UTC-3)
ART = timezone(timedelta(hours=-3))

# Ventana temporal: 24 h por defecto, 36 h si es lunes
now = datetime.now(ART)
hours = 36 if now.weekday() == 0 else 24
SINCE = now - timedelta(hours=hours)

# === Lista de feeds (podés sumar más cuando quieras) ===
FEEDS = [
    "https://www.lacapital.com.ar/rss/ultimas-noticias.xml",
    "https://www.rosario3.com/rss/",
    "https://www.elciudadanoweb.com/feed/",
    "https://www.conclusion.com.ar/feed/",
    "https://puntobiz.com.ar/rss",
    "https://www.on24.com.ar/feed/",
    "https://redboing.com/feed/",
    "https://viapais.com.ar/rosario/rss/",
    "https://www.ellitoral.com/rss/ultimas.xml",
    "https://www.unosantafe.com.ar/rss.xml",
    "https://www.airedesantafe.com.ar/rss",
    "https://www.lt9.com.ar/rss",
    "https://www.lt10.com.ar/rss",
    "https://www.sur24.com.ar/feed/",
    "https://venado24.com.ar/feed/",
    "https://casildaplus.com.ar/rss",
    "https://elinformevt.com.ar/feed/",
    "https://www.ambito.com/rss/",
    "https://www.cronista.com/files/rss/economia.xml",
    # Google News RSS (busca “Rosario” o “Santa Fe” en cada dominio)
    "https://news.google.com/rss/search?q=site:infobae.com+Rosario+OR+'Santa+Fe'&hl=es-419&gl=AR&ceid=AR:es-419",
    "https://news.google.com/rss/search?q=site:rosario.gob.ar+Rosario&hl=es-419&gl=AR&ceid=AR:es-419",
    "https://news.google.com/rss/search?q=site:santafe.gov.ar+Rosario+OR+'Santa+Fe'&hl=es-419&gl=AR&ceid=AR:es-419",
]

# === Funciones auxiliares ===
def normalize_title(t):
    return " ".join(t.lower().strip().split())

def hash_topic(title):
    """Agrupa notas del mismo hecho (mismo título base)."""
    key = " ".join(normalize_title(title).split()[:10])
    return hashlib.md5(key.encode("utf-8")).hexdigest()

def parse_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        tm = entry.get(key)
        if tm:
            return datetime(*tm[:6], tzinfo=timezone.utc).astimezone(ART)
    return now  # si no hay fecha

# === Recolección de ítems ===
items = []
for url in FEEDS:
    feed = feedparser.parse(url)
    for e in feed.entries:
        dt = parse_time(e)
        if dt < SINCE:
            continue
        title = e.get("title", "").strip()
        link = e.get("link", "")
        if not title or not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "source": feed.feed.get("title", url),
            "published": dt.isoformat()
        })

# === Agrupación de duplicados ===
groups = {}
for it in items:
    h = hash_topic(it["title"])
    groups.setdefault(h, {"topic": it["title"], "alts": []})
    groups[h]["alts"].append(it)

# === Ordenamiento y recorte a 150 ítems ===
ordered = sorted(groups.values(), key=lambda g: g["alts"][0]["published"], reverse=True)
OUT = []
for g in ordered[:150]:
    alts = sorted(g["alts"], key=lambda x: x["published"], reverse=True)
    head = alts[0]
    others = alts[1:3]
    OUT.append({
        "title": head["title"],
        "primary": {"source": head["source"], "link": head["link"]},
        "others": [{"source": o["source"], "link": o["link"]} for o in others]
    })

# === Guardado ===
os.makedirs("out", exist_ok=True)
payload = {
    "generated_at": now.isoformat(),
    "window_hours": hours,
    "count": len(OUT),
    "items": OUT
}
with open("out/rosario_headlines.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Generado out/rosario_headlines.json con {len(OUT)} ítems.")
