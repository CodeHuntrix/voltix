FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app
COPY apps/simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/simulator/simulate.py .
CMD ["python", "simulate.py"]
