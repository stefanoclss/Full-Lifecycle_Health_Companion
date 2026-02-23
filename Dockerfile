# Use official Python 3.10 runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Disable demo mode by default in production, but configurable
ENV DEMO_MODE False

# Install system dependencies required for building some python packages and audio
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# Using cpu index for torch to keep image size reasonable, unless GPU is explicitly targeted
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application (assuming gunicorn + uvicorn for production)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "server:app", "--bind", "0.0.0.0:8000"]
