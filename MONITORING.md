# Monitoring & DevSecOps – Notenverwaltung

Dieses Dokument beschreibt die Überwachung (Metriken, Dashboards, SLOs, Alarmierung) sowie das automatisierte Sicherheits-Scanning (DevSecOps) für die **Notenverwaltung**.

---

## 1. Was wird erhoben? (Metriken & Prometheus)

Die Anwendung exponiert unter `/metrics` Metriken im Prometheus-Format (via `prometheus-flask-exporter`). Prometheus arbeitet nach dem **Pull-Modell** und scrapt die Anwendung alle 15 Sekunden.

| Metrik | Typ | Bedeutung |
|---|---|---|
| `flask_http_request_total` | Counter | Anzahl aller HTTP-Anfragen nach Methode, Pfad und Statuscode |
| `flask_http_request_duration_seconds` | Histogram | Verteilung der Antwortzeiten in Buckets (`le`) |
| `notenverwaltung_info` | Gauge | Aktuelle App-Version (`version`-Label) |

- **Scrape-Ziel:** `web:8000/metrics` (Konfiguration: [`monitoring/prometheus/prometheus.yml`](monitoring/prometheus/prometheus.yml))
- **Kontrolle:** Unter `http://localhost:9090/targets` muss der Job `notenverwaltung` auf **UP** stehen.

> **Datenschutz & Kardinalität (DSG/DSGVO):** Noten, Kursnamen oder Benutzerdaten werden **niemals** als Prometheus-Labels oder im Klartext in Logs erfasst. Das schützt sensible Studierendendaten und verhindert eine Kardinalitätsexplosion im Zeitreihenspeicher.

---

## 2. Grafana-Dashboard „Notenverwaltung Overview“

Das Dashboard ist vollständig als JSON versioniert unter [`monitoring/grafana/dashboards/notenverwaltung-overview.json`](monitoring/grafana/dashboards/notenverwaltung-overview.json) und wird automatisch provisioniert.

| Panel | PromQL-Abfrage | Betriebliche Frage & Normalbereich | Eingriffsschwelle |
|---|---|---|---|
| **Request-Rate** | `sum(rate(flask_http_request_total[5m]))` | Wie hoch ist der Traffic (req/s)? Normal: je nach Nutzung $> 0$ req/s | Plötzlicher Abfall auf `0` oder extremer Spike (DoS/Last) |
| **Fehlerrate 5xx** | `sum(rate(flask_http_request_total{status=~"5.."}[5m])) / sum(rate(flask_http_request_total[5m]))` | Welcher Anteil der Requests scheitert serverseitig? Normal: `0 %` (`4xx` sind Client-Fehler und bewusst ausgeschlossen) | **`> 5 %`** über 5 Minuten |
| **p95-Latenz** | `histogram_quantile(0.95, sum by (le) (rate(flask_http_request_duration_seconds_bucket[5m])))` | Wie schnell sind 95 % der Antworten? Normal: `< 50 ms` | **`> 1.0 s`** über 5 Minuten |
| **App-Version** | `notenverwaltung_info` | Welche Version ist ausgerollt? Normal: aktive Release-Version (z. B. `1.0.0`) | Abweichung nach Rollout/Rollback prüfen |

---

## 3. Service Level Objectives (SLOs) & Error Budget

Ein Ziel von 100 % Verfügbarkeit lässt keinen Raum für Wartungen und Deployments. Für die Notenverwaltung gelten folgende SLOs über ein Zeitfenster von **30 Tagen** ($43\,200$ Minuten):

1. **Verfügbarkeit / Erfolgsrate (SLI: Anteil nicht-5xx-Antworten):**
   - **SLO:** $99{,}9\,\%$ aller Anfragen über 30 Tage sind erfolgreich (kein 5xx-Fehler).
   - **Error Budget:** $0{,}1\,\% \times 43\,200\text{ min} = \mathbf{43{,}2\text{ Minuten}}$ erlaubte Ausfall-/Fehlerzeit pro Monat.
2. **Latenz (SLI: Dauer der API-Antworten laut Histogramm):**
   - **SLO:** $95\,\%$ aller Anfragen über 30 Tage werden in unter $\mathbf{300\text{ ms}}$ beantwortet.
   - **Error Budget:** $5\,\%$ der Anfragen dürfen die 300-ms-Marke überschreiten.

---

## 4. Alarmierung & Schwellwerte

Alle Alarme in [`monitoring/prometheus/alert.rules.yml`](monitoring/prometheus/alert.rules.yml) sind **symptombasiert** (alarmiert wird auf Auswirkungen für Nutzer, nicht auf reine Ursachen wie CPU-Last):

| Alarm | Bedingung | `for` | Severity | Runbook-Skizze (Erste Massnahmen) |
|---|---|---|---|---|
| `NotenverwaltungDown` | `up{job="notenverwaltung"} == 0` | `1m` | `critical` | 1. Container/Pod-Status prüfen (`docker ps` / `kubectl get pods`)<br>2. Logs auf Crash prüfen (`--previous`)<br>3. Dienst neustarten |
| `HighErrorRate` | 5xx-Anteil $> 0.05$ (5 %) | `5m` | `warning` | 1. Logs nach `ERROR` filtern<br>2. DB-Erreichbarkeit über `/ready` prüfen<br>3. Bei defektem Release: Rollback einleiten |
| `HighLatencyP95` | p95-Latenz $> 1\text{ s}$ | `5m` | `warning` | 1. Datenbank-Antwortzeiten prüfen<br>2. Traffic-Spitze im Request-Rate-Panel prüfen |

---

## 5. DevSecOps & Trivy-Sicherheitsgate

Nach dem **Shift-Left-Prinzip** wird das gebaute Docker-Image bei jedem Pull Request und jedem Push auf `main` automatisch in der CI-Pipeline (`.github/workflows/ci.yml`) mit **Trivy** gescannt:

- **Konfigurierter Schwellwert:** `severity: CRITICAL,HIGH`
- **Gate-Verhalten:** `exit-code: "1"` (Bricht den CI-Build hart ab, sobald behebbare hohe oder kritische Schwachstellen gefunden werden).
- **Umgang mit `not fixed`-Funden:** Durch `ignore-unfixed: true` blockiert die Pipeline nicht an Lücken, für die vom Hersteller noch kein Patch existiert. Solche Funde werden bewusst geprüft, ggf. befristet in `.trivyignore` dokumentiert und über regelmässige Basis-Image-Updates (`python:3.12-slim`) behoben.
- **Secret-Hygiene:** Secrets (`DATABASE_URL`, Passwörter) liegen nie im Code oder Image, sondern ausschliesslich als Umgebungsvariablen bzw. GitHub Secrets.