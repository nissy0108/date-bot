FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY app ./app
COPY docs/date_bot_preferences_summary.md ./docs/date_bot_preferences_summary.md

EXPOSE 7860

# HF Spaces: PORT unset → 7860. Render etc.: set PORT in the environment.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
