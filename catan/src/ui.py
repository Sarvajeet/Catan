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

        self.current_player_label = tk.Label(master, text=f"Current Player: {self.game.current_player.name}")
        self.current_player_label.pack()

        self.roll_button = tk.Button(master, text="Roll Dice", command=self.roll_dice)
        self.roll_button.pack()

        self.next_turn_button = tk.Button(master, text="Next Turn", command=self.next_turn)
        self.next_turn_button.pack()

        self.trade_button = tk.Button(master, text="Trade", command=self.open_trade_window)
        self.trade_button.pack()

        self.build_road_button = tk.Button(master, text="Build Road", command=self.build_road)
        self.build_road_button.pack()

        self.build_settlement_button = tk.Button(master, text="Build Settlement", command=self.build_settlement)
        self.build_settlement_button.pack()

        self.build_city_button = tk.Button(master, text="Build City", command=self.build_city)
        self.build_city_button.pack()

        self.resource_labels = []
        for i, player in enumerate(self.game.players):
            label = tk.Label(master, text=f"{player.name}'s Resources: {player.resources}")
            label.pack()
            self.resource_labels.append(label)

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
        self.update_resource_labels()

    def update_resource_labels(self):
        for i, player in enumerate(self.game.players):
            self.resource_labels[i].config(text=f"{player.name}'s Resources: {player.resources}")

    def next_turn(self):
        self.game.next_turn()
        self.current_player_label.config(text=f"Current Player: {self.game.current_player.name}")

    def open_trade_window(self):
        trade_window = tk.Toplevel(self.master)
        trade_window.title("Trade")

        # Offered resources
        tk.Label(trade_window, text="Offered Resources").grid(row=0, column=0)
        offered_entries = {}
        for i, resource in enumerate(self.game.players[0].resources.keys()):
            tk.Label(trade_window, text=resource.name).grid(row=i + 1, column=0)
            entry = tk.Entry(trade_window)
            entry.grid(row=i + 1, column=1)
            offered_entries[resource] = entry

        # Requested resources
        tk.Label(trade_window, text="Requested Resources").grid(row=0, column=2)
        requested_entries = {}
        for i, resource in enumerate(self.game.players[0].resources.keys()):
            tk.Label(trade_window, text=resource.name).grid(row=i + 1, column=2)
            entry = tk.Entry(trade_window)
            entry.grid(row=i + 1, column=3)
            requested_entries[resource] = entry

        # Player selection
        tk.Label(trade_window, text="Trade with:").grid(row=len(offered_entries) + 1, column=0)
        player_names = [p.name for p in self.game.players if p != self.game.current_player]
        selected_player = tk.StringVar(trade_window)
        selected_player.set(player_names[0])
        player_menu = tk.OptionMenu(trade_window, selected_player, *player_names)
        player_menu.grid(row=len(offered_entries) + 1, column=1)

        def submit_trade():
            offered = {res: int(entry.get() or 0) for res, entry in offered_entries.items()}
            requested = {res: int(entry.get() or 0) for res, entry in requested_entries.items()}

            receiving_player = next(p for p in self.game.players if p.name == selected_player.get())

            if self.game.trade(self.game.current_player, receiving_player, offered, requested):
                messagebox.showinfo("Trade", "Trade successful!")
                self.update_resource_labels()
                trade_window.destroy()
            else:
                messagebox.showerror("Trade", "Trade failed. Not enough resources.")

        submit_button = tk.Button(trade_window, text="Submit Trade", command=submit_trade)
        submit_button.grid(row=len(offered_entries) + 2, column=1, columnspan=2)

    def build_road(self):
        # This is a simplified version. We need to implement a way to get the
        # location from the user.
        location = "dummy_location"
        if self.game.build_road(self.game.current_player, location):
            messagebox.showinfo("Build Road", "Road built successfully!")
            self.update_resource_labels()
        else:
            messagebox.showerror("Build Road", "Failed to build road.")

    def build_settlement(self):
        # This is a simplified version. We need to implement a way to get the
        # location from the user.
        location = "dummy_location"
        if self.game.build_settlement(self.game.current_player, location):
            messagebox.showinfo("Build Settlement", "Settlement built successfully!")
            self.update_resource_labels()
        else:
            messagebox.showerror("Build Settlement", "Failed to build settlement.")

    def build_city(self):
        # This is a simplified version. We need to implement a way to get the
        # location from the user.
        location = "dummy_location"
        if self.game.build_city(self.game.current_player, location):
            messagebox.showinfo("Build City", "City built successfully!")
            self.update_resource_labels()
        else:
            messagebox.showerror("Build City", "Failed to build city.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CatanUI(root)
    root.mainloop()
