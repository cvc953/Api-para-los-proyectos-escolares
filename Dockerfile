FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal packages required (netcat for health/wait loop) and build deps
# We install temporarily build tools needed by some Python wheels (cryptography)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       netcat \
       build-essential \
       libssl-dev \
       libffi-dev \
       python3-dev \
       cargo \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cache layer)
COPY requirements.txt /app/requirements.txt
# Install Python deps (cryptography may be installed from wheel; cargo is present in case a build is required)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Remove build-time packages to reduce image size
RUN apt-get purge -y --auto-remove build-essential cargo python3-dev \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

# Copy application code
COPY . /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser || true \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]


