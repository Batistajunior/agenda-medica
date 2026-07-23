from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.database.connection import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    usuario = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True,
    )

    senha_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)


class Paciente(db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    cpf = db.Column(
        db.String(11),
        unique=True,
        nullable=False,
        index=True,
    )

    telefone = db.Column(
        db.String(20),
        nullable=True,
    )

    email = db.Column(
        db.String(150),
        nullable=True,
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    agendamentos = db.relationship(
        "Agendamento",
        back_populates="paciente",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone or "",
            "email": self.email or "",
        }


class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    id = db.Column(db.Integer, primary_key=True)

    data = db.Column(
        db.Date,
        nullable=False,
        index=True,
    )

    horario = db.Column(
        db.Time,
        nullable=False,
    )

    medico = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    especialidade = db.Column(
        db.String(120),
        nullable=False,
    )

    convenio = db.Column(
        db.String(120),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Agendado",
    )

    paciente_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "pacientes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    atualizado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="agendamentos",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "data": self.data.strftime("%d/%m/%Y"),
            "data_iso": self.data.isoformat(),
            "hora": self.horario.strftime("%H:%M"),
            "paciente_id": self.paciente_id,
            "paciente": self.paciente.nome,
            "cpf": self.paciente.cpf,
            "medico": self.medico,
            "especialidade": self.especialidade,
            "convenio": self.convenio,
            "status": self.status,
        }