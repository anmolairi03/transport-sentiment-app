FROM python:3.11-slim

# Install dependencies for lxml and MySQL
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy all files including .env
COPY . .

# Install Python packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Start app
CMD ["python", "backend/api.py"]
