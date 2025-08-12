import tkinter as tk
from tkinter import messagebox
from catan.src.game import Game
from catan.src.components import Resource, Hex
import math
import collections

# Hex grid layout and drawing logic from Red Blob Games
Point = collections.namedtuple("Point", ["x", "y"])

class Layout:
    def __init__(self, orientation, size, origin):
        self.orientation = orientation
        self.size = size
        self.origin = origin

def hex_to_pixel(layout, h):
    M = layout.orientation
    x = (M['f0'] * h.q + M['f1'] * h.r) * layout.size.x
    y = (M['f2'] * h.q + M['f3'] * h.r) * layout.size.y
    return Point(x + layout.origin.x, y + layout.origin.y)

def pixel_to_hex(layout, p):
    M = layout.orientation
    pt = Point((p.x - layout.origin.x) / layout.size.x, (p.y - layout.origin.y) / layout.size.y)
    q = M['b0'] * pt.x + M['b1'] * pt.y
    r = M['b2'] * pt.x + M['b3'] * pt.y
    return Hex(q, r, -q - r)

def hex_corner_offset(layout, corner):
    M = layout.orientation
    size = layout.size
    angle = 2.0 * math.pi * (M['start_angle'] + corner) / 6.0
    return Point(size.x * math.cos(angle), size.y * math.sin(angle))

def polygon_corners(layout, h):
    corners = []
    center = hex_to_pixel(layout, h)
    for i in range(6):
        offset = hex_corner_offset(layout, i)
        corners.append(Point(center.x + offset.x, center.y + offset.y))
    return corners

layout_pointy = {
    'f0': math.sqrt(3.0), 'f1': math.sqrt(3.0) / 2.0, 'f2': 0.0, 'f3': 3.0 / 2.0,
    'b0': math.sqrt(3.0) / 3.0, 'b1': -1.0 / 3.0, 'b2': 0.0, 'b3': 2.0 / 3.0,
    'start_angle': 0.5
}

class CatanUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Catan")
        self.game = Game(player_names=["Player 1", "Player 2", "Player 3"])
        self.canvas = tk.Canvas(master, width=800, height=600, bg='lightblue')
        self.canvas.pack()
        self.layout = Layout(layout_pointy, Point(30, 30), Point(400, 300))
        self.building_mode = None # "settlement", "city", or "road"

        self.canvas.bind("<Button-1>", self.canvas_click)
        self.create_widgets()
        self.draw_board()

    def create_widgets(self):
        # Player info and controls
        controls_frame = tk.Frame(self.master)
        controls_frame.pack()
        self.current_player_label = tk.Label(controls_frame, text=f"Current Player: {self.game.current_player.name}")
        self.current_player_label.pack()
        self.roll_button = tk.Button(controls_frame, text="Roll Dice", command=self.roll_dice)
        self.roll_button.pack(side=tk.LEFT)
        self.next_turn_button = tk.Button(controls_frame, text="Next Turn", command=self.next_turn)
        self.next_turn_button.pack(side=tk.LEFT)
        self.build_settlement_button = tk.Button(controls_frame, text="Build Settlement", command=self.activate_build_settlement)
        self.build_settlement_button.pack(side=tk.LEFT)
        self.build_city_button = tk.Button(controls_frame, text="Build City", command=self.activate_build_city)
        self.build_city_button.pack(side=tk.LEFT)
        self.build_road_button = tk.Button(controls_frame, text="Build Road", command=self.activate_build_road)
        self.build_road_button.pack(side=tk.LEFT)

        # Resource labels
        self.resource_labels = {}
        for i, player in enumerate(self.game.players):
            frame = tk.Frame(self.master)
            frame.pack()
            label = tk.Label(frame, text=f"{player.name}'s Resources: {player.resources}")
            label.pack()
            self.resource_labels[player.name] = label
        self.update_resource_labels()

    def draw_board(self):
        self.canvas.delete("all")
        # Draw tiles
        for h, tile in self.game.board.tiles.items():
            corners = polygon_corners(self.layout, h)
            self.canvas.create_polygon([p for corner in corners for p in corner],
                                     fill=self.get_tile_color(tile.resource),
                                     outline="black")
            center = hex_to_pixel(self.layout, h)
            self.canvas.create_text(center.x, center.y, text=f"{tile.number}\n{tile.resource.name if tile.resource else 'Desert'}")

        # Draw settlements, cities, and roads
        self.draw_pieces()

    def draw_pieces(self):
        # Draw roads
        for player in self.game.players:
            for road in player.roads:
                v1_loc, v2_loc = tuple(road)
                p1 = self.get_vertex_pixel(v1_loc)
                p2 = self.get_vertex_pixel(v2_loc)
                self.canvas.create_line(p1.x, p1.y, p2.x, p2.y, fill=player.color, width=5)

        # Draw settlements and cities
        for player in self.game.players:
            for settlement_loc in player.settlements:
                p = self.get_vertex_pixel(settlement_loc)
                self.canvas.create_oval(p.x-5, p.y-5, p.x+5, p.y+5, fill=player.color)
            for city_loc in player.cities:
                p = self.get_vertex_pixel(city_loc)
                self.canvas.create_rectangle(p.x-7, p.y-7, p.x+7, p.y+7, fill=player.color)

    def get_vertex_pixel(self, vertex_location):
        # A vertex is at the corner of multiple hexes. We can average their centers.
        # A simpler way is to treat a vertex as a point on the dual graph.
        # For this UI, we'll average the pixel coordinates of the centers of the hexes that define the vertex.
        points = [hex_to_pixel(self.layout, h) for h in vertex_location]
        avg_x = sum(p.x for p in points) / len(points)
        avg_y = sum(p.y for p in points) / len(points)
        return Point(avg_x, avg_y)

    def get_tile_color(self, resource):
        if resource is None: return "beige"
        return {
            Resource.LUMBER: "forestgreen", Resource.WOOL: "lightgray",
            Resource.GRAIN: "gold", Resource.BRICK: "firebrick",
            Resource.ORE: "darkgray"
        }.get(resource, "white")

    def roll_dice(self):
        roll = self.game.roll_dice()
        messagebox.showinfo("Dice Roll", f"You rolled a {roll}")
        self.update_resource_labels()
        self.draw_board()

    def next_turn(self):
        self.game.next_turn()
        self.current_player_label.config(text=f"Current Player: {self.game.current_player.name}")

    def update_resource_labels(self):
        for player in self.game.players:
            self.resource_labels[player.name].config(text=f"{player.name}'s Resources: {dict(player.resources)}")

    def activate_build_settlement(self):
        self.building_mode = "settlement"
        messagebox.showinfo("Build Mode", "Select a location to build a settlement.")

    def activate_build_city(self):
        self.building_mode = "city"
        messagebox.showinfo("Build Mode", "Select a settlement to upgrade to a city.")

    def activate_build_road(self):
        self.building_mode = "road"
        messagebox.showinfo("Build Mode", "Select a location to build a road.")

    def canvas_click(self, event):
        if not self.building_mode:
            return

        click_point = Point(event.x, event.y)

        if self.building_mode in ["settlement", "city"]:
            # Find the closest vertex
            closest_vertex = None
            min_dist = float('inf')
            for vertex_loc in self.game.board.vertex_map.keys():
                vertex_pixel = self.get_vertex_pixel(vertex_loc)
                dist = math.hypot(click_point.x - vertex_pixel.x, click_point.y - vertex_pixel.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_vertex = vertex_loc

            if closest_vertex and min_dist < 20: # 20 is a tolerance
                player = self.game.current_player
                if self.building_mode == "settlement":
                    success = self.game.build_settlement(player, closest_vertex)
                    if success:
                        messagebox.showinfo("Build", "Settlement built successfully!")
                    else:
                        messagebox.showerror("Build", "Failed to build settlement.")
                elif self.building_mode == "city":
                    success = self.game.build_city(player, closest_vertex)
                    if success:
                        messagebox.showinfo("Build", "City built successfully!")
                    else:
                        messagebox.showerror("Build", "Failed to build city.")

        elif self.building_mode == "road":
            # Find the closest edge
            closest_edge = None
            min_dist = float('inf')
            for v1_id in self.game.board.graph.getVertices():
                v1 = self.game.board.graph.getVertex(v1_id)
                for v2 in v1.getConnections():
                    v2_id = v2.getId()
                    if v1_id < v2_id: # Avoid duplicates
                        v1_loc = self.game.board.reverse_vertex_map[v1_id]
                        v2_loc = self.game.board.reverse_vertex_map[v2_id]
                        p1 = self.get_vertex_pixel(v1_loc)
                        p2 = self.get_vertex_pixel(v2_loc)
                        mid_point = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
                        dist = math.hypot(click_point.x - mid_point.x, click_point.y - mid_point.y)
                        if dist < min_dist:
                            min_dist = dist
                            closest_edge = frozenset([v1_loc, v2_loc])

            if closest_edge and min_dist < 20:
                player = self.game.current_player
                success = self.game.build_road(player, closest_edge)
                if success:
                    messagebox.showinfo("Build", "Road built successfully!")
                else:
                    messagebox.showerror("Build", "Failed to build road.")

        self.building_mode = None
        self.update_resource_labels()
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    app = CatanUI(root)
    root.mainloop()
