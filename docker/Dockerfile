FROM python:3.11-slim

# System deps for Playwright/Crawl4AI's Chromium browser
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (no dev deps in prod)
COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./
COPY scout/ scout/
COPY website/ website/
COPY docs/product/ docs/product/
COPY docs/legal/ docs/legal/
COPY docs/security/ docs/security/
RUN pip install --no-cache-dir .

# Install Playwright and Chromium browser, then Crawl4AI browser setup
RUN playwright install chromium \
    && python -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI ready')"

# Persistent data volume
VOLUME /data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SCOUT_WORKDIR=/data/runs \
    DB_PATH=/data/scout.db

EXPOSE 8421

CMD ["uvicorn", "scout.api.main:app", "--host", "0.0.0.0", "--port", "8421"]
