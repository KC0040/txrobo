FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors anthropic requests

COPY server.py .
COPY assets/ ./assets/
COPY lang/ ./lang/
COPY data/ ./data/

COPY index.html .
COPY about.html .
COPY products.html .
COPY solutions.html .
COPY contact.html .
COPY blog.html .
COPY services.html .

EXPOSE 5000

CMD ["python", "server.py"]
