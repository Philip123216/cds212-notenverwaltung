from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.models import (
    ValidationError,
    validate_course,
    validate_ects,
    validate_grade_value,
)

bp = Blueprint("main", __name__)


def _repo():
    return current_app.extensions["repository"]


def _config():
    return current_app.extensions["app_config"]


@bp.errorhandler(ValidationError)
def _handle_validation_error(exc: ValidationError):
    return jsonify(error=str(exc)), 400


@bp.get("/health")
def health():
    """Liveness probe: läuft der Prozess? Prüft NIE die Datenbank."""
    return jsonify(status="ok", version=_config().version)


@bp.get("/ready")
def ready():
    """Readiness probe: kann die App Anfragen bedienen? Prüft DB."""
    if _repo().healthy():
        return jsonify(status="ready")
    return jsonify(status="unavailable"), 503


@bp.get("/api/grades")
def list_grades():
    return jsonify([g.to_dict() for g in _repo().list()])


@bp.post("/api/grades")
def create_grade():
    payload = request.get_json(silent=True) or {}
    course = validate_course(payload.get("course"))
    grade_val = validate_grade_value(payload.get("grade"))
    ects = validate_ects(payload.get("ects"))
    entry = _repo().add(course, grade_val, ects)
    return jsonify(entry.to_dict()), 201


@bp.get("/api/grades/<int:grade_id>")
def get_grade(grade_id: int):
    entry = _repo().get(grade_id)
    if entry is None:
        return jsonify(error="grade not found"), 404
    return jsonify(entry.to_dict())


@bp.delete("/api/grades/<int:grade_id>")
def delete_grade(grade_id: int):
    if not _repo().delete(grade_id):
        return jsonify(error="grade not found"), 404
    return "", 204


@bp.get("/api/grades/gpa")
def calculate_gpa():
    grades = _repo().list()
    if not grades:
        return jsonify(gpa=0.0, total_ects=0, count=0)
    total_weighted = sum(g.grade * g.ects for g in grades)
    total_ects = sum(g.ects for g in grades)
    gpa = round(total_weighted / total_ects, 2)
    return jsonify(gpa=gpa, total_ects=total_ects, count=len(grades))
