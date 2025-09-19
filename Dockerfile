FROM python:3.12-slim
WORKDIR /app
COPY client.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ENV OFFSHORE_HOST=host.docker.internal
ENV OFFSHORE_PORT=9999
EXPOSE 8080
CMD ["python", "client.py"]
