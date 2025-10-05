# Base image
FROM python:3.11-slim

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for Chrome
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation libnss3 libxss1 libasound2 libatk1.0-0 libgtk-3-0 libdrm2 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome’s official GPG key and repo
RUN mkdir -p /usr/share/man/man1 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-signing-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
ENV PORT=10000
EXPOSE 10000

# Run app with gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app
