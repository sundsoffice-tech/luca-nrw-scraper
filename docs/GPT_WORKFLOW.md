# GPT-Workflow (kurz)
**Ziel:** ChatGPT als Co-Dev nutzen, ohne Chaos.

## Regeln
- Immer **ein Ticket** pro Nachricht (klein, messbar).
- **Nur relevanten Codeausschnitt** mitsenden (10–150 Zeilen).
- Output klar fordern:
  - „**Nur Unified-Diff (Patch)**“ für Code.
  - „**Nur pytest-Datei**“ für Tests.
  - „**Nur Liste/Tabelle**“ für Analysen.
- Nach jedem Patch: lokal testen → **Metriken** zurückgeben.

## Kern-Metriken (bei dir)
- `links_checked`, `leads_new`, Ø`score`, `429/403/5xx`, Laufzeit.

## Ablauf je Ticket
1. Ziel & Akzeptanzkriterien notieren.
2. Codeausschnitt anhängen.
3. Passende Prompt-Vorlage (siehe unten) senden.
4. Patch anwenden → `pytest -q` → Zahlen posten.
