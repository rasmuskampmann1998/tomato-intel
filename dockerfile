# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Chrome and Selenium
RUN apt-get update \
    && apt-get install -y \
        gcc \
        libpq-dev \
        curl \
        wget \
        unzip \
        libnss3 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libxss1 \
        libasound2 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdrm2 \
        libxinerama1 \
        fonts-liberation \
        libappindicator3-1 \
        lsb-release \
        xdg-utils \
        --no-install-recommends \
    && wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose FastAPI port
EXPOSE 8004

# Run the app
CMD ["python", "main.py"]
