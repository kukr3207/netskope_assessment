FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Expose both FastAPI and Streamlit
CMD ["bash", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & python -m streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
