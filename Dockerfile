FROM python:3.9-slim-buster

EXPOSE 8080
WORKDIR /app

COPY app.py ./
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port that Streamlit will run on.
# Cloud Run expects applications to listen on port 8080 by default.
EXPOSE 8080

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]