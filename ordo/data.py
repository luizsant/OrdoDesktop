"""Dados da internet usados pelos cards: clima, cotações, indicadores e notícias.

Só biblioteca padrão; as funções bloqueiam e devem rodar fora da thread da interface.
"""
import gzip
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from .catalog import BCB_SERIES, NEWS_COUNTRIES
from .i18n import _


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux) ordo-desktop",
                                               "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data


def http_json(url):
    return json.loads(http_get(url))


def ago(dt):
    mins = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if mins < 1:
        return _("agora")
    if mins < 60:
        return _("há {n} min", n=mins)
    if mins < 24 * 60:
        return _("há {n} h", n=mins // 60)
    return dt.astimezone().strftime("%d/%m %H:%M")


# ---------------------------------------------------------------------------
# Clima (Open-Meteo, gratuito e sem chave)
# ---------------------------------------------------------------------------
def fetch_weather(city):
    return http_json("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": city["lat"], "longitude": city["lon"], "timezone": "auto", "forecast_days": 5,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,is_day,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
    }))


def search_city(query, lang):
    res = http_json("https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {"name": query, "count": 10, "language": lang})).get("results", [])
    return [{"name": r["name"], "admin1": r.get("admin1", ""), "lat": r["latitude"], "lon": r["longitude"],
             "label": ", ".join(x for x in (r["name"], r.get("admin1"), r.get("country")) if x)} for r in res]


# ---------------------------------------------------------------------------
# Mercado (Yahoo Finance + AwesomeAPI para cripto em reais + Banco Central)
# ---------------------------------------------------------------------------
def fetch_quote(sym):
    """(preço, fechamento anterior, pontos do gráfico do dia)."""
    if sym.endswith("-BRL"):
        # O Yahoo não cota cripto em reais; a AwesomeAPI (pública, brasileira) cota.
        hist = http_json(f"https://economia.awesomeapi.com.br/json/daily/{urllib.parse.quote(sym)}/24")
        last = float(hist[0]["bid"])
        prev = last / (1 + float(hist[0]["pctChange"]) / 100)
        return last, prev, [float(h["bid"]) for h in reversed(hist)]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=1d&interval=15m"
    r = http_json(url)["chart"]["result"][0]
    m = r["meta"]
    return m.get("regularMarketPrice"), m.get("chartPreviousClose"), r["indicators"]["quote"][0].get("close") or []


def fetch_market(assets):
    quotes = []
    for sym, name, kind in assets:
        try:
            quotes.append((name, sym, kind, *fetch_quote(sym)))
        except Exception:  # um ativo fora do ar não derruba o card
            quotes.append((name, sym, kind, None, None, []))
    inds = []
    for code, name in BCB_SERIES:
        try:
            v = http_json(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json")
            inds.append((name, float(v[0]["valor"])))
        except Exception:
            inds.append((name, None))
    return quotes, inds


def asset_kind(sym):
    if sym.startswith("^"):
        return "pts"
    return "brl" if sym.endswith((".SA", "BRL=X", "-BRL")) else "num"


def normalize_symbol(sym):
    sym = sym.strip().upper()
    return sym + ".SA" if re.fullmatch(r"[A-Z]{4}\d{1,2}F?", sym) else sym  # ação da B3 sem o .SA


# ---------------------------------------------------------------------------
# Notícias (RSS/RDF/Atom públicos)
# ---------------------------------------------------------------------------
MAX_NEWS = 12
PER_SOURCE = 3  # para uma fonte muito ativa não ocupar o card inteiro
MAX_AGE = timedelta(hours=72)  # feed parado não deve mostrar notícia velha como nova
NOT_NEWS = re.compile(r"^(assista|siga|veja|v[íi]deo|ao vivo|ouça|podcast|watch|live:)\b", re.I)


def parse_date(text):
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # "-0000" vem sem fuso, mas é UTC
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.astimezone()


def parse_entry(el):
    """(data, título, link) de um <item> RSS/RDF ou <entry> Atom; None para outros elementos."""
    if el.tag.rsplit("}", 1)[-1] not in ("item", "entry"):
        return None
    fields = {}
    for child in el:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "link" and not (child.text or "").strip():
            if child.get("rel", "alternate") == "alternate":
                fields.setdefault("link", child.get("href", ""))
        elif tag in ("title", "link", "pubDate", "date", "published", "updated"):
            fields.setdefault(tag, (child.text or "").strip())
    title, link = fields.get("title", ""), fields.get("link", "").strip()
    if not title or not link.startswith("http"):
        return None
    when = next((fields[k] for k in ("pubDate", "date", "published", "updated") if fields.get(k)), None)
    return parse_date(when), title, link


def fetch_news(country, keys):
    feeds = NEWS_COUNTRIES[country][1]
    oldest = datetime.now(timezone.utc) - MAX_AGE
    floor = datetime.min.replace(tzinfo=timezone.utc)
    items = []
    for key in keys:
        name, url, _on = feeds[key]
        try:
            root = ET.fromstring(http_get(url))
        except Exception:
            continue
        feed = [(e[0], name, e[1], e[2]) for e in map(parse_entry, root.iter())
                if e and (e[0] is None or e[0] >= oldest) and not NOT_NEWS.match(e[1])]
        feed.sort(key=lambda x: x[0] or floor, reverse=True)
        items += feed[:PER_SOURCE]
    items.sort(key=lambda x: x[0] or floor, reverse=True)
    return items[:MAX_NEWS]
