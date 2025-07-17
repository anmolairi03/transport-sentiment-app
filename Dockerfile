# Dockerfile

FROM python:3.11-slim

# Install lxml dependencies
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (if needed)
EXPOSE 5000

# Start the Flask app
CMD ["python", "backend/api.py"]
