# Base image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy source files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the main script
CMD ["python", "main.py"]
