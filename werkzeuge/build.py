"""Baut die Webseite aus den Inhalten im Ordner «inhalte».

Aufruf:  python werkzeuge/build.py
Ergebnis: Ordner «_site» mit der fertigen Seite (wird von GitHub automatisch veröffentlicht).
          Die deutsche Seite liegt unter /, die englische unter /en/.
          Englische Texte stehen in index.html als data-en-Attribute direkt neben dem Deutschen,
          in den Inhalten als Felder mit der Endung _en.
"""
import json, re, shutil, sys
from datetime import date, datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
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


def en_feld(e, feld, standard):
    """Englisches Feld (feld_en), sonst automatische Übersetzung des deutschen Werts."""
    if f"{feld}_en" in e:
        return text(e.get(f"{feld}_en"))
    return uebersetze(standard)


# Begriffe für die automatische Übersetzung von Kalender und Resultaten.
# Fehlt ein Begriff, bleibt er deutsch: dann im Eintrag ein Feld mit _en ergänzen.
BEGRIFFE = [
    ("Staffel mit OK Linné", "Relay with OK Linné"),
    ("Schweizer Meisterschaft", "Swiss Championships"),
    ("Jugend-Europameisterschaft", "EYOC"),
    ("Junioren-Europacup", "Junior European Cup"),
    ("Junioren-WM", "JWOC"), ("Studenten-WM", "WUOC"), ("Studenten-EM", "EUOC"),
    ("Militär-WM", "CISM"), ("Heim-Weltcup", "Home World Cup"), ("Heim-EM", "Home EOC"),
    ("Weltcup", "World Cup"), ("EM", "EOC"), ("WM", "WOC"),
    ("Sprintstaffel", "Sprint relay"), ("KO-Sprint", "Knockout sprint"),
    ("Mitteldistanz-Quali", "Middle qualification"), ("Mitteldistanz-Final", "Middle final"),
    ("Mitteldistanz", "Middle distance"), ("Langdistanz", "Long distance"),
    ("Staffel", "Relay"), ("Nacht", "Night"), ("Quali", "Qualification"),
    ("Testläufe", "Selection races"), ("Testlauf", "Selection race"), ("und", "and"),
    ("Schweiz", "Switzerland"), ("Schweden", "Sweden"), ("Finnland", "Finland"),
    ("Norwegen", "Norway"), ("Dänemark", "Denmark"), ("Ungarn", "Hungary"),
    ("Tschechien", "Czech Republic"), ("Slowakei", "Slovakia"), ("Frankreich", "France"),
    ("Spanien", "Spain"), ("Italien", "Italy"), ("Österreich", "Austria"),
    ("Deutschland", "Germany"), ("Litauen", "Lithuania"), ("Belgien", "Belgium"),
]
_BEGRIFF_RE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(d) for d, _ in BEGRIFFE) + r")(?![\w-])")
_BEGRIFF = dict(BEGRIFFE)


def uebersetze(s):
    return _BEGRIFF_RE.sub(lambda m: _BEGRIFF[m.group(1)], s)


MONATE = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def datum_en(von, bis):
    """21 March · 1–2 May · 30 Sep–3 Oct"""
    try:
        a, b = date.fromisoformat(von), date.fromisoformat(bis)
    except ValueError:
        return ""
    if a == b:
        return f"{a.day} {MONATE[a.month - 1]}"
    if a.month == b.month:
        return f"{a.day}–{b.day} {MONATE[a.month - 1]}"
    return f"{a.day} {MONATE[a.month - 1][:3]}–{b.day} {MONATE[b.month - 1][:3]}"


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
        teile = re.split(r"^##\s*English\s*$", m.group(2), maxsplit=1, flags=re.M | re.I)
        absatz = lambda t: [" ".join(a.split()) for a in re.split(r"\n\s*\n", t.strip()) if a.strip()]
        absaetze = absatz(teile[0])
        absaetze_en = absatz(teile[1]) if len(teile) > 1 else []
        news.append({
            "date": text(kopf.get("datum")),
            "title": text(kopf.get("titel")),
            "teaser": text(kopf.get("kurztext")),
            "credit": text(kopf.get("foto")),
            "img": news_bild(text(kopf.get("bild")), text(kopf.get("ausschnitt")), md.name) if kopf.get("bild") else "",
            "text": absaetze,
            "title_en": text(kopf.get("titel_en")),
            "teaser_en": text(kopf.get("kurztext_en")),
            "text_en": absaetze_en,
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
                    "woc": ja(e.get("hoehepunkt")),
                    "name_en": en_feld(e, "name", name), "info_en": en_feld(e, "info", text(e.get("info"))),
                    "d_en": text(e.get("datum_en")) or datum_en(von, bis)})
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
            "intl_en": [[en_feld(e, "anlass", text(e.get("anlass"))), en_feld(e, "disziplin", text(e.get("disziplin"))),
                         rang(e.get("rang"))] for e in (r.get("international") or [])],
            "note_en": text(r.get("hinweis_en")),
            "sm_en": {uebersetze(str(k)): rang(v) for k, v in (r.get("sm") or {}).items()},
        }
    return res


# ---------- Gönner ----------
def schweizer_qr(daten, ziel):
    """Swiss QR Code (QR-Rechnung) als SVG mit Schweizerkreuz in der Mitte."""
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    qr.add_data(daten)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    pfad = "".join(f"M{x} {y}h1v1h-1z" for y, zeile in enumerate(m) for x, v in enumerate(zeile) if v)
    k = n * 7 / 46                      # Kreuz: 7 mm auf 46 mm
    a = (n - k) / 2
    def r(x, y, w, h, f):
        return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{f}"/>'
    s = k / 7 * 1.0                      # 1 mm in Moduleinheiten
    kreuz = (r(a, a, k, k, "#fff") + r(a + .5 * s, a + .5 * s, k - s, k - s, "#000")
             + r(a + 3 * s - .1 * s, a + 1.6 * s, 1.2 * s, 3.8 * s, "#fff")
             + r(a + 1.6 * s, a + 3 * s - .1 * s, 3.8 * s, 1.2 * s, "#fff"))
    ziel.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
                    f'<rect width="{n}" height="{n}" fill="#fff"/><path d="{pfad}" fill="#000"/>{kreuz}</svg>', encoding="utf-8")


def lade_goenner():
    pfad = INH / "goenner.yml"
    if not pfad.exists():
        return None
    g = lade_yaml(pfad) or {}
    if not ja(g.get("anzeigen")):
        return None
    iban = re.sub(r"\s", "", text(g.get("iban"))).upper()
    try:
        import qrbill
        rechnung = qrbill.QRBill(account=iban, language="de",
                                 creditor={"name": text(g.get("name")), "pcode": text(g.get("plz")),
                                           "city": text(g.get("ort")), "country": "CH"},
                                 additional_information=text(g.get("mitteilung")))
    except Exception as e:
        fehler.append(f"goenner.yml: Aus diesen Angaben lässt sich kein QR-Code erstellen ({e}). Bitte IBAN, PLZ und Ort prüfen.")
        return None
    schweizer_qr(rechnung.qr_data(), OUT / "assets" / "goenner-qr.svg")
    return {"iban": " ".join(iban[i:i + 4] for i in range(0, len(iban), 4)),
            "name": text(g.get("name")), "ort": f'{text(g.get("plz"))} {text(g.get("ort"))}',
            "mitteilung": text(g.get("mitteilung")), "namen": [text(x) for x in (g.get("namen") or [])]}


# ---------- Seiten DE und EN ----------
EN_ATTR = ("alt", "aria-label", "content", "title", "href")


def seite(html, sprache):
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.find_all(True):
        for k in list(el.attrs):
            if not k.startswith("data-en"):
                continue
            wert = el.attrs.pop(k)
            if sprache != "en":
                continue
            if k == "data-en":
                el.clear()
                el.append(BeautifulSoup(wert, "html.parser"))
            elif k[8:] in EN_ATTR:
                el[k[8:]] = wert
    if sprache == "en":
        soup.html["lang"] = "en"
    out = str(soup)
    if sprache == "en":
        # Die englische Seite liegt in /en/: Verweise auf Bilder, Schriften usw. absolut setzen
        out = re.sub(r'(["\'(])assets/', r"\1/assets/", out)
    return out


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    roh = (ROOT / "index.html").read_text(encoding="utf-8")
    (OUT / "index.html").write_text(seite(roh, "de"), encoding="utf-8")
    (OUT / "en").mkdir()
    (OUT / "en" / "index.html").write_text(seite(roh, "en"), encoding="utf-8")
    shutil.copytree(ROOT / "assets", OUT / "assets")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    news = lade_news()
    kalender, countdown = lade_kalender()
    resultate = lade_resultate()
    goenner = lade_goenner()
    if fehler:
        print("Die Seite wurde NICHT veröffentlicht. Bitte korrigieren:\n")
        for f in fehler:
            print("  - " + f)
        sys.exit(1)
    schreibe = lambda pfad, d: pfad.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    de = lambda d: {k: v for k, v in d.items() if not k.endswith("_en")}
    schreibe(OUT / "daten.json", {"news": [de(n) for n in news], "kalender": [de(e) for e in kalender],
                                  "countdown": countdown, "resultate": {j: de(r) for j, r in resultate.items()},
                                  "goenner": goenner})
    # Englisch: fehlt eine Übersetzung, erscheint der deutsche Text
    news_en = [{"date": n["date"], "title": n["title_en"] or n["title"], "teaser": n["teaser_en"] or n["teaser"],
                "credit": n["credit"], "img": "/" + n["img"] if n["img"] else "", "text": n["text_en"] or n["text"]}
               for n in news]
    kal_en = [{**de(e), "name": e["name_en"], "info": e["info_en"], "d": e["d_en"] or e["d"]} for e in kalender]
    res_en = {j: {"intl": r["intl_en"], "note": r["note_en"] or r["note"], "junior": r["junior"], "sm": r["sm_en"]}
              for j, r in resultate.items()}
    schreibe(OUT / "en" / "daten.json", {"news": news_en, "kalender": kal_en, "countdown": countdown, "resultate": res_en,
                                          "goenner": goenner})
    ohne = [n["date"] + " " + n["title"] for n in news if not (n["title_en"] and n["text_en"])]
    print(f"Fertig: {len(news)} News, {len(kalender)} Wettkämpfe, {len(resultate)} Resultatjahre, Deutsch und Englisch.")
    if ohne:
        print("Hinweis: Ohne englischen Text (auf der englischen Seite erscheint Deutsch): " + "; ".join(ohne))


if __name__ == "__main__":
    main()
