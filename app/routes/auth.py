from functools import wraps
from typing import Any, Callable

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import Usuario


auth_bp = Blueprint(
    "auth",
    __name__,
)


def login_required(
    view: Callable[..., Any],
) -> Callable[..., Any]:
    """
    Protege páginas e endpoints que exigem autenticação.

    Para endpoints da API, retorna HTTP 401 em JSON.
    Para páginas HTML, redireciona para a tela de login.
    """

    @wraps(view)
    def wrapped_view(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not session.get("usuario_id"):
            if request.path.startswith("/api/"):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": ("Sessão expirada. " "Faça login novamente."),
                        }
                    ),
                    401,
                )

            flash(
                "Faça login para acessar o sistema.",
                "warning",
            )

            return redirect(url_for("auth.login"))

        return view(
            *args,
            **kwargs,
        )

    return wrapped_view


@auth_bp.get("/")
def login() -> Response | str:
    """
    Exibe a tela de login.

    Caso o usuário já esteja autenticado,
    redireciona para o painel da agenda.
    """

    if session.get("usuario_id"):
        return redirect(url_for("agenda.dashboard"))

    return render_template(
        "login.html",
        usuario_informado="",
    )


@auth_bp.post("/login")
def autenticar() -> Response | tuple[str, int]:
    """
    Valida usuário e senha e cria a sessão.
    """

    usuario_informado = request.form.get("usuario", "").strip()

    senha_informada = request.form.get(
        "senha",
        "",
    )

    if not usuario_informado:
        flash(
            "Informe o usuário.",
            "warning",
        )

        return (
            render_template(
                "login.html",
                usuario_informado=usuario_informado,
            ),
            400,
        )

    if not senha_informada:
        flash(
            "Informe a senha.",
            "warning",
        )

        return (
            render_template(
                "login.html",
                usuario_informado=usuario_informado,
            ),
            400,
        )

    try:
        usuario = Usuario.query.filter_by(
            usuario=usuario_informado,
            ativo=True,
        ).first()

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao consultar o usuário '%s' no banco.",
            usuario_informado,
        )

        flash(
            "Não foi possível acessar o sistema agora. "
            "Tente novamente em alguns instantes.",
            "danger",
        )

        return (
            render_template(
                "login.html",
                usuario_informado=usuario_informado,
            ),
            500,
        )

    credenciais_invalidas = usuario is None or not usuario.verificar_senha(
        senha_informada
    )

    if credenciais_invalidas:
        current_app.logger.warning(
            "Tentativa de login inválida para o usuário '%s'.",
            usuario_informado,
        )

        flash(
            "Usuário ou senha inválidos.",
            "danger",
        )

        return (
            render_template(
                "login.html",
                usuario_informado=usuario_informado,
            ),
            401,
        )

    session.clear()

    session["usuario_id"] = usuario.id
    session["usuario"] = usuario.usuario

    # Utilizado pelo base.html para mostrar o usuário no menu.
    session["usuario_nome"] = usuario.usuario

    current_app.logger.info(
        "Login realizado com sucesso pelo usuário '%s'.",
        usuario.usuario,
    )

    flash(
        f"Bem-vindo, {usuario.usuario}!",
        "success",
    )

    return redirect(url_for("agenda.dashboard"))


@auth_bp.get("/logout")
def logout() -> Response:
    """
    Encerra a sessão do usuário.
    """

    usuario_logado = session.get(
        "usuario",
        "desconhecido",
    )

    session.clear()

    current_app.logger.info(
        "Logout realizado pelo usuário '%s'.",
        usuario_logado,
    )

    flash(
        "Sessão encerrada com sucesso.",
        "success",
    )

    return redirect(url_for("auth.login"))
