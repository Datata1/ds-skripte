#!/usr/bin/env python3
"""Farm- und Raubzug-Statistik für einen Stamm in Die Stämme.

Liest nur öffentliche Seiten (ohne Login):
  - Weltdaten /map/ally.txt und /map/player.txt (Stamm-Mitglieder)
  - Rangliste "An einem Tag" (Gastzugang): Geplünderte Rohstoffe,
    Geplünderte Dörfer, Gesammelte Rohstoffe

Die Rangliste zeigt pro Spieler nur seinen besten Tag samt Datum. Das
Programm merkt sich jeden gesehenen Rekord mit Datum in einer JSON-Datei.
Wer es regelmäßig laufen lässt (am besten täglich), bekommt damit pro Tag
die Werte aller Spieler, die an diesem Tag einen Rekord aufgestellt haben.
Im Early Game ist das fast jeder Tag.

Aufruf:
  python3 stamm-statistik.py --stamm TAG
  python3 stamm-statistik.py --stamm TAG --webhook https://discord.com/api/webhooks/...
Optionen: --welt de262, --tage 7 (Gesamt nur über die letzten 7 Tage),
          --gestern (nur gestriger Tag statt Gesamt),
          --rekorde (bester Tag je Spieler mit Datum), --kein-graph
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

TYPEN = [("loot_res", "Farm-Ress"), ("loot_vil", "Farmen"), ("scavenge", "Raubzug-Ress")]
UA = "Mozilla/5.0 (Stamm-Statistik)"
PAUSE = 0.6  # Sekunden zwischen Anfragen an den DS-Server
TZ = ZoneInfo("Europe/Berlin")


def hole(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    time.sleep(PAUSE)
    return text


def mitglieder(basis, tag):
    stamm = None
    for zeile in hole(basis + "/map/ally.txt").splitlines():
        t = zeile.split(",")
        if len(t) > 2 and urllib.parse.unquote_plus(t[2]).lower() == tag.lower():
            stamm = t[0]
            name = urllib.parse.unquote_plus(t[1])
            break
    if not stamm:
        sys.exit(f"Stamm '{tag}' nicht gefunden.")
    spieler = {}
    for zeile in hole(basis + "/map/player.txt").splitlines():
        t = zeile.split(",")
        if len(t) > 2 and t[2] == stamm:
            spieler[t[0]] = urllib.parse.unquote_plus(t[1])
    return name, spieler


ZELLEN = re.compile(r'<td class="lit-item[^"]*">(.*?)</td>', re.S)


def datum(text, heute):
    text = text.strip()
    if text == "Heute":
        return heute
    if text == "Gestern":
        return heute - dt.timedelta(days=1)
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{2,4})", text)
    if not m:
        return None
    j = int(m.group(3))
    return dt.date(j + 2000 if j < 100 else j, int(m.group(2)), int(m.group(1)))


def rekord(basis, typ, pid, name, heute):
    q = urllib.parse.urlencode({"screen": "ranking", "mode": "in_a_day", "type": typ, "name": name})
    for zeile in hole(f"{basis}/guest.php?{q}").split("<tr")[1:]:
        if f"screen=info_player&amp;id={pid}\"" not in zeile:
            continue
        z = [re.sub(r"<[^>]+>|\s", "", c) for c in ZELLEN.findall(zeile)]
        if len(z) >= 5 and z[3].replace(".", "").isdigit():
            d = datum(z[4], heute)
            return (d, int(z[3].replace(".", ""))) if d else None
    return None


def zahl(n):
    return f"{n:,}".replace(",", ".") if n is not None else "–"


def tabelle(titel, zeilen):
    kopf = ["Spieler"] + [t[1] for t in TYPEN]
    daten = [[n] + [w if isinstance(w, str) else zahl(w) for w in werte] for n, werte in zeilen]
    breite = [max(len(r[i]) for r in [kopf] + daten) for i in range(len(kopf))]
    fmt = lambda r: "  ".join(r[0].ljust(breite[0]) if i == 0 else r[i].rjust(breite[i]) for i in range(len(r)))
    kopfzeilen = [fmt(kopf), "-" * len(fmt(kopf))]
    teile = [daten[i:i + 30] for i in range(0, len(daten), 30)] or [[]]
    return [
        (f"**{titel}**\n" if i == 0 else "") + "```\n" + "\n".join(kopfzeilen + [fmt(r) for r in t]) + "\n```"
        for i, t in enumerate(teile)
    ]


def nachrichten(teile, limit=1900):
    out, akt = [], ""
    for t in teile:
        if akt and len(akt) + len(t) + 1 > limit:
            out.append(akt)
            akt = ""
        akt = (akt + "\n" + t) if akt else t
    if akt:
        out.append(akt)
    return out


FARBEN = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"]
GRAU = "#5f5e5a"


def graph(db, spieler, tage, titel, pfad):
    """Aufsummierte Linien je Spieler, drei Felder nebeneinander. Top 8 farbig, Rest grau."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Kein Graph: matplotlib fehlt (pip install matplotlib).", file=sys.stderr)
        return None
    if not tage:
        return None
    x = [dt.date.fromisoformat(d) for d in tage]
    kum = {}
    for p in spieler:
        kum[p] = {}
        for t, _ in TYPEN:
            summe, reihe = 0, []
            for d in tage:
                summe += db["tage"][d].get(p, {}).get(t, 0)
                reihe.append(summe)
            kum[p][t] = reihe
    # Farbig: die Spitze jedes Feldes (zusammen max. 8 Spieler). Die Farbe folgt dem Spieler
    # und ist in allen drei Feldern gleich.
    rang = {t: sorted(spieler, key=lambda p: -kum[p][t][-1]) for t, _ in TYPEN}
    for n in range(5, 0, -1):
        bunt = []
        for t, _ in TYPEN:
            bunt += [p for p in rang[t][:n] if p not in bunt and kum[p][t][-1] > 0]
        if len(bunt) <= 8:
            break
    farbe = {p: FARBEN[i] for i, p in enumerate(bunt)}
    bg, ink, ink2, gitter = "#1a1a19", "#f0efec", "#c3c2b7", "#2e2e2b"
    plt.rcParams.update({"font.size": 11, "text.color": ink, "axes.labelcolor": ink2,
                         "xtick.color": ink2, "ytick.color": ink2})
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4), dpi=110, facecolor=bg)
    for ax, (t, name) in zip(axes, TYPEN):
        ax.set_facecolor(bg)
        for p in spieler:
            if p not in farbe:
                ax.plot(x, kum[p][t], color=GRAU, lw=1, alpha=0.7, zorder=1)
        for p in reversed(bunt):
            ax.plot(x, kum[p][t], color=farbe[p], lw=2, marker="o", ms=5,
                    markeredgecolor=bg, markeredgewidth=1.5, zorder=2)
        # Namen der Top dieses Feldes direkt ans Linienende, ohne Überlappung
        oben = max([kum[p][t][-1] for p in spieler] + [1])
        ax.set_ylim(0, oben * 1.06)
        top = [p for p in rang[t][:n] if p in farbe]
        span = max(1, (x[-1] - x[0]).days)
        pos, abstand = [], oben * 0.075
        for p in sorted(top, key=lambda p: -kum[p][t][-1]):
            y = kum[p][t][-1]
            if pos and pos[-1] - y < abstand:
                y = pos[-1] - abstand
            pos.append(y)
            ax.text(mdates.date2num(x[-1]) + span * 0.03, y, spieler[p], color=ink, fontsize=10, va="center")
        rechts = x[-1] + dt.timedelta(days=max(1, (x[-1] - x[0]).days) * 0.45 or 1)
        links = x[0] - dt.timedelta(days=0.3) if len(x) > 1 else x[0] - dt.timedelta(days=1)
        ax.set_xlim(links, rechts)
        ax.set_title(name, loc="left", fontsize=13, color=ink, pad=8)
        ax.grid(axis="y", color=gitter, lw=1)
        ax.set_axisbelow(True)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(x) // 6)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
    griffe = [plt.Line2D([], [], color=farbe[p], lw=2, marker="o", ms=5) for p in bunt]
    namen = [spieler[p] for p in bunt]
    if len(spieler) > len(bunt):
        griffe.append(plt.Line2D([], [], color=GRAU, lw=1))
        namen.append(f"Weitere ({len(spieler) - len(bunt)})")
    fig.legend(griffe, namen, loc="upper left", ncol=min(len(namen), 9), frameon=False,
               bbox_to_anchor=(0.005, 0.925), fontsize=10.5, handlelength=1.6, columnspacing=1.4)
    fig.suptitle(titel, x=0.012, y=0.985, ha="left", fontsize=15, fontweight="bold", color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.87), w_pad=3)
    fig.savefig(pfad, facecolor=bg)
    plt.close(fig)
    return pfad


def sende(webhook, inhalt, bild=None):
    if not bild:
        daten, typ = json.dumps({"content": inhalt}).encode(), "application/json"
    else:
        grenze = "----stammstatistik" + str(int(time.time()))
        teile = [
            f'--{grenze}\r\nContent-Disposition: form-data; name="payload_json"\r\n'
            f"Content-Type: application/json\r\n\r\n{json.dumps({'content': inhalt})}\r\n".encode(),
            f'--{grenze}\r\nContent-Disposition: form-data; name="files[0]"; filename="{bild.name}"\r\n'
            "Content-Type: image/png\r\n\r\n".encode() + bild.read_bytes() + b"\r\n",
            f"--{grenze}--\r\n".encode(),
        ]
        daten, typ = b"".join(teile), f"multipart/form-data; boundary={grenze}"
    req = urllib.request.Request(webhook, data=daten, headers={"Content-Type": typ, "User-Agent": UA})
    urllib.request.urlopen(req, timeout=30).close()


def main():
    ap = argparse.ArgumentParser(description="Farm- und Raubzug-Statistik eines Stamms")
    ap.add_argument("--stamm", required=True, help="Stammes-Tag, z.B. ABC")
    ap.add_argument("--welt", default="de262")
    ap.add_argument("--tage", type=int, default=0, help="Gesamt nur über die letzten N Tage (0 = alles)")
    ap.add_argument("--gestern", action="store_true", help="nur den gestrigen Tag statt Gesamt zeigen")
    ap.add_argument("--rekorde", action="store_true", help="aktuelle Tagesrekorde mit Datum zeigen")
    ap.add_argument("--kein-graph", action="store_true", help="kein PNG erzeugen/mitschicken")
    ap.add_argument("--webhook", help="Discord-Webhook-URL; ohne wird nur ausgegeben")
    argv = sys.argv[1:]
    for i, x in enumerate(argv[:-1]):  # Stammes-Tags wie "-B.O-" beginnen mit "-"
        if x == "--stamm":
            argv[i:i + 2] = ["--stamm=" + argv[i + 1]]
            break
    a = ap.parse_args(argv)

    basis = f"https://{a.welt}.die-staemme.de"
    datei = Path(__file__).with_name(f"stamm-statistik-{a.welt}-{a.stamm.lower()}.json")
    db = json.loads(datei.read_text()) if datei.exists() else {"tage": {}, "namen": {}}
    heute = dt.datetime.now(TZ).date()

    stammname, spieler = mitglieder(basis, a.stamm)
    print(f"{stammname}: {len(spieler)} Mitglieder, lese Rangliste ...", file=sys.stderr)
    rek = {}
    for pid, name in spieler.items():
        db["namen"][pid] = name
        rek[pid] = {}
        for typ, _ in TYPEN:
            r = rekord(basis, typ, pid, name, heute)
            if r:
                rek[pid][typ] = r
                tag = db["tage"].setdefault(r[0].isoformat(), {}).setdefault(pid, {})
                tag[typ] = max(tag.get(typ, 0), r[1])
    datei.write_text(json.dumps(db, ensure_ascii=False, indent=1))

    gestern = (heute - dt.timedelta(days=1)).isoformat()
    ab = (heute - dt.timedelta(days=a.tage)).isoformat() if a.tage else ""
    tage = sorted(d for d in db["tage"] if ab <= d < heute.isoformat())

    def werte(tagliste, pid):
        return [
            sum(db["tage"][d].get(pid, {}).get(t, 0) for d in tagliste) or None
            for t, _ in TYPEN
        ]

    sortiert = lambda z: sorted(z, key=lambda x: [-(w or 0) for w in x[1]])
    z_gestern = sortiert([(spieler[p], werte([gestern] if gestern in db["tage"] else [], p)) for p in spieler])
    z_gesamt = sortiert([(spieler[p], werte(tage, p)) for p in spieler])
    z_rekorde = [
        (spieler[p], [f"{zahl(rek[p][t][1])} ({rek[p][t][0].strftime('%d.%m.')})" if t in rek[p] else "–" for t, _ in TYPEN])
        for p in sorted(spieler, key=lambda p: [-(rek[p][t][1] if t in rek[p] else 0) for t, _ in TYPEN])
    ]
    seit = dt.date.fromisoformat(tage[0]).strftime("%d.%m.") if tage else heute.strftime("%d.%m.")
    d_gestern = (heute - dt.timedelta(days=1)).strftime("%d.%m.%Y")

    teile = [
        f"## {stammname} – Farmen & Raubzug",
        *(tabelle("Bester Tag (Datum)", z_rekorde) if a.rekorde else tabelle(f"Gestern ({d_gestern})", z_gestern) if a.gestern else tabelle(f"Gesamt seit {seit}", z_gesamt)),
        "-# Farm-Ress = geplünderte Rohstoffe, Farmen = Anzahl geplünderter Dörfer, Raubzug-Ress = beim Raubzug gesammelte Rohstoffe."
        + ("" if a.rekorde else " Gezählt werden Tage mit persönlichem Tagesrekord."),
    ]
    msgs = nachrichten(teile)
    print("\n\n".join(msgs))

    bild = None
    if not a.kein_graph:
        bild = graph(db, spieler, tage, f"{stammname} – aufsummiert seit {seit}", datei.with_suffix(".png"))
        if bild:
            print(f"Graph gespeichert: {bild}", file=sys.stderr)

    if a.webhook:
        for i, m in enumerate(msgs):
            sende(a.webhook, m, bild if i == len(msgs) - 1 else None)
            time.sleep(1)
        print("An Discord gesendet.", file=sys.stderr)


if __name__ == "__main__":
    main()
