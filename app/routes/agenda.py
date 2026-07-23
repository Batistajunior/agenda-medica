from datetime import date, datetime, time, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import db
from app.database.models import Agendamento, Paciente
from app.routes.auth import login_required
from app.services.exportacao import gerar_excel, gerar_pdf


agenda_bp = Blueprint(
    "agenda",
    __name__,
)


STATUS_VALIDOS = [
    "Agendado",
    "Confirmado",
    "Concluído",
    "Cancelado",
    "Faltou",
]

CORES_STATUS = {
    "Agendado": "#ffc107",
    "Confirmado": "#198754",
    "Concluído": "#0d6efd",
    "Cancelado": "#dc3545",
    "Faltou": "#6c757d",
}


def converter_data(
    valor: str,
) -> date | None:
    try:
        return datetime.strptime(
            valor,
            "%Y-%m-%d",
        ).date()

    except (TypeError, ValueError):
        return None


def converter_horario(
    valor: str,
) -> time | None:
    try:
        return datetime.strptime(
            valor,
            "%H:%M",
        ).time()

    except (TypeError, ValueError):
        return None


def montar_consulta_agendamentos(
    termo: str = "",
    status: str = "",
    data_inicio: date | None = None,
    data_fim: date | None = None,
):
    consulta = Agendamento.query.join(
        Paciente,
        Agendamento.paciente_id == Paciente.id,
    )

    if termo:
        termo_like = f"%{termo}%"

        consulta = consulta.filter(
            or_(
                Paciente.nome.ilike(termo_like),
                Paciente.cpf.ilike(termo_like),
                Agendamento.medico.ilike(termo_like),
                Agendamento.especialidade.ilike(termo_like),
                Agendamento.convenio.ilike(termo_like),
            )
        )

    if status:
        consulta = consulta.filter(Agendamento.status == status)

    if data_inicio:
        consulta = consulta.filter(Agendamento.data >= data_inicio)

    if data_fim:
        consulta = consulta.filter(Agendamento.data <= data_fim)

    return consulta.order_by(
        Agendamento.data.asc(),
        Agendamento.horario.asc(),
    )


def obter_filtros_requisicao() -> dict:
    return {
        "termo": request.args.get(
            "search",
            "",
        ).strip(),
        "status": request.args.get(
            "status",
            "",
        ).strip(),
        "data_inicio": converter_data(
            request.args.get(
                "data_inicio",
                "",
            )
        ),
        "data_fim": converter_data(
            request.args.get(
                "data_fim",
                "",
            )
        ),
    }


def serializar_agendamento(
    agendamento: Agendamento,
) -> dict:
    paciente = agendamento.paciente

    return {
        "id": agendamento.id,
        "paciente_id": agendamento.paciente_id,
        "paciente": paciente.nome if paciente else None,
        "cpf": paciente.cpf if paciente else None,
        "telefone": paciente.telefone if paciente else None,
        "data": (agendamento.data.strftime("%d/%m/%Y") if agendamento.data else None),
        "data_iso": (agendamento.data.isoformat() if agendamento.data else None),
        "horario": (
            agendamento.horario.strftime("%H:%M") if agendamento.horario else None
        ),
        "medico": agendamento.medico,
        "especialidade": agendamento.especialidade,
        "convenio": agendamento.convenio,
        "status": agendamento.status,
    }


def serializar_evento_calendario(
    agendamento: Agendamento,
) -> dict:
    inicio = datetime.combine(
        agendamento.data,
        agendamento.horario,
    )

    return {
        "id": agendamento.id,
        "title": (
            f"{agendamento.paciente.nome} — {agendamento.medico}"
            if agendamento.paciente
            else agendamento.medico
        ),
        "start": inicio.isoformat(),
        "end": (inicio + timedelta(minutes=30)).isoformat(),
        "url": url_for(
            "agenda.detalhes",
            agendamento_id=agendamento.id,
        ),
        "backgroundColor": CORES_STATUS.get(
            agendamento.status,
            "#0d6efd",
        ),
        "borderColor": CORES_STATUS.get(
            agendamento.status,
            "#0d6efd",
        ),
        "extendedProps": {
            "status": agendamento.status,
            "especialidade": agendamento.especialidade,
            "convenio": agendamento.convenio,
        },
    }


@agenda_bp.get("/dashboard")
@login_required
def dashboard():
    termo = request.args.get(
        "search",
        "",
    ).strip()

    status = request.args.get(
        "status",
        "",
    ).strip()

    data_inicio = converter_data(
        request.args.get(
            "data_inicio",
            "",
        )
    )

    data_fim = converter_data(
        request.args.get(
            "data_fim",
            "",
        )
    )

    try:
        agendamentos = montar_consulta_agendamentos(
            termo=termo,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
        ).all()

        hoje = date.today()

        total_hoje = Agendamento.query.filter(Agendamento.data == hoje).count()

        total_confirmados = Agendamento.query.filter(
            Agendamento.data == hoje,
            Agendamento.status == "Confirmado",
        ).count()

        total_agendados = Agendamento.query.filter(
            Agendamento.data == hoje,
            Agendamento.status == "Agendado",
        ).count()

        total_cancelados = Agendamento.query.filter(
            Agendamento.data == hoje,
            Agendamento.status == "Cancelado",
        ).count()

    except SQLAlchemyError:
        current_app.logger.exception("Erro ao carregar dashboard da agenda.")

        flash(
            "Não foi possível carregar os agendamentos.",
            "danger",
        )

        agendamentos = []
        total_hoje = 0
        total_confirmados = 0
        total_agendados = 0
        total_cancelados = 0

    return render_template(
        "agenda/dashboard.html",
        agendamentos=agendamentos,
        status_validos=STATUS_VALIDOS,
        termo=termo,
        status_selecionado=status,
        data_inicio=(data_inicio.isoformat() if data_inicio else ""),
        data_fim=(data_fim.isoformat() if data_fim else ""),
        total_hoje=total_hoje,
        total_confirmados=total_confirmados,
        total_agendados=total_agendados,
        total_cancelados=total_cancelados,
    )


@agenda_bp.get("/agenda/novo")
@login_required
def novo():
    pacientes = Paciente.query.order_by(Paciente.nome.asc()).all()

    return render_template(
        "agenda/form.html",
        agendamento=None,
        pacientes=pacientes,
        status_validos=STATUS_VALIDOS,
        titulo="Novo agendamento",
    )


@agenda_bp.post("/agenda/novo")
@login_required
def criar():
    paciente_id = request.form.get(
        "paciente_id",
        type=int,
    )

    data_consulta = converter_data(
        request.form.get(
            "data",
            "",
        )
    )

    horario = converter_horario(
        request.form.get(
            "horario",
            "",
        )
    )

    medico = request.form.get(
        "medico",
        "",
    ).strip()

    especialidade = request.form.get(
        "especialidade",
        "",
    ).strip()

    convenio = request.form.get(
        "convenio",
        "",
    ).strip()

    status = request.form.get(
        "status",
        "Agendado",
    ).strip()

    if not paciente_id:
        flash(
            "Selecione um paciente.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    paciente = db.session.get(
        Paciente,
        paciente_id,
    )

    if paciente is None:
        flash(
            "Paciente não encontrado.",
            "danger",
        )

        return redirect(url_for("agenda.novo"))

    if not data_consulta:
        flash(
            "Informe uma data válida.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    if not horario:
        flash(
            "Informe um horário válido.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    if not medico:
        flash(
            "Informe o nome do médico.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    if not especialidade:
        flash(
            "Informe a especialidade.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    if status not in STATUS_VALIDOS:
        flash(
            "Status inválido.",
            "warning",
        )

        return redirect(url_for("agenda.novo"))

    conflito = Agendamento.query.filter_by(
        data=data_consulta,
        horario=horario,
        medico=medico,
    ).first()

    if conflito is not None:
        flash(
            "Já existe um agendamento para esse médico " "na mesma data e horário.",
            "danger",
        )

        return redirect(url_for("agenda.novo"))

    try:
        agendamento = Agendamento(
            paciente_id=paciente.id,
            data=data_consulta,
            horario=horario,
            medico=medico,
            especialidade=especialidade,
            convenio=convenio or "Particular",
            status=status,
        )

        db.session.add(agendamento)

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception("Erro ao criar agendamento.")

        flash(
            "Não foi possível criar o agendamento.",
            "danger",
        )

        return redirect(url_for("agenda.novo"))

    flash(
        "Agendamento criado com sucesso.",
        "success",
    )

    return redirect(url_for("agenda.dashboard"))
@agenda_bp.get("/agenda/<int:agendamento_id>")
@login_required
def detalhes(
    agendamento_id: int,
):
    agendamento = db.get_or_404(
        Agendamento,
        agendamento_id,
    )

    return render_template(
        "agenda/detalhes.html",
        agendamento=agendamento,
    )


@agenda_bp.get("/agenda/<int:agendamento_id>/editar")
@login_required
def editar(
    agendamento_id: int,
):
    agendamento = db.get_or_404(
        Agendamento,
        agendamento_id,
    )

    pacientes = Paciente.query.order_by(
        Paciente.nome.asc()
    ).all()

    return render_template(
        "agenda/form.html",
        agendamento=agendamento,
        pacientes=pacientes,
        status_validos=STATUS_VALIDOS,
        titulo="Editar agendamento",
    )


@agenda_bp.post("/agenda/<int:agendamento_id>/editar")
@login_required
def atualizar(
    agendamento_id: int,
):
    agendamento = db.get_or_404(
        Agendamento,
        agendamento_id,
    )

   
    paciente_id = request.form.get(
        "paciente_id",
        type=int,
    )

    data_consulta = converter_data(
        request.form.get(
            "data",
            "",
        )
    )

    horario = converter_horario(
        request.form.get(
            "horario",
            "",
        )
    )

    medico = request.form.get(
        "medico",
        "",
    ).strip()

    especialidade = request.form.get(
        "especialidade",
        "",
    ).strip()

    convenio = request.form.get(
        "convenio",
        "",
    ).strip()

    status = request.form.get(
        "status",
        "",
    ).strip()

    paciente = db.session.get(
        Paciente,
        paciente_id,
    )

    if paciente is None:
        flash(
            "Paciente inválido.",
            "warning",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    if not data_consulta or not horario:
        flash(
            "Informe data e horário válidos.",
            "warning",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    if not medico or not especialidade:
        flash(
            "Informe médico e especialidade.",
            "warning",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    if status not in STATUS_VALIDOS:
        flash(
            "Status inválido.",
            "warning",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    conflito = Agendamento.query.filter(
        Agendamento.id != agendamento.id,
        Agendamento.data == data_consulta,
        Agendamento.horario == horario,
        Agendamento.medico == medico,
    ).first()

    if conflito is not None:
        flash(
            "Já existe outro agendamento para esse médico " "na mesma data e horário.",
            "danger",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    try:
        agendamento.paciente_id = paciente.id
        agendamento.data = data_consulta
        agendamento.horario = horario
        agendamento.medico = medico
        agendamento.especialidade = especialidade
        agendamento.convenio = convenio or "Particular"
        agendamento.status = status

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Erro ao atualizar agendamento %s.",
            agendamento.id,
        )

        flash(
            "Não foi possível atualizar o agendamento.",
            "danger",
        )

        return redirect(
            url_for(
                "agenda.editar",
                agendamento_id=agendamento.id,
            )
        )

    flash(
        "Agendamento atualizado com sucesso.",
        "success",
    )

    return redirect(url_for("agenda.dashboard"))


@agenda_bp.post("/agenda/<int:agendamento_id>/excluir")
@login_required
def excluir(
    agendamento_id: int,
):
    agendamento = db.get_or_404(
        Agendamento,
        agendamento_id,
    )

    try:
        db.session.delete(agendamento)

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Erro ao excluir agendamento %s.",
            agendamento.id,
        )

        flash(
            "Não foi possível excluir o agendamento.",
            "danger",
        )

        return redirect(url_for("agenda.dashboard"))

    flash(
        "Agendamento excluído com sucesso.",
        "success",
    )

    return redirect(url_for("agenda.dashboard"))


@agenda_bp.get("/calendario")
@login_required
def calendario():
    return render_template(
        "agenda/calendario.html",
        status_validos=STATUS_VALIDOS,
        cores_status=CORES_STATUS,
    )


@agenda_bp.get("/api/dashboard/stats")
@login_required
def dashboard_stats():
    try:
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=6)

        status_hoje = (
            db.session.query(
                Agendamento.status,
                func.count(Agendamento.id),
            )
            .filter(Agendamento.data == hoje)
            .group_by(Agendamento.status)
            .all()
        )

        consultas_por_dia = (
            db.session.query(
                Agendamento.data,
                func.count(Agendamento.id),
            )
            .filter(Agendamento.data >= inicio_semana)
            .filter(Agendamento.data <= hoje)
            .group_by(Agendamento.data)
            .order_by(Agendamento.data.asc())
            .all()
        )

        dias = {}
        dia_atual = inicio_semana

        while dia_atual <= hoje:
            dias[dia_atual.isoformat()] = 0
            dia_atual += timedelta(days=1)

        for dia, total in consultas_por_dia:
            dias[dia.isoformat()] = total

        return jsonify(
            {
                "success": True,
                "status_hoje": {
                    item[0]: item[1] for item in status_hoje
                },
                "consultas_por_dia": {
                    "labels": [
                        datetime.strptime(
                            chave,
                            "%Y-%m-%d",
                        ).strftime("%d/%m")
                        for chave in dias.keys()
                    ],
                    "valores": list(dias.values()),
                },
                "cores_status": CORES_STATUS,
            }
        )

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao carregar estatísticas do dashboard."
        )

        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        "Não foi possível carregar "
                        "as estatísticas."
                    ),
                }
            ),
            500,
        )


@agenda_bp.get("/api/agenda/calendario")
@login_required
def listar_calendario():
    filtros = obter_filtros_requisicao()

    try:
        agendamentos = montar_consulta_agendamentos(
            **filtros,
        ).all()

        return jsonify(
            [
                serializar_evento_calendario(item)
                for item in agendamentos
            ]
        )

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao consultar eventos do calendário."
        )

        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        "Não foi possível carregar "
                        "o calendário."
                    ),
                }
            ),
            500,
        )


@agenda_bp.get("/agenda/exportar/excel")
@login_required
def exportar_excel():
    filtros = obter_filtros_requisicao()

    try:
        agendamentos = montar_consulta_agendamentos(
            **filtros,
        ).all()

        buffer = gerar_excel(agendamentos)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="agendamentos.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao exportar agendamentos para Excel."
        )

        flash(
            "Não foi possível exportar para Excel.",
            "danger",
        )

        return redirect(url_for("agenda.dashboard"))


@agenda_bp.get("/agenda/exportar/pdf")
@login_required
def exportar_pdf():
    filtros = obter_filtros_requisicao()

    try:
        agendamentos = montar_consulta_agendamentos(
            **filtros,
        ).all()

        buffer = gerar_pdf(agendamentos)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="agendamentos.pdf",
            mimetype="application/pdf",
        )

    except SQLAlchemyError:
        current_app.logger.exception(
            "Erro ao exportar agendamentos para PDF."
        )

        flash(
            "Não foi possível exportar para PDF.",
            "danger",
        )

        return redirect(url_for("agenda.dashboard"))


@agenda_bp.get("/api/agenda")
@login_required
def listar():
    filtros = obter_filtros_requisicao()

    try:
        agendamentos = montar_consulta_agendamentos(
            **filtros,
        ).all()

        return jsonify(
            {
                "success": True,
                "total": len(agendamentos),
                "data": [
                    serializar_agendamento(agendamento)
                    for agendamento in agendamentos
                ],
            }
        )

    except SQLAlchemyError:
        current_app.logger.exception("Erro ao consultar API da agenda.")

        return (
            jsonify(
                {
                    "success": False,
                    "message": ("Não foi possível consultar " "os agendamentos."),
                }
            ),
            500,
        )


