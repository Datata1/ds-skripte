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


def graph(db, spieler, tage, titel, pfad, no_new_rekord_est_factor=0.5):
    """Ein großer Graph: Tageswert je Spieler = Farm-Ress + Raubzug-Ress (nicht aufsummiert).
    Je Typ: an Rekordtagen der exakte Rekord, sonst faktor * zuletzt bekannter Rekord (Schätzung).
    Start = erstes Datum in den Daten (tage[0]). Top 8 (nach Summe über den Zeitraum) farbig, Rest grau."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.ticker as mticker
    except ImportError:
        print("Kein Graph: matplotlib fehlt (pip install matplotlib).", file=sys.stderr)
        return None
    if not tage:
        return None

    erster = dt.date.fromisoformat(tage[0])
    letzter = dt.date.fromisoformat(tage[-1])
    # Jeder Kalendertag vom ersten Datum in den Daten bis zum letzten. Kein Nullpunkt davor.
    x_alle = [erster + dt.timedelta(days=i) for i in range((letzter - erster).days + 1)]

    # Pro Spieler: (Datum, Wert) für jeden Tag.
    # Rekordtag: exakter Wert. Kein Rekord: Faktor * zuletzt bekannter Rekord.
    # Gibt es noch keinen bekannten Rekord (Datenpunkt fehlt), zählt der Typ 0.
    reihen, gesamt = {}, {}
    for p in spieler:
        punkte = []
        letzt = {"loot_res": 0, "scavenge": 0}  # zuletzt bekannter Rekord je Typ
        for xd in x_alle:
            summe = 0
            eintrag = db["tage"].get(xd.isoformat(), {}).get(p, {})
            for t in letzt:
                if t in eintrag:
                    summe += eintrag[t]
                    letzt[t] = max(letzt[t], eintrag[t])
                else:
                    summe += no_new_rekord_est_factor * letzt[t]
            punkte.append((xd, summe))
        reihen[p] = punkte
        gesamt[p] = sum(w for _, w in punkte)  # Ranking der Farben

    rang = sorted((p for p in spieler if gesamt[p] > 0), key=lambda p: -gesamt[p])
    bunt = rang[:8]
    farbe = {p: FARBEN[i] for i, p in enumerate(bunt)}

    bg, ink, ink2, gitter = "#1a1a19", "#f0efec", "#c3c2b7", "#2e2e2b"
    plt.rcParams.update({"font.size": 12, "text.color": ink, "axes.labelcolor": ink2,
                         "xtick.color": ink2, "ytick.color": ink2})
    fig, ax = plt.subplots(figsize=(16, 9), dpi=110, facecolor=bg)
    ax.set_facecolor(bg)

    # Graue Spieler zuerst (hinten), dann die farbigen von hinten nach vorn
    for p in rang[8:]:
        xs, ys = zip(*reihen[p])
        ax.plot(xs, ys, color=GRAU, lw=1, alpha=0.6, marker="o", ms=3, zorder=1)
    for p in reversed(bunt):
        xs, ys = zip(*reihen[p])
        ax.plot(xs, ys, color=farbe[p], lw=2.2, marker="o", ms=6,
                markeredgecolor=bg, markeredgewidth=1.5, zorder=2)

    oben = max([w for p in spieler for _, w in reihen[p]] + [1])
    ax.set_ylim(0, oben * 1.08)

    # Namen der Top-Spieler direkt ans Linienende, in Linienfarbe und fett, ohne Überlappung
    span = max(1, (x_alle[-1] - x_alle[0]).days)
    pos, abstand = [], oben * 0.04
    for p in sorted(bunt, key=lambda p: -reihen[p][-1][1]):
        y = reihen[p][-1][1]
        if pos and pos[-1] - y < abstand:
            y = pos[-1] - abstand
        pos.append(y)
        ax.text(mdates.date2num(x_alle[-1]) + span * 0.015, y, spieler[p],
                color=farbe[p], fontsize=11, fontweight="bold", va="center")
    rechts = x_alle[-1] + dt.timedelta(days=span * 0.2)
    ax.set_xlim(x_alle[0] - dt.timedelta(days=0.3), rechts)

    ax.grid(axis="y", color=gitter, lw=1)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(x_alle) // 12)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
    ax.set_ylabel(f"Farm-Ress + Raubzug-Ress pro Tag (Rekordtag exakt, sonst {no_new_rekord_est_factor:g} × letzter Rekord)")

    griffe = [plt.Line2D([], [], color=farbe[p], lw=2.2, marker="o", ms=6) for p in bunt]
    namen = [spieler[p] for p in bunt]
    if len(rang) > len(bunt):
        griffe.append(plt.Line2D([], [], color=GRAU, lw=1))
        namen.append(f"Weitere ({len(rang) - len(bunt)})")
    fig.legend(griffe, namen, loc="upper left", ncol=min(len(namen), 9), frameon=False,
               bbox_to_anchor=(0.005, 0.925), fontsize=11.5, handlelength=1.6, columnspacing=1.4)
    fig.suptitle(titel, x=0.012, y=0.985, ha="left", fontsize=16, fontweight="bold", color=ink)
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=3)
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
        bild = graph(db, spieler, tage, f"{stammname} – seit {seit}", datei.with_suffix(".png"))
        if bild:
            print(f"Graph gespeichert: {bild}", file=sys.stderr)

    if a.webhook:
        for i, m in enumerate(msgs):
            sende(a.webhook, m, bild if i == len(msgs) - 1 else None)
            time.sleep(1)
        print("An Discord gesendet.", file=sys.stderr)


if __name__ == "__main__":
    main()
