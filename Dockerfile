FROM python:3.11-slim

WORKDIR /app

# Instala dependências de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos do projeto (exceto .env - veja .dockerignore)
COPY pyproject.toml .
COPY report_writer_app.py .
COPY main.py .
COPY README.md .

# Instala dependências Python
RUN python -m pip install --upgrade pip
RUN pip install google-genai>=1.49.0 streamlit>=1.51.0 python-dotenv>=1.0.0 reportlab>=4.0.0 markdown2>=2.4.0

# Expõe a porta do Streamlit
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["streamlit", "run", "report_writer_app.py", "--server.port", "5000", "--server.address", "0.0.0.0", "--server.headless", "true"]