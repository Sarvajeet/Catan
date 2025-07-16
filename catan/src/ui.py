import tkinter as tk
from tkinter import messagebox
from catan.src.game import Game

class CatanUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Catan")

        self.game = Game(player_names=["Player 1", "Player 2", "Player 3"])

        self.canvas = tk.Canvas(master, width=800, height=600, bg='lightblue')
        self.canvas.pack()

        self.draw_board()

        self.roll_button = tk.Button(master, text="Roll Dice", command=self.roll_dice)
        self.roll_button.pack()

    def draw_board(self):
        # This is a simplified representation of the board.
        # We will improve this later.
        x, y = 100, 100
        for i, tile in enumerate(self.game.board.tiles):
            self.canvas.create_oval(x, y, x + 50, y + 50, fill=self.get_tile_color(tile.resource))
            self.canvas.create_text(x + 25, y + 25, text=f"{tile.number}\n{tile.resource.name if tile.resource else 'Desert'}")
            x += 60
            if (i + 1) % 5 == 0:
                y += 60
                x = 100

    def get_tile_color(self, resource):
        if resource is None:
            return "beige"
        return {
            "lumber": "forestgreen",
            "wool": "lightgray",
            "grain": "gold",
            "brick": "firebrick",
            "ore": "darkgray"
        }.get(resource.value, "white")

    def roll_dice(self):
        roll = self.game.roll_dice()
        messagebox.showinfo("Dice Roll", f"You rolled a {roll}")
        # We need to update the UI to show resource distribution.
        # This will be implemented later.

if __name__ == "__main__":
    root = tk.Tk()
    app = CatanUI(root)
    root.mainloop()
