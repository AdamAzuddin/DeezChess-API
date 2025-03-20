import os
import tempfile
import chess.pgn
import chess.polyglot
from tqdm import tqdm
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

# Create polyglot opening book
def create_player_opening_book(pgn_file, output_book, max_moves=10):
    #player_name = os.path.splitext(os.path.basename(pgn_file))[0]
    player_name = "Adam05"
    book_data = {}
    entries = []
    pbar = tqdm(desc="Creating opening book: ", unit="moves")

    with open(pgn_file, "r") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            is_white = game.headers.get("White") == player_name
            is_black = game.headers.get("Black") == player_name
            if not is_white and not is_black:
                continue

            board = game.board()
            move_count = 0

            for move in game.mainline_moves():
                move_count += 1
                if move_count > max_moves:
                    break

                if (is_white and board.turn) or (is_black and not board.turn):
                    fen = board.fen()

                    if fen not in book_data:
                        book_data[fen] = {}

                    uci_move = move.uci()
                    if uci_move not in book_data[fen]:
                        book_data[fen][uci_move] = 0
                    book_data[fen][uci_move] += 1

                board.push(move)
                pbar.update(1)

    for fen, moves in book_data.items():
        for move, weight in moves.items():
            entry = chess.polyglot.Entry(
                key=chess.polyglot.zobrist_hash(chess.Board(fen)),
                raw_move=0,
                weight=weight,
                learn=0,
                move=chess.Move.from_uci(move),
            )
            entries.append(entry)

    entries.sort(key=lambda entry: entry.key)

    with open(output_book, "wb") as book:
        for entry in entries:
            book.write(entry.key.to_bytes(8, "big"))
            book.write(entry.raw_move.to_bytes(2, "big"))
            book.write(entry.weight.to_bytes(2, "big"))
            book.write(entry.learn.to_bytes(4, "big"))

    pbar.close()
    print(f"Polyglot book created: {output_book}")

@router.post("/pgn_upload")
async def upload_pgn(file: UploadFile = File(...)):
    try:
        tmpdir = tempfile.mkdtemp()
        pgn_path = os.path.join(tmpdir, file.filename)
        with open(pgn_path, "wb") as f:
            f.write(await file.read())

        #book_output_path = os.path.join(tmpdir, f"{os.path.splitext(file.filename)[0]}.bin")
        book_output_path = os.path.join(tmpdir, "Adam05.bin")
        create_player_opening_book(pgn_path, book_output_path)

        # Open file in binary mode and stream it
        bin_file = open(book_output_path, "rb")
        return StreamingResponse(
            bin_file,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={os.path.basename(book_output_path)}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
