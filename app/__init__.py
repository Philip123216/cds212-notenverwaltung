from __future__ import annotations

import logging

from flask import Flask
from prometheus_client import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics

from app.config import Config
from app.repository import GradeRepository, create_repository


def create_app(
    config: Config | None = None,
    repository: GradeRepository | None = None,
    registry: CollectorRegistry | None = None,
) -> Flask:
    config = config or Config.from_env()

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = Flask(__name__)
    app.extensions["app_config"] = config
    app.extensions["repository"] = repository or create_repository(config)

    metrics = PrometheusMetrics(app, registry=registry)
    metrics.info("notenverwaltung_info", "Application info", version=config.version)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
