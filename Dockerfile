# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies (removed tesseract-ocr - not used)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (no PyTorch needed - using OpenAI API only)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories (static already exists from COPY)
RUN mkdir -p uploads processed

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Set environment variables (can be overridden)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Run the application
# Use ENTRYPOINT for explicit execution (overrides any cached Railway config)
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

