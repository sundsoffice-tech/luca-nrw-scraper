# Visual Guide: Candidates Mode UI Changes

## 1. Control Panel - Industry Selector

### BEFORE:
```
Industry: [Recruiter ▼]
          [Candidates ▼]
          [All ▼]
```

### AFTER:
```
Industry: [Recruiter (Firmen finden) ▼]
          [Candidates (Jobsuchende finden) ▼]
          [All Industries ▼]
          [NRW Regional ▼]
          [Social Media ▼]
          ... and more
```

**What changed:** Clear descriptions added to help users understand what each mode does.

---

## 2. Leads Table - New Columns

### BEFORE:
```
┌────┬──────────┬───────────┬────────────┬──────────┬─────────┬────────┬────────┐
│ ID │ Name     │ Firma     │ Mobil      │ E-Mail   │ Quelle  │ Datum  │ Status │
├────┼──────────┼───────────┼────────────┼──────────┼─────────┼────────┼────────┤
│ 1  │ Max M.   │ Acme GmbH │ 0151...    │ max@...  │ xing... │ 18.12  │ Neu    │
└────┴──────────┴───────────┴────────────┴──────────┴─────────┴────────┴────────┘
```

### AFTER:
```
┌────┬────────────┬──────────┬────────────────┬────────────┬──────────┬──────────────┬─────────┬────────┬────────┐
│ ID │ Typ        │ Name     │ Firma/Standort │ Mobil      │ E-Mail   │ Erfahrung/   │ Quelle  │ Datum  │ Status │
│    │            │          │                │            │          │ Rolle        │         │        │        │
├────┼────────────┼──────────┼────────────────┼────────────┼──────────┼──────────────┼─────────┼────────┼────────┤
│ 1  │ 🏢 Firma   │ Max M.   │ Acme GmbH      │ 0151...    │ max@...  │ Sales Mgr    │ xing... │ 18.12  │ Neu    │
├────┼────────────┼──────────┼────────────────┼────────────┼──────────┼──────────────┼─────────┼────────┼────────┤
│ 2  │ 👤 Kandidat│ Anna S.  │ Köln           │ 0176...    │ anna@... │ 5 Jahre      │ klein...│ 18.12  │ Neu    │
│    │            │          │                │            │          │ B2B, D2D     │         │        │        │
└────┴────────────┴──────────┴────────────────┴────────────┴──────────┴──────────────┴─────────┴────────┴────────┘
```

**What changed:**
- Added "Typ" column with visual indicators (🏢/👤)
- "Firma" renamed to "Firma/Standort" (context-aware)
- New "Erfahrung/Rolle" column showing:
  - For companies: Role (e.g., "Sales Manager")
  - For candidates: Years + Skills (e.g., "5 Jahre, B2B, D2D")

---

## 3. Leads Filter Panel

### BEFORE:
```
┌─ Filters ────────────────────────────────┐
│ Suche: [____________]                    │
│ Status: [Alle ▼]  Datum ab: [__________]│
└──────────────────────────────────────────┘
```

### AFTER:
```
┌─ Filters ─────────────────────────────────────────────────────┐
│ Suche: [____________]                                         │
│ Typ: [Alle ▼]  Status: [Alle ▼]  Datum ab: [__________]     │
│      [Firmen (Recruiter) ▼]                                  │
│      [Kandidaten ▼]                                           │
└───────────────────────────────────────────────────────────────┘
```

**What changed:** New "Typ" filter allows filtering by company or candidate leads.

---

## 4. API Stats Response

### NEW Endpoint: /api/stats/candidates

```json
{
  "total_candidates": 189,
  "today": 23,
  "with_experience": 145,
  "avg_experience_years": 4.7,
  "by_location": [
    {"location": "Köln", "count": 45},
    {"location": "Düsseldorf", "count": 38},
    {"location": "Essen", "count": 31},
    {"location": "Dortmund", "count": 28},
    {"location": "Bonn", "count": 19}
  ]
}
```

**What this provides:** Real-time statistics specifically for candidate leads.

---

## 5. Visual Type Indicators

### Color Coding:
- **🏢 Firma**: Blue badge `bg-blue-900 text-blue-200`
- **👤 Kandidat**: Purple badge `bg-purple-900 text-purple-200`

### Context-Aware Display:

**For Companies (Recruiter Mode):**
```
Name: Max Müller (Sales Manager)
Company: Acme GmbH
Experience/Role: Sales Manager
```

**For Candidates:**
```
Name: Anna Schmidt (aktiv suchend)
Location: Köln
Experience/Role: 5 Jahre
                B2B, Kaltakquise, D2D
```

---

## Quick Reference: When to Use Each Mode

### 🏢 Recruiter Mode
**Use when:** Finding companies that need sales people
**Shows:** Company names, contact persons, roles
**Queries:** Company websites, job postings, LinkedIn company pages

### 👤 Candidates Mode
**Use when:** Finding people looking for sales jobs
**Shows:** Names, locations, experience, availability
**Queries:** Kleinanzeigen job searches, "open to work" profiles, freelancer portals

---

**Note:** Both modes can run simultaneously by selecting "All Industries"
