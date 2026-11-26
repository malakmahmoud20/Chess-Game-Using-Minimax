import tkinter as tk
from tkinter import messagebox
import chess


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

PIECE_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}


def evaluate_board(board: chess.Board) -> int:
    """Evaluate board position from White's (MAX) perspective."""
    if board.is_checkmate():
        return -999999 if board.turn == chess.WHITE else 999999
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece:
            score += 25 if piece.color == chess.WHITE else -25

    return score


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
    """Minimax algorithm with Alpha-Beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if is_maximizing:
        max_eval = -10**9
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 10**9
        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def choose_best_move(board: chess.Board, depth: int = 3) -> chess.Move | None:
    """Choose the best move for Black (MIN) using Minimax."""
    best_move = None
    best_value = 10**9

    moves = sorted(
        board.legal_moves,
        key=lambda m: board.is_capture(m),
        reverse=True,
    )

    for move in moves:
        board.push(move)
        move_value = minimax(board, depth - 1, -10**9, 10**9, True)
        board.pop()
        if move_value < best_value:
            best_value = move_value
            best_move = move

    return best_move


class ChessGUI:
    def __init__(self, root: tk.Tk, ai_depth: int = 3):
        self.root = root
        self.root.title("Chess Game - Minimax AI")
        self.ai_depth = ai_depth
        self.board = chess.Board()
        self.selected_square: int | None = None
        self.square_size = 72

        self.light_color = "#F0D9B5"
        self.dark_color = "#B58863"
        self.highlight_color = "#F6F669"
        self.move_hint_color = "#829769"

        self.canvas = tk.Canvas(
            root,
            width=self.square_size * 8,
            height=self.square_size * 8,
        )
        self.canvas.pack(padx=10, pady=10)

        self.status_label = tk.Label(
            root,
            text="Your Turn (White) - Select a piece to move",
            font=("Arial", 13, "bold"),
        )
        self.status_label.pack(pady=(0, 8))

        self.reset_btn = tk.Button(
            root,
            text="New Game",
            font=("Arial", 11),
            command=self.reset_game,
        )
        self.reset_btn.pack(pady=(0, 10))

        self.canvas.bind("<Button-1>", self.on_square_click)
        self.draw_board()

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.status_label.config(text="Your Turn (White) - Select a piece to move")
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        legal_targets = set()
        if self.selected_square is not None:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    legal_targets.add(move.to_square)

        for row in range(8):
            for col in range(8):
                rank = 7 - row
                file = col
                square = chess.square(file, rank)

                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                if square == self.selected_square:
                    fill = self.highlight_color
                else:
                    fill = self.light_color if (row + col) % 2 == 0 else self.dark_color

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")

                if square in legal_targets:
                    r_offset = self.square_size // 6
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    self.canvas.create_oval(
                        cx - r_offset,
                        cy - r_offset,
                        cx + r_offset,
                        cy + r_offset,
                        fill=self.move_hint_color,
                        outline="",
                    )

                piece = self.board.piece_at(square)
                if piece:
                    symbol = PIECE_SYMBOLS[piece.symbol()]
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=symbol,
                        font=("Arial", 42),
                        fill="#111111",
                    )

    def on_square_click(self, event):
        if self.board.is_game_over() or self.board.turn != chess.WHITE:
            return

        col = event.x // self.square_size
        row = event.y // self.square_size
        if not (0 <= col < 8 and 0 <= row < 8):
            return

        rank = 7 - row
        clicked_square = chess.square(col, rank)

        if self.selected_square is None:
            piece = self.board.piece_at(clicked_square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = clicked_square
                self.draw_board()
        else:
            move = chess.Move(self.selected_square, clicked_square)
            if chess.Move(self.selected_square, clicked_square, promotion=chess.QUEEN) in self.board.legal_moves:
                move = chess.Move(self.selected_square, clicked_square, promotion=chess.QUEEN)

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.draw_board()

                if self.check_game_end():
                    return

                self.status_label.config(text="Computer is thinking...")
                self.root.update_idletasks()
                self.root.after(150, self.computer_turn)
            else:
                piece = self.board.piece_at(clicked_square)
                if piece and piece.color == chess.WHITE:
                    self.selected_square = clicked_square
                else:
                    self.selected_square = None
                self.draw_board()

    def computer_turn(self):
        if self.board.is_game_over() or self.board.turn != chess.BLACK:
            return

        ai_move = choose_best_move(self.board, depth=self.ai_depth)
        if ai_move:
            self.board.push(ai_move)

        self.draw_board()
        if not self.check_game_end():
            if self.board.is_check():
                self.status_label.config(text="Check! Your Turn (White)")
            else:
                self.status_label.config(text="Your Turn (White) - Select a piece to move")

    def check_game_end(self) -> bool:
        if not self.board.is_game_over():
            return False

        if self.board.is_checkmate():
            winner = "Computer (Black)" if self.board.turn == chess.WHITE else "You (White)"
            msg = f"Checkmate! Winner: {winner}"
        elif self.board.is_stalemate():
            msg = "Game over: Stalemate."
        elif self.board.is_insufficient_material():
            msg = "Game over: Draw due to insufficient material."
        else:
            msg = "Game over: Draw."

        self.status_label.config(text=msg)
        messagebox.showinfo("Game Over", msg)
        return True


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root, ai_depth=3)
    root.mainloop()