# OSRS F2P Melee Optimizer

A high-fidelity optimization tool for Old School RuneScape (F2P) melee training. It calculates the mathematically optimal path to reach your Attack and Strength goals by simulating every hit, considering:

*   **Damage Per Second (DPS):** Exact max hit and accuracy formulas.
*   **Weapon & Amulet Stats:** Full F2P database (Bronze to Rune).
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

The tool automatically considers **all** F2P weapons and amulets. To exclude an item (or make it "expensive" to acquire), use the `--costs` argument.

For a full list of available arguments and their defaults, run:
```bash
python3 new_optimize_leveling.py --help
```

### Key Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--goal` | Target level for both Attack and Strength. | `40` |
| `--costs` | Custom acquisition costs for specific items (format `name:time`). | None (default 30s) |
| `--lookahead` | Number of levels to look ahead for value estimation. | `100` |
| `--timeout` | Max execution time in seconds. | `300` |

### Time Formats
Costs can be specified in seconds (`30s`), minutes (`10m`), or hours (`1h`). Use a high cost (e.g., `999h`) to effectively exclude an item.

---

## Examples

### 1. The "Realistic" F2P Ironman (Meta)
Optimizes for 99/99, accounting for the massive grind to craft and enchant high-tier jewelry and weapons.

*   **Rune Scimitar:** ~1300h (90 Smithing) -> Excluded.
*   **Adamant Scimitar:** ~100h (75 Smithing) -> Excluded.
*   **Amulet of Power:** ~110h (70 Crafting + 57 Magic) -> Likely skipped.
*   **Amulet of Strength:** ~15h (50 Crafting + 49 Magic) -> Realistic goal.
*   **Barronite Mace:** ~9h (Camdozaal RNG) -> Marginal upgrade.
*   **Rune Sword:** ~5h (Champions' Guild) -> Primary weapon.

```bash
python3 new_optimize_leveling.py \
  --goal 99 \
  --costs "rune scimitar:1300h" "adamant scimitar:100h" "rune sword:5h" "barronite mace:9h" \
          "power:110h" "str:15h" "accuracy:1h"
```

### 2. The "Rich" Main Account
Assumes you can buy any item instantly from the Grand Exchange (default cost ~30s). No cost overrides needed.

```bash
python3 new_optimize_leveling.py --goal 99
```

### 3. Is the Rune Scimitar Worth It?
If you have a method to get a Rune Scimitar in **22 hours**, is it worth the grind over just using a Rune Sword?

```bash
python3 new_optimize_leveling.py \
  --goal 99 \
  --costs "rune scimitar:22h" "rune sword:5h"
```
*(Spoiler: Yes, it saves ~2 hours total. If it takes >24 hours, it's a net loss.)*

---

## How It Works

1.  **DPS Calculation:** Uses standard OSRS formulas (`floor(0.5 + ...)`).
2.  **Lookahead Window:** For every decision (e.g., at Atk 30 / Str 37), the optimizer looks ahead 100 levels. It calculates the "Window Score": the total time to train the next 100 levels using a specific weapon + its acquisition cost.
3.  **A* Search:** It explores the state space `(Attack, Strength, OwnedWeapons, OwnedAmmys)` using an admissible heuristic (estimated time to goal using best possible gear).
4.  **Pruning:** It aggressively removes suboptimal paths to ensure fast execution.

## License

MIT