# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Preinstall CPU-only PyTorch to avoid pulling CUDA wheels on amd64,
# then install the rest of the requirements normally (so their dependencies like 'click' are present)
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch==2.9.1+cpu \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories (static already exists from COPY)
RUN mkdir -p uploads processed

# Expose port
EXPOSE 8000

# Set environment variables (can be overridden)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

