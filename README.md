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
| `--reqs` | Dependency graph for items (format `node:cost:parents`). | None |
| `--lookahead` | Number of levels to look ahead for value estimation. | `100` |
| `--timeout` | Max execution time in seconds. | `300` |

### Time Formats
Costs can be specified in seconds (`30s`), minutes (`10m`), or hours (`1h`).

---

## Examples

### 1. The "Realistic" F2P Ironman (Meta)
Optimizes for 99/99, modeling the complex unlock requirements for top-tier gear.

*   **Rune Scimitar:** ~1300h (90 Smithing) -> Excluded via high cost.
*   **Champions' Guild:** 5h Questing -> Unlocks Rune Sword & Mace.
*   **Crafting:** 50 (Str Ammy) takes 15h. 70 (Power Ammy) takes another 95h (110h total).

```bash
python3 optimize_melee.py \
  --goal 99 \
  --reqs "rune scimitar:1300h" "adamant scimitar:100h" "barronite mace:9h" "accuracy:1h" \
         "guild:5h" \
         "rune sword:30s:guild" \
         "rune mace:30s:guild" \
         "crafting_50:15h" \
         "str:0s:crafting_50" \
         "crafting_70:95h:crafting_50" \
         "power:0s:crafting_70"
```

### 2. The "Rich" Main Account
Assumes you can buy any item instantly from the Grand Exchange (default cost ~30s). No special setup needed.

```bash
python3 optimize_melee.py --goal 99
```

### 3. Is the Rune Scimitar Worth It?
If you have a method to get a Rune Scimitar in **22 hours**, is it worth the grind over just using a Rune Sword?

```bash
python3 optimize_melee.py \
  --goal 99 \
  --reqs "rune scimitar:22h" "rune sword:5h"
```
*(Spoiler: Yes, it saves ~2 hours total. If it takes >24 hours, it's a net loss.)*

### 4. Separate Skill Goals (Pures)
Optimizes for a specific build, like 40 Attack / 99 Strength.

```bash
python3 optimize_melee.py \
  --goal_atk 40 --goal_str 99 \
  --reqs "rune scimitar:22h"
```

---

## How It Works

1.  **DPS Calculation:** Uses standard OSRS formulas (`floor(0.5 + ...)`).
2.  **Lookahead Window:** For every decision (e.g., at Atk 30 / Str 37), the optimizer looks ahead 100 levels. It calculates the "Window Score": the total time to train the next 100 levels using a specific weapon + its acquisition cost.
3.  **A* Search:** It explores the state space `(Attack, Strength, OwnedWeapons, OwnedAmmys)` using an admissible heuristic (estimated time to goal using best possible gear).
4.  **Pruning:** It aggressively removes suboptimal paths to ensure fast execution.

## License

MIT
