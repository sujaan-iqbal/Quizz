FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies (only if needed for PDF libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Final stage ----------
FROM python:3.13-slim

# Create non‑root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Copy only installed packages and app code
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Switch to non‑root user
USER app

# Use gunicorn (production WSGI)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]