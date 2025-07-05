FROM python:3.10-slim
WORKDIR /app

COPY . .

RUN pip install flask kafka-python pandas

CMD ["python", "consumer.py"]