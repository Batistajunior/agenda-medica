# ============================================================
# IMAGEM BASE
# ============================================================

FROM python:3.13-slim


# ============================================================
# CONFIGURAÇÕES DO PYTHON
# ============================================================

# Evita a criação de arquivos .pyc.
ENV PYTHONDONTWRITEBYTECODE=1

# Faz o Python enviar os logs imediatamente para o terminal.
ENV PYTHONUNBUFFERED=1

# Porta utilizada pela aplicação.
ENV PORT=8000


# ============================================================
# DIRETÓRIO DE TRABALHO
# ============================================================

WORKDIR /app


# ============================================================
# DEPENDÊNCIAS DO SISTEMA
# ============================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# DEPENDÊNCIAS PYTHON
# ============================================================

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --upgrade pip \
    && pip install \
    --no-cache-dir \
    -r requirements.txt


# ============================================================
# CÓDIGO DA APLICAÇÃO
# ============================================================

COPY . .


# ============================================================
# DIRETÓRIO DO BANCO SQLITE
# ============================================================

RUN mkdir -p /app/instance


# ============================================================
# PORTA
# ============================================================

EXPOSE 8000


# ============================================================
# INICIALIZAÇÃO
# ============================================================

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "app.main:app"]