## A) Analyse (Risiken/Quick Wins)
Ziel: [z. B. Durchsatz erhöhen, 429 reduzieren]
Kontext: [Funktionsausschnitt hier einfügen]
Liefere: Liste (max 10 Punkte) in Priorität — je Punkt 1 Satz „Was/Warum/Wie“.

## B) Patch (klein & atomar)
Ziel: [konkret, z. B. dateRestrict korrekt durchreichen]
Kontext: [nur betroffene Funktionen]
Output: **Nur Unified-Diff** (git patch). Keine Erklärtexte.
Constraints: Stil/Typen beibehalten, keine Blocking-Calls im Async-Pfad.

## C) Tests erzeugen
Ziel: pytest für [Funktion]
Kontext: [Funktionsausschnitt]
Output: **Nur** Testdatei (pytest), deterministisch, ohne Netzwerk.

## D) Review/Refactor-Plan
Ziel: Qualitätscheck
Kontext: [Ausschnitt/Datei]
Liefere: Tabelle — Kategorie | Fundstelle | Befund | Empfehlung (knapp).

## E) Mess-Feedback
Hier sind die Run-Zahlen:


Ziel: [z. B. +20 % leads_new, −30 % 429]. Mach mir die nächsten 2 Tickets.
