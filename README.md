# Die Stämme – Skripte

Kleine Helfer für Die Stämme:

| Skript | Wofür | Wo |
|---|---|---|
| **Raubzug-Rechner** | Teilt deine Truppen optimal auf die Raubzug-Stufen auf (Ress pro Lauf, Ress pro Stunde oder gleiche Laufzeit, optional mit max. Laufzeit) | Schnellleiste im Spiel |
| **Späh-Notiz** | Schreibt aus einem Spähbericht eine einzeilige Dorfnotiz: 🟢/🟡/🔴 Ampel, HG-Stufe, Wall, Ress/h, Minen, Spähzeitpunkt | Schnellleiste im Spiel (Premium nötig) |
| **Stamm-Statistik** | Wer im Stamm wie viel gefarmt und beim Raubzug gesammelt hat – als Tabelle und Graph für Discord | Python am PC |

---

## Schnellleiste einrichten (Raubzug-Rechner & Späh-Notiz)

👉 **[datata1.github.io/ds-skripte](https://datata1.github.io/ds-skripte/)** – dort pro Skript auf **Code kopieren** klicken,
dann im Spiel **Einstellungen → Schnellleiste bearbeiten → Link hinzufügen**, Name eintragen und den Code bei
**Ziel-URL** einfügen.

Die Seite wird bei jeder Änderung automatisch aus dem Quelltext in [`src/`](src) gebaut – der Code dort ist also immer aktuell.

**Raubzug-Rechner:** Einheiten an-/abhaken, optional eine Anzahl festlegen (leer = alle), Ziel wählen
(Ress pro Lauf, Ress pro Stunde, gleiche Laufzeit, optional max. Laufzeit). Der Rechner trägt die Truppen für die
nächste Stufe ein und lässt den passenden Start-Knopf grün blinken – **abschicken musst du selbst**.

**Späh-Notiz:** Spähbericht öffnen, klicken. Die Notiz des Zieldorfs wird überschrieben mit z. B.
`🟡 HG 2 · 1.234 Ress/h · Holz 8 Lehm 7 Eisen 6 · Spy 26.11.26 14:03`
(🟢 HG 1 · 🟡 HG 2 · 🔴 HG 3+ oder Wall). Dorfnotizen gibt es nur mit **Premium-Account**.

> **Hinweis zu den Skript-Regeln:** Beide Skripte lesen nur die offene Seite, schicken nichts automatisch
> und machen eine Aktion pro Klick. Sie sind aber (noch) nicht offiziell in der Skript-Bibliothek
> freigegeben – Nutzung auf eigene Verantwortung.

### Selbst ändern

Nur die lesbaren Dateien in `src/` bearbeiten. Lokal bauen und ansehen:

```bash
npm install
npm run build
```

Das erzeugt `_site/index.html` und die fertigen Links `_site/*.txt`. Der Build bricht ab, wenn ein Skript
länger als 10.000 Zeichen wird.

---

## Stamm-Statistik (Python)

Liest nur **öffentliche** Seiten ohne Login (Weltdaten und die Rangliste „An einem Tag“) und baut daraus
eine Übersicht pro Stammesmitglied:

- **Farm-Ress** – geplünderte Rohstoffe
- **Farmen** – Anzahl geplünderter Dörfer
- **Raubzug-Ress** – beim Raubzug gesammelte Rohstoffe

Dazu ein PNG-Graph (eine Farbe pro Spieler) zum Reinkopieren in Discord.

### Installation

Du brauchst [Python 3.9 oder neuer](https://www.python.org/downloads/). Dann einmalig:

```bash
pip install -r requirements.txt
```

(Ohne `matplotlib` läuft das Skript auch, dann nur ohne Graph.)

### Benutzen

```bash
python3 stamm-statistik.py --stamm GBB
```

Unter Windows heißt der Befehl meist `python` statt `python3`.

| Option | Bedeutung |
|---|---|
| `--stamm TAG` | Stammes-Kürzel (Pflicht), z. B. `GBB` oder `-B.O-` |
| `--welt de262` | Welt (Standard: `de262`) |
| `--rekorde` | bester Tag je Spieler mit Datum |
| `--gestern` | nur der gestrige Tag |
| `--tage 7` | Gesamt nur über die letzten 7 Tage |
| `--kein-graph` | kein PNG erzeugen |
| `--webhook URL` | Tabelle und Graph direkt in einen Discord-Kanal posten |

Der Text wird im Terminal ausgegeben (zum Kopieren nach Discord), der Graph landet als
`stamm-statistik-<welt>-<tag>.png` im selben Ordner.

### Wichtig: täglich laufen lassen

Die Rangliste zeigt pro Spieler nur seinen **besten Tag**. Das Skript merkt sich jeden Rekord in
`stamm-statistik-<welt>-<tag>.json`. Wer es **einmal am Tag** startet, sammelt so die Tageswerte
und bekommt echte Summen. Im Early Game stellt fast jeder täglich einen neuen Rekord auf.

Automatisch jeden Morgen (Linux/Mac, `crontab -e`):

```text
0 8 * * * cd /pfad/zum/ordner && python3 stamm-statistik.py --stamm GBB --webhook https://discord.com/api/webhooks/...
```

Unter Windows geht das gleiche mit der **Aufgabenplanung**.

**Discord-Webhook anlegen:** Kanal-Einstellungen → Integrationen → Webhooks → Neuer Webhook → URL kopieren.
Die URL ist wie ein Passwort – nicht öffentlich teilen.
