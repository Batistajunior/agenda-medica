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
    """
    Cria e configura a aplicação Flask.

    A função utiliza o padrão Application Factory, permitindo
    configurações diferentes para desenvolvimento, testes e produção.
    """

    load_dotenv()

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    # Garante que a pasta instance exista.
    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    banco_sqlite = (
        Path(app.instance_path)
        / "agenda.db"
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "agenda-medica-secret-development",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{banco_sqlite.as_posix()}",
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    # Configurações de segurança dos cookies.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Em produção com HTTPS, defina COOKIE_SECURE=1.
    app.config["SESSION_COOKIE_SECURE"] = (
        os.getenv(
            "COOKIE_SECURE",
            "0",
        )
        == "1"
    )

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(pacientes_bp)

    @app.get("/health")
    def health():
        """
        Verifica se a aplicação e o banco estão disponíveis.
        """

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
                "Falha ao acessar o banco no health check."
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
        """
        Trata páginas e recursos inexistentes.
        """

        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
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
        """
        Trata erros internos não capturados.
        """

        db.session.rollback()

        app.logger.error(
            "Erro interno não tratado: %s",
            error,
            exc_info=True,
        )

        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
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