FROM python:3.12-slim

ARG APP_DIR

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace

WORKDIR /workspace

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl ffmpeg \
  && rm -rf /var/lib/apt/lists/*

COPY ${APP_DIR}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /workspace
WORKDIR /workspace/${APP_DIR}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
