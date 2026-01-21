# OSRS F2P Melee Optimizer

A high-fidelity optimization tool for Old School RuneScape (F2P) melee training. It calculates the mathematically optimal path to reach your Attack and Strength goals by simulating every hit, considering:

*   **Damage Per Second (DPS):** Exact max hit and accuracy formulas.
*   **Weapon Stats:** Full F2P weapon database (Bronze to Rune).
*   **Acquisition Cost:** Is it worth spending 5 hours to get a Rune Sword? Or 22 hours for a Rune Scimitar?
*   **Global Lookahead:** Uses A* search to make "investment" decisions (e.g., spending time now to save more time later).

## Installation

Requires Python 3.6+.

```bash
# Clone the repository
git clone <your-repo-url>
cd osrs_dps

# No external dependencies required!
```

## Usage

Run the optimizer using `python3 new_optimize_leveling.py`. 

For a full list of available arguments and their defaults, run:
```bash
python3 new_optimize_leveling.py --help
```

---

## Examples

### 1. The "Realistic" F2P Ironman (Meta)
Optimizes for 99/99, assuming you can buy a **Rune Sword** (Champions' Guild, ~5h) but cannot reasonably smith a **Rune Scimitar** (~1300h) or **Adamant Scimitar** (~100h).

```bash
python3 new_optimize_leveling.py \
  --goal 99 \
  --weapons scimitar sword mace "barronite mace" \
  --costs "rune scimitar:999h" "adamant scimitar:100h" "rune sword:5h" "barronite mace:9h" \
  --amulet str
```

### 2. The "Rich" Main Account
Assumes you can buy any item instantly from the Grand Exchange (default cost ~30s).

```bash
python3 new_optimize_leveling.py \
  --goal 99 \
  --weapons scimitar sword 2h warhammer mace \
  --amulet power
```

### 3. Sword vs. Mace Comparison
Curious if Maces are better than Swords for Strength training? (Hint: They often are!).

```bash
python3 new_optimize_leveling.py \
  --goal 60 \
  --weapons sword mace \
  --costs "rune sword:0s" "rune mace:0s" \
  --amulet str
```

### 4. Is the Rune Scimitar Worth It?
If you have a method to get a Rune Scimitar in **22 hours**, is it worth the grind over just using a Rune Sword?

```bash
python3 new_optimize_leveling.py \
  --goal 99 \
  --weapons scimitar sword \
  --costs "rune scimitar:22h" "rune sword:5h" \
  --amulet str
```
*(Spoiler: Yes, it saves ~2 hours total. If it takes >24 hours, it's a net loss.)*

---

## How It Works

1.  **DPS Calculation:** Uses standard OSRS formulas (`floor(0.5 + ...)`).
2.  **Lookahead Window:** For every decision (e.g., at Atk 30 / Str 37), the optimizer looks ahead 100 levels. It calculates the "Window Score": the total time to train the next 100 levels using a specific weapon + its acquisition cost.
3.  **A* Search:** It explores the state space `(Attack, Strength, OwnedWeapons)` using an admissible heuristic (estimated time to goal using best possible gear).
4.  **Pruning:** It aggressively removes suboptimal paths (e.g., if Weapon A has strictly worse DPS than Weapon B and you own both, A is ignored).
