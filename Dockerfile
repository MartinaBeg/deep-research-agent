FROM python:3.11-slim

# A Unicode font so PDFs render nicely (DejaVu); optional but recommended.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

# Reports are written under /app/reports — mount a volume there to keep them.
ENTRYPOINT ["deep-research"]
