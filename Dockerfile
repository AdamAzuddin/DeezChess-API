# 1. Use official Python image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy entire project code
COPY . .

# 5. Ensure Linux stockfish binary is executable
RUN chmod +x /app/stockfish

# 6. Expose port
EXPOSE 8000

# 7. Command to run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
