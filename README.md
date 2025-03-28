# DeezChess-API ♟️

This is a lightweight and deployable FastAPI backend — designed to power chess-related features, like board state analysis, move generation, and more (coming soon).

---

## 🚀 Getting Started

Follow these steps to get this API running locally.

### 1. Clone the repository

```bash
git clone https://github.com/your-username/DeezChess-API.git
cd DeezChess-API
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux

```bash
source venv/bin/activate
```

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

### 💡 Run the FastAPI server (development mode)

```bash
uvicorn app.main:app --reload
```

The API will start at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
Swagger UI (interactive API docs): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
