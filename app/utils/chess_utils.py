def uci_square_to_bitboard_index(square: str) -> int:
    if len(square) != 2:
        return -1

    file = square[0]
    rank = square[1]

    file_index = ord(file) - ord('a')
    rank_index = int(rank) - 1

    return rank_index * 8 + file_index


def uci_move_to_bitboard_indices(uci_move: str) -> tuple[int, int]:
    if len(uci_move) not in [4, 5]:
        return -1, -1

    move_copy = uci_move[:4]  # e.g., e7e8q → e7e8

    from_square = move_copy[:2]
    to_square = move_copy[2:]

    from_index = uci_square_to_bitboard_index(from_square)
    to_index = uci_square_to_bitboard_index(to_square)

    return from_index, to_index
