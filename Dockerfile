# Use an official Python 3.9 image as the base
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Install necessary system packages
RUN apt-get update && \
    apt-get install -y \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Command to run when the container starts
CMD ["python", "./client.py"]
