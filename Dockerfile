# Use official Python slim image
FROM python:3.10-slim

# Install system dependencies for Chrome & Selenium
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary paths for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && python -m spacy download en_core_web_sm

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1
ARG PORT=5000
EXPOSE ${PORT}

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}", "--timeout", "360"]

