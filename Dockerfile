# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run from Backend so relative paths (models/, users.json) work
WORKDIR /app/Backend

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]