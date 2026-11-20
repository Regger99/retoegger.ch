"""Baut die Webseite aus den Inhalten im Ordner «inhalte».

Aufruf:  python werkzeuge/build.py
Ergebnis: Ordner «_site» mit der fertigen Seite (wird von GitHub automatisch veröffentlicht).
"""
import json, re, shutil, sys
from datetime import date, datetime
from pathlib import Path

import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
INH = ROOT / "inhalte"
OUT = ROOT / "_site"
fehler = []


def lade_yaml(pfad):
    try:
        return yaml.safe_load(pfad.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        fehler.append(f"{pfad.relative_to(ROOT)}: Die Datei ist nicht korrekt formatiert ({e}).")
        return None


def text(x):
    if isinstance(x, (date, datetime)):
        return x.isoformat()[:10]
    return "" if x is None else str(x).strip()


def ja(x):
    return x is True or str(x).strip().lower() in ("ja", "yes", "true", "1")


# ---------- News ----------
def news_bild(name, ausschnitt, datei):
    quelle = INH / "bilder" / name
    if not quelle.exists():
        fehler.append(f"{datei}: Das Bild «{name}» fehlt im Ordner inhalte/bilder.")
        return ""
    ziel = OUT / "assets" / "news" / (quelle.stem + ".jpg")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    im = ImageOps.exif_transpose(Image.open(quelle)).convert("RGB")
    w, h = im.size
    if w / h > 4 / 3:
        nw = int(h * 4 / 3)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * 3 / 4)
        anteil = {"oben": 0.0, "mitte": 0.5, "unten": 1.0}.get(ausschnitt, 0.35)
        top = int((h - nh) * anteil)
        im = im.crop((0, top, w, top + nh))
    im.thumbnail((1000, 1000))
    im.save(ziel, quality=82, optimize=True, progressive=True)
    return f"assets/news/{ziel.name}"


def lade_news():
    news = []
    for md in sorted(p for p in (INH / "news").glob("*.md") if not p.name.startswith("_")):
        roh = md.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", roh, re.S)
        if not m:
            fehler.append(f"{md.name}: Der Kopfbereich zwischen den beiden «---» fehlt.")
            continue
        try:
            kopf = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            fehler.append(f"{md.name}: Kopfbereich nicht lesbar ({e}).")
            continue
        for feld in ("titel", "datum", "bild", "kurztext"):
            if not kopf.get(feld):
                fehler.append(f"{md.name}: Das Feld «{feld}» fehlt oder ist leer.")
        absaetze = [" ".join(a.split()) for a in re.split(r"\n\s*\n", m.group(2).strip()) if a.strip()]
        news.append({
            "date": text(kopf.get("datum")),
            "title": text(kopf.get("titel")),
            "teaser": text(kopf.get("kurztext")),
            "credit": text(kopf.get("foto")),
            "img": news_bild(text(kopf.get("bild")), text(kopf.get("ausschnitt")), md.name) if kopf.get("bild") else "",
            "text": absaetze,
        })
    news.sort(key=lambda n: n["date"], reverse=True)
    return news


# ---------- Kalender ----------
def lade_kalender():
    daten = lade_yaml(INH / "kalender.yml") or []
    typen = {"international": "int", "selektion": "sl", "schweiz": "nat"}
    kal, countdown = [], None
    for i, e in enumerate(daten, 1):
        name = text(e.get("name"))
        if e.get("typ") not in typen:
            fehler.append(f"kalender.yml, Eintrag {i} ({name}): typ muss international, selektion oder schweiz sein.")
        von = text(e.get("von"))
        bis = text(e.get("bis")) or von
        kal.append({"name": name, "d": text(e.get("datum")), "from": von, "to": bis,
                    "info": text(e.get("info")), "type": typen.get(e.get("typ"), "nat"),
                    "woc": ja(e.get("hoehepunkt"))})
        if e.get("countdown"):
            c = e["countdown"]
            countdown = c.isoformat() if isinstance(c, datetime) else text(c)
    return kal, countdown


# ---------- Resultate ----------
def rang(x):
    s = text(x)
    return s + "." if s.isdigit() else s


def lade_resultate():
    daten = lade_yaml(INH / "resultate.yml") or {}
    res = {}
    for jahr, r in daten.items():
        r = r or {}
        res[str(jahr)] = {
            "intl": [[text(e.get("anlass")), text(e.get("disziplin")), rang(e.get("rang"))]
                     for e in (r.get("international") or [])],
            "note": text(r.get("hinweis")),
            "junior": ja(r.get("junioren")),
            "sm": {k: rang(v) for k, v in (r.get("sm") or {}).items()},
        }
    return res


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(ROOT / "index.html", OUT / "index.html")
    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    news = lade_news()
    kalender, countdown = lade_kalender()
    resultate = lade_resultate()
    if fehler:
        print("Die Seite wurde NICHT veröffentlicht. Bitte korrigieren:\n")
        for f in fehler:
            print("  - " + f)
        sys.exit(1)
    (OUT / "daten.json").write_text(json.dumps(
        {"news": news, "kalender": kalender, "countdown": countdown, "resultate": resultate},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Fertig: {len(news)} News, {len(kalender)} Wettkämpfe, {len(resultate)} Resultatjahre.")


if __name__ == "__main__":
    main()
