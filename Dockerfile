FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot file
COPY study.py .

# Run the bot
CMD ["python", "study.py"]
