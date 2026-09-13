FROM python:3.10-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application package, configuration, and documentation
COPY ip_sakti/ ./ip_sakti/
COPY config/ ./config/
COPY README.md .

# Copy data and indexes if available in build context
COPY data* ./data/
COPY indexes* ./indexes/

EXPOSE 7860

CMD ["uvicorn", "ip_sakti.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
