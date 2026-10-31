"""Feriados e contagem de prazos (CPC): sem rede, calculado no próprio computador.

- Conta a partir do primeiro dia útil seguinte ao da intimação (art. 224: exclui o dia do começo).
- Prazos em dias úteis (art. 219) ou corridos (vencimento em dia não útil prorroga para o próximo útil).
- Suspensão de 20/12 a 20/01 (art. 220), opcional.
Os feriados forenses variam por tribunal: a lista é um ponto de partida e o usuário confere no calendário
do seu tribunal.
"""
from datetime import date, timedelta


def easter(year):
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month = (h + m - 7 * n + 114) // 31
    day = (h + m - 7 * n + 114) % 31 + 1
    return date(year, month, day)


# Grupos que o usuário liga/desliga. Valor: função(ano) -> {data: nome}
def _national(y):
    p = easter(y)
    days = {date(y, 1, 1): "Confraternização Universal", p - timedelta(days=2): "Sexta-feira Santa",
            date(y, 4, 21): "Tiradentes", date(y, 5, 1): "Dia do Trabalho", date(y, 9, 7): "Independência",
            date(y, 10, 12): "Nossa Senhora Aparecida", date(y, 11, 2): "Finados",
            date(y, 11, 15): "Proclamação da República", date(y, 12, 25): "Natal"}
    if y >= 2024:
        days[date(y, 11, 20)] = "Consciência Negra"  # Lei 14.759/2023
    return days


def _forense(y):
    p = easter(y)
    return {p - timedelta(days=48): "Carnaval (segunda)", p - timedelta(days=47): "Carnaval (terça)",
            p - timedelta(days=3): "Quinta-feira Santa",
            p + timedelta(days=60): "Corpus Christi", date(y, 12, 8): "Dia da Justiça"}


def _para(y):
    return {date(y, 8, 15): "Adesão do Pará à Independência"}


def _belem(y):
    return {date(y, 1, 12): "Aniversário de Belém"}


HOLIDAY_GROUPS = {
    "nacional": ("Feriados nacionais", _national),
    "forense": ("Feriados forenses (Carnaval, Semana Santa, Corpus Christi, 8/12)", _forense),
    "para": ("Feriados do Pará", _para),
    "belem": ("Feriados de Belém", _belem),
}
# Só os nacionais por padrão: tratar como feriado um dia que é útil no tribunal adiaria o vencimento
# além do real. Os demais grupos o usuário liga conforme o calendário do seu tribunal.
DEFAULT_GROUPS = ["nacional"]


def holidays(year, groups=DEFAULT_GROUPS, extra=()):
    """{data: nome} do ano, juntando os grupos escolhidos e as datas extras ("AAAA-MM-DD" ou "MM-DD")."""
    out = {}
    for g in groups:
        if g in HOLIDAY_GROUPS:
            out.update(HOLIDAY_GROUPS[g][1](year))
    for item in extra:
        parts = str(item).split("=", 1)
        when, name = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "Feriado")
        try:
            d = date.fromisoformat(when) if len(when) == 10 else date.fromisoformat(f"{year}-{when}")
        except ValueError:
            continue
        if d.year == year:
            out[d] = name
    return out


def in_recess(d):
    """Art. 220 do CPC: prazos suspensos de 20 de dezembro a 20 de janeiro, inclusive."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)


class Calendar:
    """Dias úteis segundo os feriados escolhidos (com cache por ano)."""

    def __init__(self, groups=DEFAULT_GROUPS, extra=(), recess=True):
        self.groups, self.extra, self.recess = list(groups), list(extra), recess
        self._cache = {}

    def holiday(self, d):
        if d.year not in self._cache:
            self._cache[d.year] = holidays(d.year, self.groups, self.extra)
        return self._cache[d.year].get(d)

    def is_business(self, d):
        return d.weekday() < 5 and not self.holiday(d) and not (self.recess and in_recess(d))

    def next_business(self, d):
        while not self.is_business(d):
            d += timedelta(days=1)
        return d

    def deadline(self, start, days, business=True):
        """Último dia do prazo contado a partir da intimação/publicação em `start`."""
        if days <= 0:
            return start
        if business:
            d, count = start, 0
            while count < days:
                d += timedelta(days=1)
                if self.is_business(d):
                    count += 1
            return d
        # Corridos: começa no primeiro dia útil seguinte e, se terminar em dia não útil, prorroga.
        first = self.next_business(start + timedelta(days=1))
        return self.next_business(first + timedelta(days=days - 1))

    def skipped(self, start, end):
        """Feriados e suspensões entre start (exclusive) e end (inclusive), para o usuário conferir."""
        out, d = [], start
        while d < end:
            d += timedelta(days=1)
            if self.holiday(d) and d.weekday() < 5:
                out.append((d, self.holiday(d)))
        if self.recess and any(in_recess(start + timedelta(days=i)) for i in range(1, (end - start).days + 1)):
            out.append((None, "Suspensão de 20/12 a 20/01 (art. 220 do CPC)"))
        return out

    def business_days_between(self, a, b):
        """Dias úteis de a (exclusive) até b (inclusive); negativo se b já passou."""
        if b < a:
            return -self.business_days_between(b, a)
        n, d = 0, a
        while d < b:
            d += timedelta(days=1)
            n += self.is_business(d)
        return n
