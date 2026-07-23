import re

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database.connection import db
from app.database.models import Agendamento, Paciente
from app.routes.auth import login_required


pacientes_bp = Blueprint(
    "pacientes",
    __name__,
)


def somente_numeros(
    valor: str,
) -> str:
    return re.sub(
        r"\D",
        "",
        valor or "",
    )


def validar_email(
    email: str,
) -> bool:
    if not email:
        return True

    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            padrao,
            email,
        )
    )


def obter_dados_formulario() -> dict:
    return {
        "nome": request.form.get(
            "nome",
            "",
        ).strip(),
        "cpf": somente_numeros(
            request.form.get(
                "cpf",
                "",
            )
        ),
        "telefone": somente_numeros(
            request.form.get(
                "telefone",
                "",
            )
        ),
        "email": request.form.get(
            "email",
            "",
        ).strip().lower(),
    }


def validar_dados_paciente(
    dados: dict,
) -> list[str]:
    erros = []

    if not dados["nome"]:
        erros.append(
            "Informe o nome do paciente."
        )

    elif len(dados["nome"]) < 3:
        erros.append(
            "O nome deve possuir pelo menos 3 caracteres."
        )

    if not dados["cpf"]:
        erros.append(
            "Informe o CPF."
        )

    elif len(dados["cpf"]) != 11:
        erros.append(
            "O CPF deve possuir 11 números."
        )

    if dados["telefone"] and len(
        dados["telefone"]
    ) not in (10, 11):
        erros.append(
            "O telefone deve possuir 10 ou 11 números."
        )

    if not validar_email(
        dados["email"]
    ):
        erros.append(
            "Informe um endereço de e-mail válido."
        )

    return erros


@pacientes_bp.get("/pacientes")
@login_required
def listar_pacientes():
    termo = request.args.get(
        "search",
        "",
    ).strip()

    try:
        consulta = Paciente.query

        if termo:
            termo_like = f"%{termo}%"
            termo_numerico = somente_numeros(
                termo
            )

            filtros = [
                Paciente.nome.ilike(
                    termo_like
                ),
                Paciente.email.ilike(
                    termo_like
                ),
            ]

            if termo_numerico:
                filtros.extend(
                    [
                        Paciente.cpf.ilike(
                            f"%{termo_numerico}%"
                        ),
                        Paciente.telefone.ilike(
                            f"%{termo_numerico}%"
                        ),
                    ]
                )

            consulta = consulta.filter(
                or_(
                    *filtros
                )
            )

        pacientes = (
            consulta
            .order_by(
                Paciente.nome.asc()
            )
            .all()
        )

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao listar pacientes."
        )

        flash(
            "Não foi possível carregar os pacientes.",
            "danger",
        )

        pacientes = []

    return render_template(
        "pacientes/lista.html",
        pacientes=pacientes,
        termo=termo,
    )


@pacientes_bp.get("/pacientes/novo")
@login_required
def novo_paciente():
    return render_template(
        "pacientes/form.html",
        paciente=None,
        dados={},
        titulo="Novo paciente",
    )


@pacientes_bp.post("/pacientes/novo")
@login_required
def criar_paciente():
    dados = obter_dados_formulario()

    erros = validar_dados_paciente(
        dados
    )

    paciente_existente = None

    if dados["cpf"]:
        paciente_existente = (
            Paciente.query
            .filter_by(
                cpf=dados["cpf"]
            )
            .first()
        )

    if paciente_existente:
        erros.append(
            "Já existe um paciente cadastrado com esse CPF."
        )

    if erros:
        for erro in erros:
            flash(
                erro,
                "warning",
            )

        return render_template(
            "pacientes/form.html",
            paciente=None,
            dados=dados,
            titulo="Novo paciente",
        ), 400

    try:
        paciente = Paciente(
            nome=dados["nome"],
            cpf=dados["cpf"],
            telefone=(
                dados["telefone"]
                or None
            ),
            email=(
                dados["email"]
                or None
            ),
        )

        db.session.add(
            paciente
        )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        current_app.logger.exception(
            "Conflito de integridade ao criar paciente."
        )

        flash(
            "Já existe um paciente com os dados informados.",
            "danger",
        )

        return render_template(
            "pacientes/form.html",
            paciente=None,
            dados=dados,
            titulo="Novo paciente",
        ), 409

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Erro ao criar paciente."
        )

        flash(
            "Não foi possível cadastrar o paciente.",
            "danger",
        )

        return render_template(
            "pacientes/form.html",
            paciente=None,
            dados=dados,
            titulo="Novo paciente",
        ), 500

    flash(
        "Paciente cadastrado com sucesso.",
        "success",
    )

    return redirect(
        url_for(
            "pacientes.listar_pacientes"
        )
    )


@pacientes_bp.get(
    "/pacientes/<int:paciente_id>/editar"
)
@login_required
def editar_paciente(
    paciente_id: int,
):
    paciente = db.get_or_404(
        Paciente,
        paciente_id,
    )

    return render_template(
        "pacientes/form.html",
        paciente=paciente,
        dados={},
        titulo="Editar paciente",
    )


@pacientes_bp.post(
    "/pacientes/<int:paciente_id>/editar"
)
@login_required
def atualizar_paciente(
    paciente_id: int,
):
    paciente = db.get_or_404(
        Paciente,
        paciente_id,
    )

    dados = obter_dados_formulario()

    erros = validar_dados_paciente(
        dados
    )

    cpf_em_uso = (
        Paciente.query
        .filter(
            Paciente.id != paciente.id,
            Paciente.cpf == dados["cpf"],
        )
        .first()
    )

    if cpf_em_uso:
        erros.append(
            "O CPF informado pertence a outro paciente."
        )

    if erros:
        for erro in erros:
            flash(
                erro,
                "warning",
            )

        return render_template(
            "pacientes/form.html",
            paciente=paciente,
            dados=dados,
            titulo="Editar paciente",
        ), 400

    try:
        paciente.nome = dados["nome"]
        paciente.cpf = dados["cpf"]
        paciente.telefone = (
            dados["telefone"]
            or None
        )
        paciente.email = (
            dados["email"]
            or None
        )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        current_app.logger.exception(
            "Conflito ao atualizar paciente %s.",
            paciente.id,
        )

        flash(
            "Os dados informados já estão sendo utilizados.",
            "danger",
        )

        return render_template(
            "pacientes/form.html",
            paciente=paciente,
            dados=dados,
            titulo="Editar paciente",
        ), 409

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Erro ao atualizar paciente %s.",
            paciente.id,
        )

        flash(
            "Não foi possível atualizar o paciente.",
            "danger",
        )

        return render_template(
            "pacientes/form.html",
            paciente=paciente,
            dados=dados,
            titulo="Editar paciente",
        ), 500

    flash(
        "Paciente atualizado com sucesso.",
        "success",
    )

    return redirect(
        url_for(
            "pacientes.listar_pacientes"
        )
    )


@pacientes_bp.post(
    "/pacientes/<int:paciente_id>/excluir"
)
@login_required
def excluir_paciente(
    paciente_id: int,
):
    paciente = db.get_or_404(
        Paciente,
        paciente_id,
    )

    possui_agendamentos = (
        Agendamento.query
        .filter_by(
            paciente_id=paciente.id
        )
        .first()
    )

    if possui_agendamentos:
        flash(
            "O paciente não pode ser excluído porque possui "
            "agendamentos vinculados.",
            "warning",
        )

        return redirect(
            url_for(
                "pacientes.listar_pacientes"
            )
        )

    try:
        db.session.delete(
            paciente
        )

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Erro ao excluir paciente %s.",
            paciente.id,
        )

        flash(
            "Não foi possível excluir o paciente.",
            "danger",
        )

        return redirect(
            url_for(
                "pacientes.listar_pacientes"
            )
        )

    flash(
        "Paciente excluído com sucesso.",
        "success",
    )

    return redirect(
        url_for(
            "pacientes.listar_pacientes"
        )
    )