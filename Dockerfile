# ──────────────────────────────────────────────
#  Dockerfile  —  Drop-in replacement for Koyeb
#  Adds: health check, proper port binding,
#        psutil for /status page.
#  Does NOT change any main bot code.
# ──────────────────────────────────────────────

FROM python:3.11-slim

# System deps (ffmpeg for media, curl for health probe)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psutil aiohttp

# Copy source
COPY . .

# Expose the web server port
EXPOSE 8080

# ── Koyeb Health Check ─────────────────────────────────────────────
# Koyeb will call /health every 30s.
# If it fails 3 times, Koyeb restarts the container automatically.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the bot
CMD ["python3", "-m", "Adarsh"]
