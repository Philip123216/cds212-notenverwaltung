# Deployment-Runbook – Notenverwaltung (Grades Tracker)

Dieses Dokument beschreibt die Voraussetzungen, den Betrieb, die Verifikation und das Störungsmanagement für die **Notenverwaltung** (CDS212 DevOps Semesterprojekt).

- **Primäre Produktions-URL:** https://cds212-notenverwaltung.onrender.com
- **Zielplattform:** Render (PaaS, Free Tier, Region Frankfurt)

---

## A. Voraussetzungen

Bevor das Deployment durchgeführt werden kann, müssen folgende Konten und Tools vorhanden sein:

### Benötigte Konten
- **GitHub:** Zugriff auf das Repository `Philip123216/cds212-notenverwaltung`
- **Render:** Kostenloses Konto auf [render.com](https://render.com), verknüpft mit GitHub

### Lokale Werkzeuge (mit Prüfbefehl)
```bash
git --version      # erwartet: git version 2.x
docker --version   # erwartet: Docker version 24.x oder höher
curl --version     # erwartet: curl 7.x oder 8.x
python3 --version  # erwartet: Python 3.12.x
```

---

## B. Lokale Installation (Entwicklung)

Zur lokalen Ausführung und für Integrationstests:

```bash
# 1. Repository klonen & wechseln
git clone git@github.com:Philip123216/cds212-notenverwaltung.git
cd cds212-notenverwaltung

# 2. Virtuelle Umgebung einrichten
python3 -m venv .venv
source .venv/bin/activate
make install

# 3. Tests & Linter prüfen
make test
make lint

# 4. Lokal starten (Port 8000)
make run
```
**Lokale Verifikation:**
```bash
curl http://127.0.0.1:8000/health
# Erwartete Ausgabe: {"status":"ok","version":"0.0.0-dev"}
```

---

## C. Konfigurationsvariablen (12-Factor III)

Alle Konfigurationen werden ausschliesslich über Umgebungsvariablen gesteuert:

| Variable | Standardwert | Geheim? | Beschreibung / Wirkung |
|---|---|---|---|
| `PORT` | `10000` (Render) | Nein | Port, an den Render Anfragen leitet. **Muss auf `8000` gesetzt werden!** |
| `APP_VERSION` | `0.0.0-dev` | Nein | Versionsnummer, erscheint in `/health` und `/metrics` |
| `LOG_LEVEL` | `INFO` | Nein | Schwellwert für Logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `GUNICORN_WORKERS` | `1` | Nein | Anzahl Worker-Prozesse (im In-Memory-Betrieb zwingend `1`) |
| `DATABASE_URL` | *(leer)* | **Ja** | PostgreSQL-Verbindungsstring. Leer = In-Memory, gesetzt = Postgres |

> **Sicherheitsregel:** Geheimnisse wie `DATABASE_URL` gehören **niemals** ins Git-Repository (Datei `.env` ist in `.gitignore`). Auf Render werden sie unter *Environment Variables* als Secret eingetragen.

---

## D. Deployment-Schritte auf Render

1. Auf [dashboard.render.com](https://dashboard.render.com) einloggen.
2. Oben rechts auf **New +** $\to$ **Web Service** klicken.
3. Repository `Philip123216/cds212-notenverwaltung` verbinden.
4. Folgende Einstellungen wählen:
   - **Name:** `cds212-notenverwaltung`
   - **Region:** `Frankfurt (EU Central)`
   - **Branch:** `main`
   - **Root Directory:** *(leer lassen)*
   - **Runtime:** `Docker`
   - **Instance Type:** `Free`
5. **Environment Variables** hinzufügen:
   - `PORT` = `8000`
   - `APP_VERSION` = `1.0.0`
   - `LOG_LEVEL` = `INFO`
   - `GUNICORN_WORKERS` = `1`
6. Unter **Advanced**:
   - **Health Check Path:** `/health`
   - **Auto-Deploy:** `Yes`
7. Auf **Deploy Web Service** klicken.

---

## E. Verifikation nach dem Deployment

Nachdem Render `Deploy succeeded | Live` meldet, wird die Funktion live geprüft:

### 1. Liveness-Probe abfragen
```bash
curl -i https://cds212-notenverwaltung.onrender.com/health
```
**Erwartete Ausgabe:**
```text
HTTP/2 200
content-type: application/json
{"status":"ok","version":"1.0.0"}
```

### 2. Noten-API testen (End-to-End)
```bash
# Note anlegen
curl -X POST https://cds212-notenverwaltung.onrender.com/api/grades \
  -H "Content-Type: application/json" \
  -d '{"course":"DevOps-Live","grade":5.5,"ects":4}'

# Notenschnitt abrufen
curl https://cds212-notenverwaltung.onrender.com/api/grades/gpa
```

---

## F. Rollback-Anleitung

Sollte ein fehlerhafter Deploy in Produktion gelangen:

1. **Schnelles Rollback über Render Dashboard:**
   - Navigiere zu *Render Dashboard* $\to$ *cds212-notenverwaltung* $\to$ **Deploys**.
   - Wähle den letzten stabilen Deploy aus der Liste aus.
   - Klicke rechts oben auf das Dreipunkt-Menü $\to$ **Rollback to this deploy**.
   - Render startet sofort das vorherige Container-Image neu.
2. **Rollback über Git (Dauerhafter Fix):**
   - Im lokalen Repository:
     ```bash
     git revert <fehlerhafter-commit-hash>
     git push origin main
     ```
   - Render erkennt den Push auf `main` und rollt automatisch die Vorversion aus.

> **Grenzen des Rollbacks:** Ein Rollback stellt den Codezustand wieder her. Datenbankmigrationen oder bereits in eine Datenbank geschriebene Daten werden dadurch nicht automatisch zurückgerollt.

---

## G. Troubleshooting (Störungsbehebung)

| Symptom | Ursache | Lösung |
|---|---|---|
| **Deploy hängt / „No open ports detected“** | Port-Mismatch. Render leitet an Port 10000, der Container lauscht auf 8000. | In Render unter *Environment Variables* `PORT=8000` setzen. |
| **Deploy scheitert endlos mit „unhealthy“** | Health Check Path fälschlicherweise auf `/ready` statt `/health` gesetzt. | Unter *Settings* $\to$ *Health Check Path* auf `/health` ändern (Liveness prüft keine DB). |
| **Erster Aufruf dauert 30–60 Sekunden** | Free-Tier **Cold Start**. Render legt inaktive Instanzen nach 15 Min. schlafen. | Kein Fehler! Geduld beim ersten Request; folgende Requests sind sofort da. |
| **Geleaktes Secret im Git-Repo** | Eine `.env`-Datei wurde versehentlich committet und gepusht. | **Sofortiges Rotieren:** In der Datenbank/Cloud neues Passwort setzen! `git rm` reicht nicht. |

---

## H. Kontakt und Eskalation

- **Service Owner:** Philip Solinger (`@Philip123216`)
- **Eskalation:** Bei Störungen $> 30$ Minuten: Issue im GitHub-Repository eröffnen oder Benachrichtigung via Hochschul-Mail.
```