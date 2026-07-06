FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/app/.local/bin:${PATH}"

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY devtrack_ai_api ./devtrack_ai_api
COPY devtrack_ai_ai ./devtrack_ai_ai
COPY devtrack_ai_auth ./devtrack_ai_auth
COPY devtrack_ai_dashboard ./devtrack_ai_dashboard
COPY devtrack_ai_db ./devtrack_ai_db
COPY devtrack_ai_integrations ./devtrack_ai_integrations
COPY devtrack_ai_kanban ./devtrack_ai_kanban
COPY devtrack_ai_projects ./devtrack_ai_projects
COPY devtrack_ai_tasks ./devtrack_ai_tasks
COPY devtrack_ai_workspace ./devtrack_ai_workspace

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3).read()"

CMD ["uvicorn", "devtrack_ai_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
