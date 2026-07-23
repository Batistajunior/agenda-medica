import os
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import db
from app.routes.agenda import agenda_bp
from app.routes.auth import auth_bp
from app.routes.pacientes import pacientes_bp


def create_app() -> Flask:
    load_dotenv()

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    database_path = (
        Path(app.instance_path)
        / "agenda_medica.db"
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "agenda-medica-secret-development",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{database_path.as_posix()}",
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(pacientes_bp)

    @app.get("/health")
    def health():
        try:
            db.session.execute(
                text("SELECT 1")
            )

            return jsonify(
                {
                    "status": "ok",
                    "database": "ok",
                }
            ), 200

        except SQLAlchemyError:
            app.logger.exception(
                "Falha ao acessar o banco."
            )

            return jsonify(
                {
                    "status": "degraded",
                    "database": "unavailable",
                    "message": (
                        "Banco de dados temporariamente "
                        "indisponível."
                    ),
                }
            ), 503

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "message": "Recurso não encontrado.",
                }
            ), 404

        return render_template(
            "error.html",
            title="Página não encontrada",
            message=(
                "A página solicitada não foi encontrada."
            ),
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()

        app.logger.error(
            "Erro interno não tratado: %s",
            error,
            exc_info=True,
        )

        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "message": (
                        "Não foi possível concluir "
                        "a operação."
                    ),
                }
            ), 500

        return render_template(
            "error.html",
            title="Erro inesperado",
            message=(
                "Não foi possível concluir a operação. "
                "Tente novamente."
            ),
        ), 500

    return app