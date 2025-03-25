import os
import json
import tempfile
import zipfile
import chess.pgn
import chess.polyglot
from tqdm import tqdm
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


def encode_move(move: chess.Move) -> int:
    """Polyglot move encoding as 16-bit integer."""
    from_sq = move.from_square
    to_sq = move.to_square
    promo = move.promotion

    # Polyglot promotion: 1=knight, 2=bishop, 3=rook, 4=queen
    promotion_map = {
        chess.KNIGHT: 1,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 4,
    }
    promotion = promotion_map.get(promo, 0)

    return (from_sq << 6) | to_sq | (promotion << 12)


# Create polyglot opening book
def process_pgn(pgn_file, output_book, config_file_path, player_name, max_moves=10):
    book_data = {}
    entries = []
    pbar = tqdm(desc="Creating opening book: ", unit="moves")

    total_elo = 0
    game_count = 0
    wins = 0
    draws = 0
    losses = 0

    with open(pgn_file, "r", encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            is_white = game.headers.get("White") == player_name
            is_black = game.headers.get("Black") == player_name
            if not is_white and not is_black:
                continue

            game_count += 1

            try:
                total_elo += int(
                    game.headers.get("WhiteElo" if is_white else "BlackElo", 1200)
                )
            except ValueError:
                total_elo += 1200

            result = game.headers.get("Result", "*")
            if (is_white and result == "1-0") or (is_black and result == "0-1"):
                wins += 1
            elif result == "1/2-1/2":
                draws += 1
            elif (is_white and result == "0-1") or (is_black and result == "1-0"):
                losses += 1

            board = game.board()
            move_count = 0

            for move in game.mainline_moves():
                move_count += 1
                if move_count > max_moves:
                    break

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
        for move_uci, weight in moves.items():
            try:
                board = chess.Board()
                board.set_fen(fen)
                move = board.parse_uci(move_uci)
                encoded_move = encode_move(move=move)
                entry = chess.polyglot.Entry(
                    key=chess.polyglot.zobrist_hash(board),
                    raw_move=encoded_move,
                    weight=weight,
                    learn=0,
                    move=move,
                )
                entries.append(entry)
            except Exception as e:
                print(f"Skipping entry: FEN={fen}, Move={move_uci}, Error={e}")

    entries.sort(key=lambda entry: entry.key)

    try:
        with open(output_book, "wb") as book:
            for entry in entries:
                book.write(entry.key.to_bytes(8, "big"))
                book.write(entry.raw_move.to_bytes(2, "big"))
                book.write(entry.weight.to_bytes(2, "big"))
                book.write(entry.learn.to_bytes(4, "big"))
    except Exception as e:
        print(f"Failed writing book: {e}")
        raise

    avg_elo = total_elo // game_count if game_count > 0 else 1200
    estimated_elo = ((avg_elo + 50) // 100) * 100 + 200

    total_games = wins + draws + losses
    contempt_score = 0
    if total_games > 0:
        contempt_score = round(((wins - losses) / total_games) * 100, 2)

    config = {
        "player_name": player_name,
        "estimated_elo": estimated_elo,
        "avg_elo_from_pgn": avg_elo,
        "games_played": total_games,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "estimated_contempt_score": contempt_score,
    }

    with open(config_file_path, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)

    pbar.close()
    print(f"Polyglot book created: {output_book}")
    print(f"Config file created: {config_file_path}")


@router.post("/pgn_upload")
async def upload_pgn(file: UploadFile = File(...), playerName: str = Form(...)):
    try:
        tmpdir = tempfile.mkdtemp()
        pgn_path = os.path.join(tmpdir, file.filename)
        with open(pgn_path, "wb") as f:
            f.write(await file.read())

        safe_player_name = playerName.replace(" ", "_").replace(",", "")
        book_output_path = os.path.join(tmpdir, f"{safe_player_name}.bin")
        config_output_path = os.path.join(tmpdir, f"{safe_player_name}.json")

        # Process PGN file and generate book & config
        process_pgn(
            pgn_path, book_output_path, config_output_path, player_name=playerName
        )

        # Create ZIP file
        zip_path = os.path.join(tmpdir, f"{safe_player_name}_output.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(book_output_path, arcname=os.path.basename(book_output_path))
            zipf.write(config_output_path, arcname=os.path.basename(config_output_path))

        # Stream ZIP file as response
        zip_file = open(zip_path, "rb")
        return StreamingResponse(
            zip_file,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(zip_path)}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
