FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY agents/pyproject.toml agents/
RUN pip install -e agents/

# Install Playwright browsers
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "-m", "agents", "run"]
