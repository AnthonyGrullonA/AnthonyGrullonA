#!/usr/bin/env python3
"""Regenera el arte del perfil a partir de datos reales. Solo stdlib.

1. Lee el calendario público de contribuciones (el mismo HTML que pinta el perfil; sin token).
2. Escribe data/contributions.json, contrib-heatmap.svg e info-card.svg.

Lo ejecuta a diario .github/workflows/update-profile-art.yml.
STATIC=1 emite los SVG ya revelados (para previsualizar sin animación).
"""
import datetime as dt
import html
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "AnthonyGrullonA")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATIC = bool(os.environ.get("STATIC"))

BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, GREEN, ACCENT = "#7d8590", "#c9d1d9", "#3fb950", "#58a6ff"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def fetch_days():
    page = get(f"https://github.com/users/{USER}/contributions")
    tips = dict(re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)', page))
    days = []
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', td))
        if "data-date" not in a:
            continue
        m = re.match(r"\s*(\d[\d,]*)", tips.get(a.get("id"), ""))
        days.append({"date": a["data-date"], "count": int(m.group(1).replace(",", "")) if m else 0,
                     "level": int(a.get("data-level", 0))})
    if not days:
        raise SystemExit("sin celdas en el calendario: GitHub cambió el HTML")
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    """Racha actual (un hoy en cero no la rompe todavía) y la más larga."""
    counts = [d["count"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if counts and counts[i] == 0:
        i -= 1
    current = 0
    while i >= 0 and counts[i]:
        current, i = current + 1, i - 1
    return current, longest


def stats(days):
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    try:
        repos = json.loads(get(f"https://api.github.com/users/{USER}"))["public_repos"]
    except Exception:  # la API sin token tiene límite; el resto del arte no depende de esto
        repos = None
    return {"user": USER, "range": [days[0]["date"], days[-1]["date"]],
            "total": sum(d["count"] for d in days), "current_streak": current,
            "longest_streak": longest, "best_day": best, "public_repos": repos,
            "active_days": sum(1 for d in days if d["count"]), "days": days}


def window(w, h, title):
    """Marco de terminal: fondo, borde, barra de título con los tres puntos."""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="{MONO}">',
           f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
           f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
           f'<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>',
           f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{FRAME}"/>',
           f'<line x1="0" y1="30" x2="{w}" y2="30" stroke="{FRAME}"/>']
    out += [f'<circle cx="{20 + i*16}" cy="15" r="5" fill="{c}"/>'
            for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])]
    out.append(f'<text x="{w/2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">{title}</text>')
    return out


def heatmap(s):
    cell, step, pad, left, top = 12, 15, 20, 34, 56
    first = dt.date.fromisoformat(s["days"][0]["date"])
    sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cols = (dt.date.fromisoformat(s["days"][-1]["date"]) - sunday).days // 7 + 1
    w, grid_h = pad * 2 + left + cols * step, 7 * step
    h = top + grid_h + 96
    out = window(w, h, f"{USER.lower()}@github: ~/contribuciones --grafo")
    out.append('<style>@keyframes c{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}'
               '.c{opacity:0;animation:c .45s cubic-bezier(.2,.8,.2,1) both}</style>' if not STATIC else "")
    prev_month = None
    for d in s["days"]:
        day = dt.date.fromisoformat(d["date"])
        col, row = (day - sunday).days // 7, (day.weekday() + 1) % 7
        x, y = pad + left + col * step, top + row * step
        if row == 0 and day.month != prev_month and col < cols - 2:
            out.append(f'<text x="{x}" y="{top - 8}" fill="{MUTED}" font-size="10">{MESES[day.month-1]}</text>')
            prev_month = day.month
        anim = "" if STATIC else f' class="c" style="animation-delay:{col*0.045 + row*0.03:.3f}s"'
        n = d["count"]
        out.append(f'<rect{anim} x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                   f'fill="{PALETTE[min(d["level"], 4)]}"><title>{d["date"]}: {n} '
                   f'contribución{"" if n == 1 else "es"}</title></rect>')
    for row, name in [(1, "lun"), (3, "mié"), (5, "vie")]:
        out.append(f'<text x="{pad}" y="{top + row*step + 10}" fill="{MUTED}" font-size="9">{name}</text>')
    ly = top + grid_h + 8
    lx = w - pad - len(PALETTE) * step - 34
    out.append(f'<text x="{lx - 6}" y="{ly + 10}" fill="{MUTED}" font-size="10" text-anchor="end">menos</text>')
    out += [f'<rect x="{lx + i*step}" y="{ly}" width="{cell-1}" height="{cell-1}" rx="2" fill="{c}"/>'
            for i, c in enumerate(PALETTE)]
    out.append(f'<text x="{lx + len(PALETTE)*step + 4}" y="{ly + 10}" fill="{MUTED}" font-size="10">más</text>')
    sy = ly + 26
    out.append(f'<line x1="0" y1="{sy}" x2="{w}" y2="{sy}" stroke="{FRAME}" stroke-opacity=".5"/>')
    b, (r0, r1) = s["best_day"], s["range"]
    out.append(f'<text x="{pad}" y="{sy + 26}" font-size="13" fill="{MUTED}"><tspan fill="{GREEN}" '
               f'font-weight="700">{s["total"]:,}</tspan> contribuciones en el último año</text>'.replace(",", " "))
    out.append(f'<text x="{w - pad}" y="{sy + 26}" font-size="12" fill="{MUTED}" text-anchor="end">'
               f'{r0} → {r1}</text>')
    out.append(f'<text x="{pad}" y="{sy + 50}" font-size="13" fill="{MUTED}">racha actual <tspan fill="{ACCENT}" '
               f'font-weight="700">{s["current_streak"]} días</tspan>   ·   más larga <tspan fill="{ACCENT}" '
               f'font-weight="700">{s["longest_streak"]} días</tspan></text>')
    out.append(f'<text x="{w - pad}" y="{sy + 50}" font-size="12" fill="{MUTED}" text-anchor="end">mejor día '
               f'<tspan fill="#e3b341" font-weight="700">{b["count"]}</tspan> el {b["date"]}</text>')
    return "".join(out) + "</svg>"


# Ficha estilo neofetch. Edita estas filas a mano; las de "en vivo" salen de stats().
FICHA = [
    ("Nombre", "Anthony Grullón"),
    ("Rol", "Arquitecto y consultor de software"),
    ("Base", "República Dominicana"),
    ("Ahora", "Construyendo BohioSystem"),
    ("", ""),
    ("Backend", "Python · Django/DRF · FastAPI"),
    ("Datos", "PostgreSQL · MySQL · Redis"),
    ("DevOps", "Docker · Kubernetes · GitHub Actions"),
    ("Nube", "AWS · Azure · GCP"),
    ("Seguridad", "Wazuh · FortiSIEM · WAF · OSINT"),
    ("Infra", "Linux · Terraform · Ansible"),
    ("", ""),
]
LEMA = ["Automatiza lo repetitivo,", "protege lo crítico", "y documenta lo valioso."]


def info_card(s):
    w, h, pad, lh = 840, 880, 34, 31
    out = window(w, h, f"{USER.lower()}@github: ~$ neofetch")
    live = [("Repos", f'{s["public_repos"]} públicos' if s["public_repos"] is not None else "—"),
            ("Aportes", f'{s["total"]:,} en el último año'.replace(",", " ")),
            ("Racha", f'{s["current_streak"]} días · máx. {s["longest_streak"]}'),
            ("Activo", f'{s["active_days"]} de {len(s["days"])} días')]
    head = f"{USER.lower()}@github"
    lines = [(f'<tspan fill="{GREEN}" font-weight="700">{head}</tspan>', len(head)),
             (f'<tspan fill="{MUTED}">{"─" * len(head)}</tspan>', len(head))]
    for k, v in FICHA + live:
        k, v = html.escape(k), html.escape(v)
        lines.append((f'<tspan fill="{ACCENT}" font-weight="700">{k}</tspan><tspan fill="{MUTED}">: </tspan>'
                      f'<tspan fill="{INK}">{v}</tspan>' if k else "", len(k) + 2 + len(v)))
    lines.append(("", 0))
    lines += [(f'<tspan fill="{MUTED}" font-style="italic">{html.escape(t)}</tspan>', len(t)) for t in LEMA]
    y0, fs, t = 74, 19, 0.3
    for i, (body, n) in enumerate(lines):
        y = y0 + i * lh
        if not body:
            continue
        txt = f'<text x="{pad}" y="{y}" font-size="{fs}" xml:space="preserve">{body}</text>'
        if STATIC:
            out.append(txt)
            continue
        dur = max(0.15, n * 0.012)  # cada fila se "teclea" y la siguiente arranca al acabar
        out.append(f'<clipPath id="l{i}"><rect x="{pad}" y="{y - lh + 8}" height="{lh}" width="0">'
                   f'<animate attributeName="width" from="0" to="{w - pad*2}" begin="{t:.2f}s" dur="{dur:.2f}s" '
                   f'fill="freeze"/></rect></clipPath><g clip-path="url(#l{i})">{txt}</g>')
        t += dur + 0.06
    # bloques de color de neofetch y un cursor que parpadea al final
    by = y0 + len(lines) * lh
    out += [f'<rect x="{pad + i*42}" y="{by}" width="38" height="22" rx="3" fill="{c}"/>'
            for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f", ACCENT, "#bc8cff", "#39c5cf", INK])]
    cy = by + 64
    out.append(f'<text x="{pad}" y="{cy}" font-size="{fs}" fill="{GREEN}">➜ <tspan fill="{ACCENT}">~</tspan></text>')
    blink = "" if STATIC else ('<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" '
                               'dur="1s" repeatCount="indefinite"/>')
    out.append(f'<rect x="{pad + 40}" y="{cy - 14}" width="9" height="18" fill="{INK}">{blink}</rect>')
    assert cy + 30 < h, "la ficha no cabe: quita filas o sube h"
    return "".join(out) + "</svg>"


def write(name, text):
    with open(os.path.join(ROOT, name), "w") as f:
        f.write(text)
    print(f"{name}: {len(text):,} bytes")


if __name__ == "__main__":
    s = stats(fetch_days())
    assert streaks([{"count": c} for c in [1, 1, 0, 1, 1, 1, 0]]) == (3, 3)  # hoy en cero no rompe
    assert streaks([{"count": c} for c in [1, 0, 1, 1]]) == (2, 2)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    write("data/contributions.json", json.dumps(s, indent=1))
    write("contrib-heatmap.svg", heatmap(s))
    write("info-card.svg", info_card(s))
