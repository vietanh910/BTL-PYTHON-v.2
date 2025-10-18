FROM python:3.10-slim
WORKDIR /app

# System deps (sqlite for DB CLI if needed)
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

EXPOSE 5000
CMD ["python", "app.py"]
