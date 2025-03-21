from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import chess
import chess.polyglot
import os
import tempfile
import random

router = APIRouter()

@router.post("/find_opening_move")
async def find_opening_move(file: UploadFile = File(...), fen: str = Form(...)):
    try:
        # Save uploaded .bin file temporarily
        tmpdir = tempfile.mkdtemp()
        book_path = os.path.join(tmpdir, file.filename)
        with open(book_path, "wb") as f:
            f.write(await file.read())

        # Parse FEN
        try:
            board = chess.Board(fen)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")

        # Read from Polyglot book
        try:
            with chess.polyglot.open_reader(book_path) as reader:
                entries = list(reader.find_all(board))
                print(f"Looking up FEN={fen}, ZobristKey={chess.polyglot.zobrist_hash(board)}")
                if entries:
                    move = random.choice(entries).move
                    return {"uci_move": move.uci()}
                else:
                    return {"uci_move": ""}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading opening book: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
