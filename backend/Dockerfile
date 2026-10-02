FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

# Build tools only for the pip step; the runtime image keeps libpq.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --use-deprecated=legacy-resolver --no-cache-dir -r requirements.txt

COPY . .

# Uploaded files live on a volume mounted at /home/media; the app runs unprivileged.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /home/media /home/static \
    && chown -R app:app /home/media /home/static /usr/src/app \
    && chmod +x /usr/src/app/docker-entrypoint.sh
USER app

EXPOSE 8000
ENTRYPOINT ["sh", "/usr/src/app/docker-entrypoint.sh"]
