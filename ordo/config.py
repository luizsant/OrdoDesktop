"""Configuração do Ordo (mesmo formato de config.json no Linux e no Windows)."""
import json
import os

from . import system
from .catalog import DEFAULT_ASSETS

CONFIG_FILE = os.path.join(system.config_dir(), "config.json")


def load_config():
    cfg = system.load_json(CONFIG_FILE) or {}
    cfg.setdefault("boxes", {})
    cfg.setdefault("clock", {})
    cfg.setdefault("show_seconds", True)
    cfg.setdefault("show_clock", True)
    cfg.setdefault("hide_native", True)
    cfg.setdefault("show_hidden", False)
    cfg.setdefault("show_gadgets", True)
    cfg.setdefault("theme", "padrao")
    cfg.setdefault("language", "auto")
    cfg.setdefault("show_market", True)
    cfg.setdefault("show_news", True)
    cfg.setdefault("market_assets", DEFAULT_ASSETS)
    cfg.setdefault("news_country", "br")
    if not isinstance(cfg.get("news_sources"), dict):
        cfg["news_sources"] = {}
    cfg.setdefault("cards", {})
    cfg.setdefault("autostart", True)
    cfg.setdefault("notes", [])
    cfg.setdefault("weather_city", None)
    cfg.setdefault("native_disabled", [])  # o que o Ordo ocultou, para devolver mesmo após travar
    cfg.setdefault("timer_min", 25)
    cfg.setdefault("overrides", {})  # nome do arquivo -> caixa escolhida pelo usuário
    return cfg


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_FILE)
