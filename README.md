# Notenverwaltung (Grades Tracker)

REST-API zur Erfassung von Studienleistungen, Noten und ECTS-Punkten mit automatisierter Berechnung des Notendurchschnitts (GPA). Entwickelt als Semesterprojekt im Modul **CDS212 (DevOps)** an der FHGR.

## Geplante Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/health` | Liveness-Probe (ohne Datenbank) |
| `GET` | `/ready` | Readiness-Probe (prüft Datenbankverbindung) |
| `GET` | `/metrics` | Prometheus-Metriken |
| `GET` | `/api/grades` | Alle Noteneinträge abrufen |
| `POST` | `/api/grades` | Neue Note erfassen (`course`, `grade`, `ects`) |
| `GET` | `/api/grades/gpa` | Gewichteten Gesamtschnitt berechnen |
| `DELETE` | `/api/grades/<id>` | Noteneintrag löschen |

## Voraussetzungen

- Python >= 3.12
- Docker & Docker Compose

## Lokale Installation (geplant)

```bash
git clone git@github.com:Philip123216/cds212-notenverwaltung.git
cd cds212-notenverwaltung
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
make run