# How to Play Catan

Welcome to Catan! This document explains how to play this implementation of the classic board game.

## Objective
The goal of the game is to be the first player to reach 10 victory points. You score victory points by building settlements and cities.

- **Settlement**: 1 victory point
- **City**: 2 victory points

## Game Setup
The game board is randomly generated at the start of each game. This includes the placement of resource tiles (lumber, wool, grain, brick, ore) and the number tokens on them.

The initial setup phase, where players place their first two settlements and roads, is not yet fully implemented. For now, the game starts with players able to build freely for their first two settlements, without the need for road connectivity.

## Your Turn
On your turn, you can perform the following actions in order:

1.  **Roll the Dice**: Click the "Roll Dice" button to roll the dice. The result determines which resource tiles produce resources.
2.  **Collect Resources**: If the number rolled matches a tile adjacent to one of your settlements or cities, you receive resources. Settlements produce 1 resource, and cities produce 2.
3.  **Trade**: You can trade resources with other players. The trading UI is not yet implemented.
4.  **Build**: You can spend your resources to build new roads, settlements, or upgrade settlements to cities.
5.  **End Your Turn**: Click the "Next Turn" button to pass the turn to the next player.

## Building
To build, click on one of the build buttons ("Build Settlement", "Build City", "Build Road"). This will activate the build mode. Then, click on the board to select a location for your new piece.

### Building Costs
- **Road**: 1 Brick, 1 Lumber
- **Settlement**: 1 Brick, 1 Lumber, 1 Wool, 1 Grain
- **City**: 2 Grain, 3 Ore

### Building Rules
- **Roads**: A new road must be connected to one of your existing roads, settlements, or cities.
- **Settlements**:
    - A new settlement must be connected to one of your roads (unless it's one of your first two settlements).
    - A new settlement must be at least two edges away from any other settlement or city (the "Distance Rule").
- **Cities**: A city can only be built by upgrading one of your existing settlements.

## Winning the Game
The first player to reach 10 victory points wins the game. The game will announce the winner when this happens.
