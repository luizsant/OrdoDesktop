"""Tabelas do Ordo: categorias das caixas, estilos, cores das notas, ativos, notícias e clima.

Compartilhado entre as interfaces (GTK no Linux hoje, Qt no Windows e Linux).
"""

APP_NAME = "Ordo Desktop"
ICON_SIZE = 48
HEADER_H = 34

THEMES = {"padrao": "Padrão (degradê)", "vidro": "Vidro claro", "contorno": "Contorno colorido",
          "compacto": "Preto compacto"}

# (chave, título, cor de destaque, extensões). Ordem = prioridade de exibição.
CATEGORIES = [
    ("atalhos", "Aplicativos", "#7c8cff", {"desktop", "lnk", "url"}),  # .lnk/.url: atalhos do Windows
    ("pastas", "Pastas", "#f5c04a", set()),
    ("pdf", "PDFs", "#ff6b6b", {"pdf", "p7s"}),
    ("docs", "Documentos", "#4aa8ff", {"doc", "docx", "odt", "rtf", "txt", "md", "dotx", "pages", "epub"}),
    ("planilhas", "Planilhas", "#3ecf8e", {"xls", "xlsx", "ods", "csv", "tsv", "numbers"}),
    ("apresentacoes", "Apresentações", "#ff9f43", {"ppt", "pptx", "odp", "key"}),
    ("imagens", "Imagens", "#e06cff", {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "heic", "tif", "tiff", "ico"}),
    ("videos", "Vídeos", "#ff5c8a", {"mp4", "mkv", "avi", "mov", "webm", "wmv", "flv", "m4v"}),
    ("audio", "Áudio", "#2ed1c7", {"mp3", "wav", "ogg", "flac", "m4a", "aac", "opus"}),
    ("compactados", "Compactados", "#c0a080", {"zip", "rar", "7z", "tar", "gz", "xz", "bz2", "zst", "tgz"}),
    ("programas", "Instaladores", "#9aa5b1", {"deb", "appimage", "sh", "run", "rpm", "flatpakref", "exe", "msi"}),
    ("outros", "Outros", "#8892a0", set()),
]
CAT_BY_KEY = {c[0]: c for c in CATEGORIES}

# cor: (fundo, cabeçalho)
NOTE_COLORS = {
    "amarelo": ("#fff1d0", "#ffc98a"),
    "lilas": ("#efe4ff", "#c9a7ff"),
    "azul": ("#e1e9ff", "#a3b8ff"),
    "verde": ("#dcf5e3", "#93dcab"),
    "rosa": ("#ffe1ea", "#ffa3bf"),
    "cinza": ("#eceef2", "#b9bfca"),
}
NOTE_COLOR_NAMES = {"amarelo": "Amarelo", "lilas": "Lilás", "azul": "Azul", "verde": "Verde", "rosa": "Rosa",
                    "cinza": "Cinza"}

# Ativos do card de mercado: (símbolo no Yahoo Finance, nome exibido, tipo de valor)
DEFAULT_ASSETS = [
    ["^BVSP", "Ibovespa", "pts"], ["^GSPC", "S&P 500", "pts"], ["^IXIC", "Nasdaq", "pts"],
    ["BRL=X", "Dólar", "brl"], ["EURBRL=X", "Euro", "brl"], ["BTC-BRL", "Bitcoin", "brl"],
    ["PETR4.SA", "Petrobras", "brl"], ["VALE3.SA", "Vale", "brl"], ["ITUB4.SA", "Itaú", "brl"],
]
# Indicadores do Banco Central (API SGS, oficial): código da série -> nome
BCB_SERIES = [(432, "Selic"), (4389, "CDI"), (13522, "IPCA 12m")]
# Feeds RSS públicos de veículos reconhecidos, por país: chave -> (nome, URL, ligado por padrão)
NEWS_COUNTRIES = {
    "br": ("Brasil", {
        "agenciabrasil": ("Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", True),
        "g1": ("G1", "https://g1.globo.com/rss/g1/", True),
        "folha": ("Folha", "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml", True),
        "bbcbrasil": ("BBC News Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml", True),
        "estadao": ("Estadão (política)", "https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/politica/",
                    False),
        "agenciasenado": ("Agência Senado", "https://www12.senado.leg.br/noticias/feed/todasnoticias/RSS", False),
        "nexo": ("Nexo", "https://www.nexojornal.com.br/rss.xml", False),
        "cnnbrasil": ("CNN Brasil", "https://www.cnnbrasil.com.br/feed/", False),
        "poder360": ("Poder360", "https://www.poder360.com.br/feed/", False),
        "dwbrasil": ("DW Brasil", "https://rss.dw.com/rdf/rss-br-all", False),
        "valor": ("Valor (economia)", "https://valor.globo.com/rss/valor", False),
        "infomoney": ("InfoMoney (economia)", "https://www.infomoney.com.br/feed/", False),
        "exame": ("Exame (economia)", "https://exame.com/feed/", False),
    }),
    "pt": ("Portugal", {
        "publico": ("Público", "https://feeds.feedburner.com/PublicoRSS", True),
        "rtp": ("RTP Notícias", "https://www.rtp.pt/noticias/rss", True),
        "observador": ("Observador", "https://observador.pt/feed/", True),
    }),
    "us": ("Estados Unidos", {
        "npr": ("NPR", "https://feeds.npr.org/1001/rss.xml", True),
        "nyt": ("The New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", True),
        "pbs": ("PBS NewsHour", "https://www.pbs.org/newshour/feeds/rss/headlines", True),
        "cbs": ("CBS News", "https://www.cbsnews.com/latest/rss/main", False),
        "abc": ("ABC News", "https://abcnews.go.com/abcnews/topstories", False),
    }),
    "uk": ("Reino Unido", {
        "bbc": ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", True),
        "guardian": ("The Guardian", "https://www.theguardian.com/uk/rss", True),
        "sky": ("Sky News", "https://feeds.skynews.com/feeds/rss/home.xml", True),
        "independent": ("The Independent", "https://www.independent.co.uk/news/uk/rss", False),
    }),
    "es": ("Espanha", {
        "elpais": ("El País", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", True),
        "elmundo": ("El Mundo", "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", True),
        "lavanguardia": ("La Vanguardia", "https://www.lavanguardia.com/rss/home.xml", True),
        "eldiario": ("elDiario.es", "https://www.eldiario.es/rss/", False),
    }),
    "ar": ("Argentina", {
        "lanacion": ("La Nación", "https://www.lanacion.com.ar/arc/outboundfeeds/rss/?outputType=xml", True),
        "clarin": ("Clarín", "https://www.clarin.com/rss/lo-ultimo/", True),
        "infobae": ("Infobae", "https://www.infobae.com/arc/outboundfeeds/rss/", True),
    }),
    "world": ("Mundo", {
        "bbcworld": ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", True),
        "dw": ("DW", "https://rss.dw.com/rdf/rss-en-all", True),
        "france24": ("France 24", "https://www.france24.com/en/rss", True),
        "aljazeera": ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", True),
        "guardianworld": ("The Guardian (mundo)", "https://www.theguardian.com/world/rss", False),
        "euronews": ("Euronews", "https://www.euronews.com/rss?level=theme&name=news", False),
        "onu": ("ONU News (português)", "https://news.un.org/feed/subscribe/pt/news/all/rss.xml", False),
    }),
}


def default_news_sources(country):
    return [k for k, (_n, _u, on) in NEWS_COUNTRIES[country][1].items() if on]

# Códigos WMO do Open-Meteo -> (descrição, ícone de dia, ícone de noite)
WEATHER_CODES = {
    0: ("Céu limpo", "weather-clear-symbolic", "weather-clear-night-symbolic"),
    1: ("Predomínio de sol", "weather-few-clouds-symbolic", "weather-few-clouds-night-symbolic"),
    2: ("Parcialmente nublado", "weather-few-clouds-symbolic", "weather-few-clouds-night-symbolic"),
    3: ("Nublado", "weather-overcast-symbolic", "weather-overcast-symbolic"),
    45: ("Neblina", "weather-fog-symbolic", "weather-fog-symbolic"),
    48: ("Neblina com geada", "weather-fog-symbolic", "weather-fog-symbolic"),
    51: ("Garoa fraca", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    53: ("Garoa", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    55: ("Garoa forte", "weather-showers-symbolic", "weather-showers-symbolic"),
    61: ("Chuva fraca", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    63: ("Chuva", "weather-showers-symbolic", "weather-showers-symbolic"),
    65: ("Chuva forte", "weather-showers-symbolic", "weather-showers-symbolic"),
    71: ("Neve fraca", "weather-snow-symbolic", "weather-snow-symbolic"),
    73: ("Neve", "weather-snow-symbolic", "weather-snow-symbolic"),
    75: ("Neve forte", "weather-snow-symbolic", "weather-snow-symbolic"),
    80: ("Pancadas de chuva", "weather-showers-scattered-symbolic", "weather-showers-scattered-symbolic"),
    81: ("Pancadas de chuva", "weather-showers-symbolic", "weather-showers-symbolic"),
    82: ("Pancadas fortes", "weather-storm-symbolic", "weather-storm-symbolic"),
    95: ("Trovoadas", "weather-storm-symbolic", "weather-storm-symbolic"),
    96: ("Trovoadas com granizo", "weather-storm-symbolic", "weather-storm-symbolic"),
    99: ("Trovoadas com granizo", "weather-storm-symbolic", "weather-storm-symbolic"),
}


def categorize(name, is_dir):
    if is_dir:
        return "pastas"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    for key, _t, _c, exts in CATEGORIES:
        if ext in exts:
            return key
    return "outros"
