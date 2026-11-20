# Anleitung: Webseite selbst pflegen

Alles, was du regelmässig änderst, liegt im Ordner **inhalte**. Sobald du eine Änderung in GitHub speicherst («Commit changes»), baut GitHub die Seite neu und veröffentlicht sie. Das dauert rund 1–2 Minuten.

## Neuen News-Beitrag erstellen

1. **Bild hochladen:** Öffne den Ordner `inhalte/bilder`, klicke auf **Add file → Upload files** und ziehe das Foto hinein. Das Originalfoto reicht, die Seite schneidet es automatisch ins richtige Format und verkleinert es. Verwende einen einfachen Dateinamen ohne Leerzeichen, zum Beispiel `weltcup-schweden.jpg`.
2. **Text anlegen:** Öffne den Ordner `inhalte/news`, öffne die Datei `_vorlage.md` und kopiere ihren Inhalt. Gehe zurück in den Ordner, klicke auf **Add file → Create new file** und nenne die Datei nach dem Muster `2027-06-06-weltcup-schweden.md` (Datum, dann ein kurzer Name).
3. **Ausfüllen:** Füge den kopierten Inhalt ein und ersetze die Platzhalter:
   - `titel`: die Überschrift
   - `datum`: Datum im Format JJJJ-MM-TT, zum Beispiel `2027-06-06`
   - `bild`: der Dateiname aus Schritt 1, zum Beispiel `weltcup-schweden.jpg`
   - `foto`: wer das Bild gemacht hat (erscheint unter dem Artikel und im Bildnachweis)
   - `kurztext`: ein bis zwei Sätze für die Kachel
   - `ausschnitt` (optional): `oben`, `mitte` oder `unten`, falls beim Zuschneiden der Kopf abgeschnitten wird
   - Unterhalb der zweiten `---`-Linie folgt der Artikel. Zwischen Absätzen eine leere Zeile.
4. **Speichern:** Klicke auf **Commit changes**. Fertig.

Text und Werte mit einem Doppelpunkt darin bitte immer in Anführungszeichen setzen, wie in der Vorlage.

## Wettkampfkalender ändern

Datei `inhalte/kalender.yml` öffnen, auf den Stift (Bearbeiten) klicken und einen Eintrag kopieren und anpassen. Die Reihenfolge in der Datei ist die Reihenfolge auf der Seite. Welcher Wettkampf «als Nächstes» markiert ist, berechnet die Seite selbst.

## Resultate nachtragen

Datei `inhalte/resultate.yml` bearbeiten. Ein neues Jahr fügst du oben ein, indem du einen bestehenden Jahresblock kopierst. Beim Rang nur die Zahl eintragen (also `3`, nicht `3.`).

## Wenn etwas nicht klappt

Hat sich ein Fehler eingeschlichen (zum Beispiel ein falscher Bildname), wird die Seite **nicht** verändert, die bisherige Version bleibt online. Unter dem Reiter **Actions** siehst du einen roten Eintrag. Ein Klick darauf zeigt im Schritt «Seite bauen» genau, welche Datei und welches Feld zu korrigieren ist.
