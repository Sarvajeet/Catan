import sys
from catan.src.game import Game
from catan.src.player import Player
from catan.src.components import Resource

class CatanTextUI:
    def __init__(self):
        self.game = Game(player_names=["Player 1", "Player 2", "Player 3"])
        self._setup_game()

    def _setup_game(self):
        # Simplified setup for now
        initial_placements = [
            # P1
            {"settlement": 8, "road": (8, 9)},
            {"settlement": 22, "road": (22, 21)},
            # P2
            {"settlement": 14, "road": (14, 13)},
            {"settlement": 33, "road": (33, 32)},
            # P3
            {"settlement": 40, "road": (40, 41)},
            {"settlement": 45, "road": (45, 46)},
        ]
        self.game.start_game(initial_placements)
        print("Catan game started!")

    def run(self):
        while not self.game.check_for_winner():
            self.print_game_state()
            self.take_turn()
            self.game.next_turn()

        winner = self.game.check_for_winner()
        print(f"\n\nPlayer {winner.name} has won the game!")

    def print_game_state(self):
        print("\n" + "="*30)
        print(f"Turn {self.game.turn}: Player {self.game.current_player.name}'s turn")
        print("="*30)
        for player in self.game.players:
            self.print_player_info(player)
        print("-" * 30)

    def print_player_info(self, player):
        print(f"{player.name} ({player.color}):")
        print(f"  Victory Points: {player.victory_points}")
        print(f"  Resources: {dict(player.resources)}")
        print(f"  Development Cards: {len(player.development_cards)}")
        print(f"  Knights: {player.knights}")

    def take_turn(self):
        player = self.game.current_player
        print(f"\n{player.name}, it's your turn.")

        # 1. Roll dice
        input("Press Enter to roll the dice...")
        roll = self.game.roll_dice()
        print(f"You rolled a {roll}")
        if roll == 7:
            print("Robber activated!")
            # Simplified robber action for now
            print("The robber has been moved randomly.")
        else:
            print("Resources have been distributed.")

        self.print_player_info(player)

        # 2. Actions
        while True:
            action = input("\nChoose an action: [b]uild, [t]rade, [p]lay card, [e]nd turn: ").lower()
            if action == 'b':
                self.handle_build(player)
            elif action == 't':
                self.handle_trade(player)
            elif action == 'p':
                self.handle_play_card(player)
            elif action == 'e':
                break
            else:
                print("Invalid action.")

    def handle_build(self, player):
        build_choice = input("What do you want to build? [r]oad, [s]ettlement, [c]ity, [d]ev card: ").lower()
        if build_choice == 'r':
            try:
                loc1 = int(input("Enter road start vertex: "))
                loc2 = int(input("Enter road end vertex: "))
                if self.game.build_road(player, (loc1, loc2)):
                    print("Road built successfully.")
                else:
                    print("Failed to build road.")
            except ValueError:
                print("Invalid vertex.")
        elif build_choice == 's':
            try:
                loc = int(input("Enter settlement vertex: "))
                if self.game.build_settlement(player, loc):
                    print("Settlement built successfully.")
                else:
                    print("Failed to build settlement.")
            except ValueError:
                print("Invalid vertex.")
        elif build_choice == 'c':
            try:
                loc = int(input("Enter city vertex: "))
                if self.game.build_city(player, loc):
                    print("City built successfully.")
                else:
                    print("Failed to build city.")
            except ValueError:
                print("Invalid vertex.")
        elif build_choice == 'd':
            if self.game.buy_development_card(player):
                print("Development card purchased.")
            else:
                print("Failed to buy development card.")
        else:
            print("Invalid build choice.")

    def handle_trade(self, player):
        trade_type = input("Trade with [p]layer or [m]aritime? ").lower()
        if trade_type == 'p':
            self.handle_player_trade(player)
        elif trade_type == 'm':
            self.handle_maritime_trade(player)
        else:
            print("Invalid trade type.")

    def handle_player_trade(self, player):
        other_player_name = input("Enter player name to trade with: ")
        other_player = next((p for p in self.game.players if p.name == other_player_name), None)
        if not other_player:
            print("Player not found.")
            return

        print("Enter resources to offer (e.g., 'lumber 1, brick 2'):")
        offered_str = input("> ")
        print("Enter resources to request:")
        requested_str = input("> ")

        try:
            offered_resources = self._parse_resources(offered_str)
            requested_resources = self._parse_resources(requested_str)
        except ValueError:
            print("Invalid resource format.")
            return

        if self.game.trade(player, other_player, offered_resources, requested_resources):
            print("Trade successful.")
        else:
            print("Trade failed.")

    def handle_maritime_trade(self, player):
        resource_to_give_str = input("Enter resource to give: ").upper()
        resource_to_get_str = input("Enter resource to get: ").upper()
        try:
            resource_to_give = Resource[resource_to_give_str]
            resource_to_get = Resource[resource_to_get_str]
        except KeyError:
            print("Invalid resource name.")
            return

        if self.game.maritime_trade(player, resource_to_give, resource_to_get):
            print("Maritime trade successful.")
        else:
            print("Maritime trade failed.")

    def handle_play_card(self, player):
        if not player.development_cards:
            print("You have no development cards to play.")
            return

        print("Your development cards:")
        for i, card in enumerate(player.development_cards):
            print(f"  {i}: {card.name}")

        try:
            choice = int(input("Choose a card to play: "))
            card = player.development_cards[choice]
        except (ValueError, IndexError):
            print("Invalid choice.")
            return

        kwargs = {}
        if card.name == "Knight":
            try:
                new_loc = int(input("Enter new robber location (tile index): "))
                kwargs['new_location'] = new_loc
                # Add logic to choose a player to steal from if applicable
            except ValueError:
                print("Invalid location.")
                return
        elif card.name == "Monopoly":
            res_str = input("Enter resource to monopolize: ").upper()
            try:
                kwargs['resource'] = Resource[res_str]
            except KeyError:
                print("Invalid resource.")
                return
        elif card.name == "Road Building":
            try:
                r1_v1 = int(input("Enter road 1 start vertex: "))
                r1_v2 = int(input("Enter road 1 end vertex: "))
                r2_v1 = int(input("Enter road 2 start vertex: "))
                r2_v2 = int(input("Enter road 2 end vertex: "))
                kwargs['road1_loc'] = (r1_v1, r1_v2)
                kwargs['road2_loc'] = (r2_v1, r2_v2)
            except ValueError:
                print("Invalid vertex.")
                return
        elif card.name == "Year of Plenty":
            try:
                res1_str = input("Enter first resource to take: ").upper()
                res2_str = input("Enter second resource to take: ").upper()
                kwargs['resource1'] = Resource[res1_str]
                kwargs['resource2'] = Resource[res2_str]
            except KeyError:
                print("Invalid resource.")
                return

        if self.game.play_development_card(player, card, **kwargs):
            print(f"{card.name} card played successfully.")
        else:
            print("Failed to play card.")

    def _parse_resources(self, resources_str):
        resources = {}
        parts = resources_str.split(',')
        for part in parts:
            name, amount = part.strip().split()
            resources[Resource[name.upper()]] = int(amount)
        return resources

if __name__ == "__main__":
    ui = CatanTextUI()
    ui.run()