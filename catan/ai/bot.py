"""Heuristic Catan bot.

Entry point is ``advance_bots(game)``: if the current player (or a pending
discarder / robber-mover / stealer) is a bot, make one move and return True.
The server calls it in a loop so multiple sequential bot decisions chain.
"""

from __future__ import annotations

import random
from collections import defaultdict

from catan.src.components import Resource
from catan.src.game import Game
from catan.src.phase import TurnPhase
from catan.src.player import Player


# Classic Catan probability pip counts.
PROBABILITY = {
    2: 1, 3: 2, 4: 3, 5: 4, 6: 5,
    8: 5, 9: 4, 10: 3, 11: 2, 12: 1,
    7: 0,
}


def advance_bots(game: Game) -> bool:
    """Make one bot move. Returns True if any bot acted."""

    if game.phase == TurnPhase.GAME_OVER:
        return False

    # Any bot needing to discard? (7 was rolled; bots discard lowest-value cards.)
    if game.phase == TurnPhase.DISCARD:
        for seat_name, required in list(game.pending_discards.items()):
            p = game.get_player(seat_name)
            if p is not None and p.is_bot:
                _bot_discard(game, p, required)
                return True
        return False

    # Robber moves / steals are always by current_player; act if they're a bot.
    if game.phase == TurnPhase.MOVE_ROBBER:
        p = game.robber_mover
        if p is not None and p.is_bot:
            _bot_move_robber(game, p)
            return True
        return False

    if game.phase == TurnPhase.ROBBER_STEAL:
        p = game.robber_mover
        if p is not None and p.is_bot:
            target = random.choice(game.pending_steal_targets)
            game.steal_from(p, target)
            return True
        return False

    current = game.current_player
    if not current.is_bot:
        return False

    if game.phase in (TurnPhase.SETUP_1, TurnPhase.SETUP_2):
        return _bot_setup_action(game, current)

    if game.phase == TurnPhase.ROLL:
        game.roll_dice(current)
        return True

    if game.phase == TurnPhase.MAIN:
        return _bot_main_action(game, current)

    return False


# ---------------------------------------------------------------------------
# Setup placement
# ---------------------------------------------------------------------------

def _bot_setup_action(game: Game, bot: Player) -> bool:
    if game._setup_expects_road_for is not None:  # noqa: SLF001 - internal use
        edge = _pick_bot_setup_road(game, bot, game._setup_expects_road_for)
        if edge is None:
            return False
        game.place_setup_road(bot, edge)
        return True

    vertex = _pick_bot_settlement(game, bot)
    if vertex is None:
        return False
    game.place_setup_settlement(bot, vertex)
    return True


def _intersection_score(game: Game, vertex: int) -> float:
    """Sum of probabilities of adjacent tiles, with a diversity bonus."""
    tiles = game.board.get_tiles_for_settlement(vertex)
    score = 0.0
    resources = set()
    for tile in tiles:
        if tile.resource is None:
            continue
        score += PROBABILITY.get(tile.number, 0)
        resources.add(tile.resource)
    score += 0.3 * len(resources)
    return score


def _pick_bot_settlement(game: Game, bot: Player) -> int | None:
    candidates = []
    for vertex in range(54):
        if not game._is_valid_settlement_location(bot, vertex):  # noqa: SLF001
            continue
        candidates.append((vertex, _intersection_score(game, vertex)))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _pick_bot_setup_road(game: Game, bot: Player, pivot: int) -> tuple[int, int] | None:
    # Prefer an edge whose other endpoint has the highest expected production.
    best: tuple[int, int] | None = None
    best_score = -1.0
    for other in game.board.vertex_neighbors(pivot):
        edge = game.board.normalised_edge((pivot, other))
        if not game.board.is_edge(edge):
            continue
        if game._edge_is_occupied(edge):  # noqa: SLF001
            continue
        score = _intersection_score(game, other)
        if score > best_score:
            best_score = score
            best = edge
    return best


# ---------------------------------------------------------------------------
# Main-turn decisions
# ---------------------------------------------------------------------------

BUILD_COSTS = {
    "city": {Resource.GRAIN: 2, Resource.ORE: 3},
    "settlement": {Resource.BRICK: 1, Resource.LUMBER: 1, Resource.WOOL: 1, Resource.GRAIN: 1},
    "dev_card": {Resource.ORE: 1, Resource.WOOL: 1, Resource.GRAIN: 1},
    "road": {Resource.BRICK: 1, Resource.LUMBER: 1},
}


def _can_afford(player: Player, cost: dict[Resource, int]) -> bool:
    return all(player.resources[r] >= n for r, n in cost.items())


def _bot_main_action(game: Game, bot: Player) -> bool:
    # 1) City upgrade if we can
    if _can_afford(bot, BUILD_COSTS["city"]) and bot.settlements:
        game.build_city(bot, bot.settlements[0])
        return True

    # 2) Settlement if we can
    if _can_afford(bot, BUILD_COSTS["settlement"]):
        vertex = _best_settlement_spot(game, bot)
        if vertex is not None:
            ok, _ = game.build_settlement(bot, vertex)
            if ok:
                return True

    # 3) Dev card if deck available
    if _can_afford(bot, BUILD_COSTS["dev_card"]) and game.development_card_deck:
        ok, _ = game.buy_development_card(bot)
        if ok:
            return True

    # 4) Play a Knight if it would help (robber currently sitting on our hex)
    if _has_card(bot, "knight") and _robber_hurts_us(game, bot):
        ok, _ = game.play_development_card(bot, "knight")
        if ok:
            return True

    # 5) Build a road toward the best open intersection
    if _can_afford(bot, BUILD_COSTS["road"]):
        edge = _best_road_spot(game, bot)
        if edge is not None:
            ok, _ = game.build_road(bot, edge)
            if ok:
                return True

    # 6) Maritime-trade surplus into a useful resource
    if _try_maritime_trade(game, bot):
        return True

    # Nothing productive; end turn
    game.end_turn(bot)
    return True


def _has_card(bot: Player, kind: str) -> bool:
    return any(c.kind == kind for c in bot.development_cards)


def _robber_hurts_us(game: Game, bot: Player) -> bool:
    verts = set(game.board.vertices_on_tile(game.board.robber_location))
    return any(v in verts for v in bot.settlements + bot.cities)


def _best_settlement_spot(game: Game, bot: Player) -> int | None:
    own_edges = {game.board.normalised_edge(r) for r in bot.roads}
    endpoints = {v for e in own_edges for v in e}
    best = None
    best_score = -1.0
    for v in endpoints:
        if not game._is_valid_settlement_location(bot, v):  # noqa: SLF001
            continue
        score = _intersection_score(game, v)
        if score > best_score:
            best_score = score
            best = v
    return best


def _best_road_spot(game: Game, bot: Player) -> tuple[int, int] | None:
    own_edges = {game.board.normalised_edge(r) for r in bot.roads}
    endpoints = {v for e in own_edges for v in e}
    # Also consider endpoints on our buildings (first road from a settlement)
    for s in bot.settlements + bot.cities:
        endpoints.add(s)

    best = None
    best_score = -1.0
    for v in endpoints:
        for neighbour in game.board.vertex_neighbors(v):
            edge = game.board.normalised_edge((v, neighbour))
            if edge in own_edges:
                continue
            if game._edge_is_occupied(edge):  # noqa: SLF001
                continue
            # Score by best open vertex reachable past this edge
            score = _intersection_score(game, neighbour)
            if score > best_score:
                best_score = score
                best = edge
    return best


def _try_maritime_trade(game: Game, bot: Player) -> bool:
    # Figure out what we need for any achievable build.
    # Goal order: settlement → city → dev card → road
    goals = [
        BUILD_COSTS["settlement"],
        BUILD_COSTS["city"],
        BUILD_COSTS["dev_card"],
        BUILD_COSTS["road"],
    ]
    for cost in goals:
        shortfall = {r: n - bot.resources[r] for r, n in cost.items() if bot.resources[r] < n}
        if sum(shortfall.values()) != 1:
            continue  # Don't try to cover multi-resource gaps by one trade
        needed = next(iter(shortfall.keys()))
        # Find a resource we can afford to trade away
        for give, amount in bot.resources.items():
            if give == needed:
                continue
            ratio = _best_ratio(bot, give)
            if amount >= ratio + cost.get(give, 0):  # keep what we'd need
                ok, _ = game.maritime_trade(bot, give, needed)
                if ok:
                    return True
    return False


def _best_ratio(bot: Player, resource: Resource) -> int:
    r = 4
    for h in bot.harbors:
        if h.resource is None:
            r = min(r, 3)
        elif h.resource == resource:
            r = min(r, 2)
    return r


# ---------------------------------------------------------------------------
# Seven / robber
# ---------------------------------------------------------------------------

def _bot_discard(game: Game, bot: Player, required: int) -> None:
    # Discard from the most plentiful non-settlement-critical first.
    # Heuristic: we value ore/grain (build cities/dev cards) more than the rest.
    priority = [Resource.WOOL, Resource.LUMBER, Resource.BRICK, Resource.GRAIN, Resource.ORE]
    plan: dict[Resource, int] = defaultdict(int)
    remaining = required
    for r in priority:
        if remaining <= 0:
            break
        take = min(bot.resources[r], remaining)
        if take > 0:
            plan[r] = take
            remaining -= take
    game.submit_discard(bot, dict(plan))


def _bot_move_robber(game: Game, bot: Player) -> None:
    # Place on the hex that maximises (opp pips stolen) - (self pips stolen).
    best_idx = game.board.robber_location
    best_score = -1e9
    for idx, tile in enumerate(game.board.tiles):
        if idx == game.board.robber_location or tile.resource is None:
            continue
        verts = set(game.board.vertices_on_tile(idx))
        opp = 0
        self_hit = 0
        pip = PROBABILITY.get(tile.number, 0)
        for p in game.players:
            hits = sum(1 for v in p.settlements if v in verts) + 2 * sum(
                1 for v in p.cities if v in verts
            )
            if p is bot:
                self_hit += hits
            else:
                opp += hits
        score = opp * pip - self_hit * pip * 2
        if opp == 0:
            score -= 100
        if score > best_score:
            best_score = score
            best_idx = idx
    if best_idx == game.board.robber_location:
        # Fallback: any other hex
        for idx in range(len(game.board.tiles)):
            if idx != game.board.robber_location:
                best_idx = idx
                break
    game.move_robber(bot, best_idx)
