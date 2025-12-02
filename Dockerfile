# ============================================================
# Outlaw Legal AI — FastAPI + ReportLab container (Python 3.12)
# ============================================================

# 1️⃣ Use the latest stable Python 3.12 image
FROM python:3.12-slim

# 2️⃣ Set working directory
WORKDIR /app

# 3️⃣ Copy dependency list
COPY requirements.txt .

# 4️⃣ Install system dependencies for ReportLab and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev libjpeg-dev libpng-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 5️⃣ Copy the application code
COPY . .

# 6️⃣ Expose the FastAPI port
EXPOSE 8000

# 7️⃣ Default command — run the API using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
