from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import chess
import chess.polyglot
import os
import platform
import tempfile
import random
import json
import asyncio

router = APIRouter()

def get_stockfish_path():
    base_path = os.path.dirname(os.path.dirname(__file__))
    if platform.system() == "Windows":
        return os.path.join(base_path, "stockfish.exe")
    else:
        return "/usr/local/bin/stockfish"
    
async def getMoveFromStockfish(fen: str, estimated_elo: int, contempt_score: int) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            get_stockfish_path(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def communicate(command: str):
            process.stdin.write((command + "\n").encode())
            await process.stdin.drain()

        await communicate("uci")
        await asyncio.sleep(0.1)

        await communicate("setoption name UCI_LimitStrength value true")
        await communicate(f"setoption name UCI_Elo value {estimated_elo}")
        await communicate(f"setoption name Contempt value {contempt_score}")

        await communicate("isready")
        await asyncio.sleep(0.1)

        await communicate(f"position fen {fen}")
        await communicate("go depth 15")

        best_move = None
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded = line.decode().strip()
            if decoded.startswith("bestmove"):
                best_move = decoded.split()[1]
                break

        process.kill()
        return best_move if best_move else "0000"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stockfish error: {str(e)}")


@router.post("/get_bot_move")
async def get_bot_move(
    bin_file: UploadFile = File(...),
    config_file: UploadFile = File(...),
    fen: str = Form(...)
):
    print("Finding move for fen "+fen)
    try:
        estimated_elo = 1200
        contempt_score = 20

        tmpdir = tempfile.mkdtemp()

        book_path = os.path.join(tmpdir, bin_file.filename)
        with open(book_path, "wb") as f:
            f.write(await bin_file.read())

        config_path = os.path.join(tmpdir, config_file.filename)
        with open(config_path, "wb") as cf:
            cf.write(await config_file.read())

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                estimated_elo = int(config.get("estimated_elo", estimated_elo))
                contempt_score = int(round(config.get("estimated_contempt_score", contempt_score)))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid config JSON: {str(e)}")

        try:
            board = chess.Board(fen)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")

        try:
            with chess.polyglot.open_reader(book_path) as reader:
                entries = list(reader.find_all(board))
                if entries:
                    move = random.choice(entries).move
                    return {"uci_move": move.uci()}
        except Exception as e:
            # Log the error but don't crash — fallback to Stockfish
            print(f"Opening book error: {e}")

        # If no move from book OR book read failed, fallback to Stockfish
        bestMove = await getMoveFromStockfish(fen, estimated_elo=estimated_elo, contempt_score=contempt_score)
        return {"uci_move": bestMove}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
