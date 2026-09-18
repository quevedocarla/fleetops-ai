FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# O requirements.txt foi gerado no Windows.
# PowerShell pode gravá-lo em UTF-16, que o Linux interpreta como binário.
# Aqui normalizamos para UTF-8 e removemos somente pywin32,
# que é uma dependência exclusiva do Windows.
RUN python -c "from pathlib import Path; \
p=Path('requirements.txt'); \
raw=p.read_bytes(); \
text=(raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')); \
lines=[line for line in text.splitlines() if line.strip() and not line.lower().startswith('pywin32')]; \
Path('requirements-docker.txt').write_text('\n'.join(lines)+'\n', encoding='utf-8')" \
    && pip install --no-cache-dir -r requirements-docker.txt \
    && pip install --no-cache-dir "uvicorn[standard]"

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
