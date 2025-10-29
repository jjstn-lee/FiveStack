# parent image
FROM python:3.11-slim

WORKDIR /app

# install system dependencies required to compile Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# install dependencies from requirements.txt (COPY will leverage dockerfile cache)
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of the application code to the container; .venv is ignored
COPY main.py .

# Command to run your bot
CMD ["python", "bot.py"]
