FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

CMD ["uv", "run", "python", "-m", "duplex_voice.main"]

