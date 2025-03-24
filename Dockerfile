# 1. Use official slim Python image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install required system packages (for curl & unzip)
RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Download and install Stockfish Linux binary
RUN curl -L https://stockfishchess.org/files/stockfish_15_linux_x64_avx2.zip -o stockfish.zip && \
    unzip stockfish.zip && \
    mv stockfish_15_x64_avx2 /usr/local/bin/stockfish && \
    chmod +x /usr/local/bin/stockfish && \
    rm stockfish.zip

# 6. Copy all your source code
COPY . .

# 7. Expose port
EXPOSE 8000

# 8. Start FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
