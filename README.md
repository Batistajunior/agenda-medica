# 🏥 Agenda Médica

Sistema web desenvolvido com **Python e Flask** para gerenciamento de pacientes, consultas médicas e agenda clínica.

O projeto conta com autenticação, dashboard, API, exportação de relatórios, SQLite e execução conteinerizada com Docker.

---

## ✨ Funcionalidades

### 🔐 Autenticação

- Login e logout
- Proteção de rotas
- Controle de sessão
- Usuário administrador para demonstração

### 👥 Pacientes

- Cadastro de pacientes
- Edição de dados
- Exclusão
- Pesquisa
- Listagem completa

### 📅 Agendamentos

- Cadastro de consultas
- Edição
- Exclusão
- Visualização dos detalhes
- Pesquisa
- Filtro por período
- Filtro por status
- Visualização em calendário

### 📊 Dashboard

- Consultas do dia
- Consultas agendadas
- Consultas confirmadas
- Consultas canceladas
- Indicadores gerais da agenda

### 📄 Exportação

- Exportação de agendamentos para Excel
- Exportação de agendamentos para PDF

### 🔌 API

Endpoint para consulta dos agendamentos:

```http
GET /api/agenda
```

Os dados são retornados em formato JSON.

### ❤️ Health Check

Endpoint para verificar a disponibilidade da aplicação e do banco de dados:

```http
GET /health
```

Exemplo de resposta:

```json
{
  "database": "ok",
  "status": "ok"
}
```

---

## 🚀 Tecnologias

### Backend

- Python 3.13
- Flask
- Flask-SQLAlchemy
- SQLite
- Gunicorn
- Python Dotenv

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Bootstrap Icons
- Jinja2

### Relatórios

- OpenPyXL
- ReportLab

### DevOps

- Docker
- Docker Compose

### Testes

- Pytest

---

## 📁 Estrutura do projeto

```text
agenda-medica/
│
├── app/
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   │
│   ├── routes/
│   │   ├── agenda.py
│   │   ├── auth.py
│   │   └── pacientes.py
│   │
│   ├── services/
│   │   ├── api_service.py
│   │   ├── auth_service.py
│   │   └── exportacao.py
│   │
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   │
│   ├── templates/
│   │   ├── agenda/
│   │   ├── pacientes/
│   │   ├── base.html
│   │   ├── error.html
│   │   └── login.html
│   │
│   ├── utils/
│   ├── __init__.py
│   ├── main.py
│   └── seed.py
│
├── config/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚙️ Executando localmente

### 1. Clone o repositório

```bash
git clone https://github.com/Batistajunior/agenda-medica.git
```

### 2. Entre na pasta

```bash
cd agenda-medica
```

### 3. Crie o ambiente virtual

No Windows:

```powershell
python -m venv .venv
```

No Linux:

```bash
python3 -m venv .venv
```

### 4. Ative o ambiente virtual

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

No Linux:

```bash
source .venv/bin/activate
```

### 5. Instale as dependências

```bash
pip install -r requirements.txt
```

### 6. Configure o banco de dados

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=agenda-medica-chave-local
DATABASE_URL=sqlite:///C:/Users/junio/Downloads/agenda-medica/instance/agenda_medica.db
PORT=8000
FLASK_DEBUG=1
COOKIE_SECURE=0
```

### 7. Execute a aplicação

```bash
python -m app.main
```

Acesse:

```text
http://localhost:8000
```

---

## 🐳 Executando com Docker

A forma recomendada de executar o projeto é utilizando Docker Compose.

### Construir e iniciar os contêineres

```bash
docker compose up --build
```

Para executar em segundo plano:

```bash
docker compose up --build -d
```

### Verificar os contêineres

```bash
docker compose ps
```

### Visualizar os logs

```bash
docker compose logs -f web
```

### Parar os contêineres

```bash
docker compose down
```

A aplicação estará disponível em:

```text
http://localhost:8000
```

---

## 🔑 Usuário de demonstração

```text
Usuário: admin
Senha: 123456
```

> As credenciais são destinadas apenas ao ambiente de demonstração.

---

## 🧪 Testes automatizados

Execute os testes com:

```bash
pytest
```

Para exibir informações detalhadas:

```bash
pytest -v
```

---

## 🔧 Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave utilizada para proteger a sessão |
| `DATABASE_URL` | String de conexão com o banco |
| `PORT` | Porta da aplicação |
| `FLASK_DEBUG` | Ativa ou desativa o modo de desenvolvimento |
| `COOKIE_SECURE` | Controla o uso de cookies somente via HTTPS |

---

## 🗺️ Roadmap

- Autenticação por perfis: Administrador, Médico e Recepção
- API REST completa
- Documentação Swagger/OpenAPI
- Ampliação da cobertura de testes
- Upload de documentos
- Histórico médico
- Prontuário eletrônico
- Notificações por e-mail
- Integração com Google Calendar
- CI/CD com GitHub Actions
- Deploy em Render ou Railway

---

## 👨‍💻 Autor

**Antonio Carlos Batista Junior**

Engenheiro de Dados | Python Developer | Data Engineer | BI Developer

- GitHub: [Batistajunior](https://github.com/Batistajunior)
- LinkedIn: [Antonio Carlos Batista Junior](https://www.linkedin.com/in/antonio-carlos-a5367494/)

---

## 📄 Licença

Projeto desenvolvido para fins de estudo, portfólio e demonstração técnica.
