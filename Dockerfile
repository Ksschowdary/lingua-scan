FROM python:3.10-slim

# Install system dependencies for Tesseract OCR & OpenCV support
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt-get/lists/*

WORKDIR /app

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

EXPOSE 10000

# Start Uvicorn app server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]