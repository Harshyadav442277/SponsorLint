FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-demo.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY sponsorlint ./sponsorlint
COPY samples ./samples
COPY THIRD_PARTY_NOTICES.md ./

RUN adduser --disabled-password --gecos "" --uid 10001 sponsorlint \
    && mkdir -p /app/uploads \
    && chown -R sponsorlint:sponsorlint /app/uploads

USER sponsorlint

EXPOSE 10000

CMD ["uvicorn", "sponsorlint.web.app:app", "--host", "0.0.0.0", "--port", "10000", "--no-server-header"]
