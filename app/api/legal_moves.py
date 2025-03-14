from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import chess
from app.utils.chess_utils import uci_move_to_bitboard_indices

router = APIRouter()

class FenInput(BaseModel):
    fen: str

@router.post("/legal_moves")
def get_legal_moves(input_data: FenInput):
    fen = input_data.fen

    try:
        board = chess.Board(fen)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid FEN: {str(e)}")

    legal_moves = list(board.legal_moves)
    bitboard_indices = [uci_move_to_bitboard_indices(move.uci()) for move in legal_moves]

    return {"legal_moves_bitboard": bitboard_indices}
