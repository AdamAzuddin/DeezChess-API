# 1. Use official slim Python image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install required system packages (curl + tar)
RUN apt-get update && apt-get install -y curl tar && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Download and install Stockfish Linux binary (from GitHub tar)
RUN curl -L https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar -o stockfish.tar && \
    tar -xf stockfish.tar && \
    rm stockfish.tar && \
    mv stockfish-ubuntu-x86-64-avx2/stockfish/stockfish-ubuntu-x86-64-avx2 stockfish && \
    rm -rf stockfish-ubuntu-x86-64-avx2 && \
    mv stockfish /usr/local/bin/stockfish && \
    chmod +x /usr/local/bin/stockfish

# 6. Copy all your project files
COPY . .

# 7. Expose port
EXPOSE 8000

# 8. Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
