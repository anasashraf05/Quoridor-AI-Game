# Quoridor AI Game

A complete implementation of the **Quoridor** board game built with Python and Pygame, featuring a polished GUI, full rule enforcement, and an AI opponent powered by Minimax with Alpha-Beta pruning.

---

## Table of Contents

- [Game Description](#game-description)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Running the Game](#running-the-game)
- [Controls](#controls)
- [Game Modes](#game-modes)
- [AI Opponent](#ai-opponent)
- [Project Structure](#project-structure)
- [Demo Video](#demo-video)

---

## Game Description

Quoridor is an abstract strategy board game invented by Mirko Marchesi (1997) and winner of the Mensa Mind Game award. Two players race their pawns across a 9×9 grid to reach the opposite side, while strategically placing walls to slow each other down.

**Objective:** Be the first player to move your pawn to any square on the opponent's starting row.

**On each turn, a player must either:**
- Move their pawn one square orthogonally (up, down, left, or right), or
- Place one wall segment on the board to redirect the opponent.

**Movement rules:**
- Pawns cannot move through walls or onto an opponent's square.
- If your pawn is directly adjacent to the opponent's pawn, you may **jump over** them (straight jump) — provided no wall blocks the landing square.
- If a straight jump is blocked by a wall or the board edge, you may instead move **diagonally** around the opponent.

**Wall rules:**
- Each player starts with **10 walls**.
- Walls span two cell-edges and cannot overlap or cross existing walls.
- A wall placement is **illegal** if it would completely cut off either player's path to their goal (guaranteed by BFS validation on every placement attempt).
- Once placed, walls cannot be moved or removed.

---

## Screenshots

> *(Add screenshots here after running the game — e.g., `docs/screenshot_menu.png`, `docs/screenshot_gameplay.png`)*

| Mode Selection | Gameplay | Winner Screen |
|:-:|:-:|:-:|
| ![Menu](src/ui/assets/Screenshot%202026-05-27%20173133.png) | ![Gameplay](src/ui/assets/Screenshot%202026-05-27%20173342.png) | ![Winner](src/ui/assets/Screenshot%202026-05-27%20173434.png) |

---

## Installation

### Prerequisites

- Python **3.10** or later
- [pip](https://pip.pypa.io/)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/Quoridor-AI-Game.git
   cd Quoridor-AI-Game
   ```

2. **Install the required dependency:**
   ```bash
   pip install pygame
   ```

   > No other third-party libraries are required. All game logic, AI, and UI are implemented from scratch.

---

## Running the Game

```bash
python main.py
```

The game window will open and display the mode selection screen.

---

## Controls

| Input | Action |
|---|---|
| **Left click** on a highlighted green square | Move your pawn to that square |
| **Left click** on a wall gap | Place a wall at that position (hover to preview) |
| **R key** or **Reset button** | Restart the current game |
| **Close window / Alt+F4** | Quit the game |

**Visual cues:**
- 🟢 **Green squares** — valid pawn destinations for the current player
- 🟡 **Yellow wall preview** — shows where a wall will be placed on hover
- 🔴 **Red walls** — placed by Player 1
- 🔵 **Blue walls** — placed by Player 2

---

## Game Modes

Select your mode from the opening screen:

### Human vs Human
Two players take turns on the same keyboard and mouse. Ideal for local two-player matches.

### Human vs AI
Player 1 is human; Player 2 is the AI. The AI uses Minimax with Alpha-Beta pruning at **Medium** difficulty (2-ply search depth) by default.

---

## AI Opponent

The AI is implemented using the **Minimax algorithm with Alpha-Beta pruning**.

### Difficulty Levels

| Difficulty | Search Depth | Behaviour |
|---|---|---|
| Easy | 1 ply | Looks one move ahead — makes locally reasonable moves |
| Medium | 2 plies | Looks two moves ahead — balances offence and defence |
| Hard | 3 plies | Looks three moves ahead — more strategic wall usage |

> The difficulty can be changed by editing `difficulty=DIFFICULTY.MEDIUM` in `src/controller/game_controller.py`.

### How the AI Evaluates the Board

At each leaf node of the search tree, the board is scored using:

```
score = (human's shortest path to goal) − (AI's shortest path to goal)
```

A higher score means the AI is relatively closer to winning. Shortest paths are computed using **BFS** from each player's current position to their goal row, respecting all placed walls.

### Why Alpha-Beta Pruning?

The legal-action space in Quoridor is large — up to ~128 wall placements plus pawn moves per turn. Alpha-Beta pruning cuts branches that cannot affect the final decision, making deeper searches feasible without sacrificing correctness.

---

## Project Structure

```
Quoridor-AI-Game/
├── main.py                        # Entry point
├── src/
│   ├── core/                      # Game logic (no UI dependencies)
│   │   ├── board.py               # Board state, wall storage, pawn positions
│   │   ├── rules.py               # Move validation and win detection
│   │   ├── pathfinder.py          # BFS for path existence and shortest path
│   │   ├── player.py              # Player model (position, wall count)
│   │   ├── wall.py                # Wall model and blocked-edge calculation
│   │   └── enums.py               # GameMode, Orientation, DIFFICULTY enums
│   ├── ai/                        # AI subsystem
│   │   ├── minimax.py             # Minimax + Alpha-Beta search
│   │   ├── evaluation.py          # Board evaluation heuristic
│   │   └── ai_player.py           # AI player interface
│   ├── controller/
│   │   └── game_controller.py     # Orchestrates game flow, connects UI ↔ logic
│   ├── ui/                        # Pygame rendering and input
│       ├── game_screen.py         # Main window, game loop, event dispatch
│       ├── renderer.py            # All drawing routines
│       ├── input_handler.py       # Mouse/keyboard → game actions
│       └── constants.py           # All visual constants and colours
│
├──tests/
│       └── test_game.py     
└── README.md
```

---

## Demo Video

>📹 [Watch the Demo Video](https://drive.google.com/file/d/1MS3SollmXqDL4VF-NsKLnErDfp8tIIX4/view?usp=sharing)

The video covers:
- Game setup and UI overview
- A full Human vs Human game
- A full Human vs AI game demonstrating the AI's wall-blocking strategy

---

## References

- [Official Quoridor Rules](https://en.gigamic.com/game/quoridor)
- [Quoridor on BoardGameGeek](https://boardgamegeek.com/boardgame/624/quoridor)
- [Minimax with Alpha-Beta Pruning — Wikipedia](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
- [BFS Pathfinding](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Pygame Documentation](https://www.pygame.org/docs/)
