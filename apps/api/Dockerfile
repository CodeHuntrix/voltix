FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir .
COPY apps/api/app /app/app
COPY voltix-pulse/src /pulse/src
COPY voltix-pulse/models/pulse /pulse/models/pulse
COPY voltix-condition/src /condition/src
COPY voltix-condition/models/drift /condition/models/drift
ENV PYTHONPATH=/pulse:/condition
ENV VOLTIX_MODELS_DIR=/pulse/models/pulse
ENV VOLTIX_CONDITION_MODELS_DIR=/condition/models/drift
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

COPY apps/api/docker-entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
