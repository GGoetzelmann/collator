# app/Dockerfile
FROM eclipse-temurin:8-jdk
WORKDIR /app
RUN apt-get update && apt-get install -y curl git python3.12 python3-pip
COPY . .
RUN pip3 install -r requirements.streamlit.txt --break-system-packages
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "streamlit_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]