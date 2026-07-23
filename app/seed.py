from datetime import date, time

from app import create_app
from app.database.connection import db
from app.database.models import (
    Agendamento,
    Paciente,
    Usuario,
)


app = create_app()


def criar_usuario_admin():
    usuario = Usuario.query.filter_by(
        usuario="admin"
    ).first()

    if usuario is not None:
        print(
            "Usuário admin já existe."
        )

        return usuario

    usuario = Usuario(
        usuario="admin",
        ativo=True,
    )

    usuario.definir_senha(
        "123456"
    )

    db.session.add(
        usuario
    )

    print(
        "Usuário admin criado."
    )

    return usuario


def criar_pacientes():
    if Paciente.query.count() > 0:
        print(
            "Pacientes já existem."
        )

        return Paciente.query.all()

    pacientes = [
        Paciente(
            nome="Maria Souza",
            cpf="11111111112",
            telefone="71999999999",
            email="maria.souza@email.com",
        ),
        Paciente(
            nome="Antonio Carlos",
            cpf="22222222223",
            telefone="71888888888",
            email="antonio.carlos@email.com",
        ),
        Paciente(
            nome="Juliana Santos",
            cpf="33333333334",
            telefone="71777777777",
            email="juliana.santos@email.com",
        ),
    ]

    db.session.add_all(
        pacientes
    )

    db.session.flush()

    print(
        "Pacientes iniciais criados."
    )

    return pacientes


def criar_agendamentos(pacientes):
    if Agendamento.query.count() > 0:
        print(
            "Agendamentos já existem."
        )

        return

    agendamentos = [
        Agendamento(
            paciente_id=pacientes[0].id,
            data=date.today(),
            horario=time(8, 0),
            medico="Dr. João Silva",
            especialidade="Cardiologia",
            convenio="Unimed",
            status="Confirmado",
        ),
        Agendamento(
            paciente_id=pacientes[1].id,
            data=date.today(),
            horario=time(9, 30),
            medico="Dra. Ana Costa",
            especialidade="Clínica Geral",
            convenio="Bradesco Saúde",
            status="Agendado",
        ),
        Agendamento(
            paciente_id=pacientes[2].id,
            data=date.today(),
            horario=time(11, 0),
            medico="Dr. Paulo Lima",
            especialidade="Ortopedia",
            convenio="Particular",
            status="Agendado",
        ),
    ]

    db.session.add_all(
        agendamentos
    )

    print(
        "Agendamentos iniciais criados."
    )


def executar_seed():
    with app.app_context():
        db.create_all()

        criar_usuario_admin()

        pacientes = criar_pacientes()

        criar_agendamentos(
            pacientes
        )

        db.session.commit()

        print(
            "Banco inicializado com sucesso."
        )


if __name__ == "__main__":
    executar_seed()