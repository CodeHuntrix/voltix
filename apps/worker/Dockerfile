FROM python:3.12-slim
WORKDIR /work
COPY apps/api /work/api
COPY apps/worker/worker.py /work/worker.py
RUN pip install --no-cache-dir /work/api arq redis
ENV PYTHONPATH=/work/api
WORKDIR /work
CMD ["arq", "worker.WorkerSettings"]
