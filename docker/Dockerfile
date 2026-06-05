FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Inject homoglyph into utils/auth.py — Trap 42
# Runs in build layer so the injected bytes are baked into the image.
# entrypoint.sh verifies presence at runtime but does not re-inject.
RUN python3 tools/inject_homoglyph.py

# Initialize database with all seed data including adversarial entries
RUN python3 db_setup.py

# Verify all traps intact before image is finalized
RUN python3 tools/verify_traps.py

EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_APP=app.py

ENTRYPOINT ["./docker/entrypoint.sh"]
