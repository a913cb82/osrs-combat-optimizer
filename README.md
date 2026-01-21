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

Run the optimizer using `python3 optimize_melee.py`.

The tool automatically considers **all** F2P weapons and amulets. To exclude an item (or make it "expensive" to acquire), use the `--costs` argument.

For a full list of available arguments and their defaults, run:
```bash
python3 optimize_melee.py --help
```

### Key Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--goal` | Default goal for both skills. | `40` |
| `--goal_atk` | Specific target for Attack level. | `None` (uses goal) |
| `--goal_str` | Specific target for Strength level. | `None` (uses goal) |
| `--start_atk` | Starting Attack level. | `1` |
| `--start_str` | Starting Strength level. | `1` |
| `--costs` | Custom acquisition costs for specific items (format `name:time`). | None (default 30s) |
| `--lookahead` | Number of levels to look ahead for value estimation. | `100` |
| `--timeout` | Max execution time in seconds. | `300` |

### Time Formats
Costs can be specified in seconds (`30s`), minutes (`10m`), or hours (`1h`). Use a high cost (e.g., `999h`) to effectively exclude an item.

---

## Examples

### 1. The "Realistic" F2P Ironman (Meta)
Optimizes for 99/99, accounting for the massive grind to craft jewelry and the quest requirements for rune gear. Uses **nested shared costs** to model how the 15h Strength Amulet grind contributes toward the 110h Power Amulet total.

*   **Rune Scimitar:** ~1300h (90 Smithing)
*   **Champions' Guild:** ~5h (Unlocks both **Rune Sword** and **Rune Mace**)
*   **Crafting 50 (Str Ammy):** 15h.
*   **Crafting 70 (Power Ammy):** An *additional* 95h (110h total).

```bash
python3 optimize_melee.py \
  --goal 99 \
  --costs "rune scimitar:1300h" "adamant scimitar:100h" "barronite mace:9h" "accuracy:1h" \
  --shared_costs "rune sword,rune mace:5h" \
                 "str,power:15h" \
                 "power:95h" # Power Ammy Total = 15h (Shared) + 95h (Unique) = 110h
```

### 2. The "Rich" Main Account
Assumes you can buy any item instantly from the Grand Exchange (default cost ~30s). No cost overrides needed.

```bash
python3 optimize_melee.py --goal 99
```

### 3. Is the Rune Scimitar Worth It?
If you have a method to get a Rune Scimitar in **22 hours**, is it worth the grind over just using a Rune Sword?

```bash
python3 optimize_melee.py \
  --goal 99 \
  --costs "rune scimitar:22h" "rune sword:5h"
```
*(Spoiler: Yes, it saves ~2 hours total. If it takes >24 hours, it's a net loss.)*

### 5. Separate Skill Goals
Optimizes for a specific build, like 40 Attack / 99 Strength (F2P Pure).

```bash
python3 optimize_melee.py \
  --goal_atk 40 --goal_str 99 \
  --costs "rune scimitar:22h"
```

---

## How It Works

1.  **DPS Calculation:** Uses standard OSRS formulas (`floor(0.5 + ...)`).
2.  **Lookahead Window:** For every decision (e.g., at Atk 30 / Str 37), the optimizer looks ahead 100 levels. It calculates the "Window Score": the total time to train the next 100 levels using a specific weapon + its acquisition cost.
3.  **A* Search:** It explores the state space `(Attack, Strength, OwnedWeapons, OwnedAmmys)` using an admissible heuristic (estimated time to goal using best possible gear).
4.  **Pruning:** It aggressively removes suboptimal paths to ensure fast execution.

## License

MIT