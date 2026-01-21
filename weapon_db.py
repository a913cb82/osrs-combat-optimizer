# Weapon Database Generator

# --- Base Weapon Stats (Attack Speed) ---
# Speed: Seconds per attack (ticks * 0.6)

WEAPON_TYPES = {
    "dagger":     {"speed": 2.4},
    "sword":      {"speed": 2.4},
    "scimitar":   {"speed": 2.4},
    "longsword":  {"speed": 3.0},
    "mace":       {"speed": 2.4},
    "battleaxe":  {"speed": 3.6},
    "warhammer":  {"speed": 3.6},
    "2h sword":   {"speed": 4.2},
}

# --- Material Tiers (Level Req) ---
MATERIALS = {
    "bronze":   {"req": 1},
    "iron":     {"req": 1},
    "steel":    {"req": 5},
    "black":    {"req": 10},
    "mithril":  {"req": 20},
    "adamant":  {"req": 30},
    "rune":     {"req": 40},
}

# --- Exact Stats Overrides (Source of Truth) ---
# Format: "material weapon": (Stab, Slash, Crush, Str)
EXACT_STATS = {
    # Bronze
    "bronze dagger":     (4, 2, -4, 3),
    "bronze sword":      (4, 3, -2, 5),
    "bronze scimitar":   (1, 7, -2, 6),
    "bronze longsword":  (4, 5, -2, 7),
    "bronze mace":       (1, -2, 6, 5),
    "bronze battleaxe":  (-2, 6, 3, 9),
    "bronze warhammer":  (-4, -4, 10, 10),
    "bronze 2h sword":   (-4, 9, 8, 10),

    # Iron
    "iron dagger":       (5, 3, -4, 4),
    "iron sword":        (6, 4, -2, 7),
    "iron scimitar":     (2, 10, -2, 9),
    "iron longsword":    (6, 8, -2, 10),
    "iron mace":         (4, -2, 9, 7),
    "iron battleaxe":    (-2, 8, 5, 13),
    "iron warhammer":    (-4, -4, 11, 11),
    "iron 2h sword":     (-4, 14, 12, 15),

    # Steel
    "steel dagger":      (8, 4, -4, 7),
    "steel sword":       (11, 8, -2, 12),
    "steel scimitar":    (3, 15, -2, 14),
    "steel longsword":   (9, 14, -2, 16),
    "steel mace":        (7, -2, 13, 11),
    "steel battleaxe":   (-2, 16, 11, 20),
    "steel warhammer":   (-4, -4, 18, 16),
    "steel 2h sword":    (-4, 21, 18, 22),

    # Black
    "black dagger":      (10, 5, -4, 7),
    "black sword":       (14, 10, -2, 12),
    "black scimitar":    (4, 19, -2, 14),
    "black longsword":   (13, 18, -2, 16),
    "black mace":        (8, -2, 16, 13),
    "black battleaxe":   (-2, 20, 15, 24),
    "black warhammer":   (-4, -4, 22, 22),
    "black 2h sword":    (-4, 26, 22, 26),

    # Mithril
    "mithril dagger":    (11, 5, -4, 10),
    "mithril sword":     (16, 11, -2, 17),
    "mithril scimitar":  (5, 21, -2, 20),
    "mithril longsword": (15, 20, -2, 22),
    "mithril mace":      (11, -2, 18, 16),
    "mithril battleaxe": (-2, 22, 17, 29),
    "mithril warhammer": (-4, -4, 25, 27),
    "mithril 2h sword":  (-4, 32, 26, 33),

    # Adamant
    "adamant dagger":    (15, 8, -4, 14),
    "adamant sword":     (23, 18, -2, 24),
    "adamant scimitar":  (6, 29, -2, 28),
    "adamant longsword": (20, 29, -2, 31),
    "adamant mace":      (13, -2, 25, 23),
    "adamant battleaxe": (-2, 31, 26, 41),
    "adamant warhammer": (-4, -4, 35, 39),
    "adamant 2h sword":  (-4, 43, 35, 44),

    # Rune
    "rune dagger":       (25, 12, -4, 24),
    "rune sword":        (38, 26, -2, 39),
    "rune scimitar":     (7, 45, -2, 44),
    "rune longsword":    (38, 47, -2, 49),
    "rune mace":         (20, -2, 39, 36),
    "rune battleaxe":    (-2, 48, 43, 64),
    "rune warhammer":    (-4, -4, 53, 53),
    "rune 2h sword":     (-4, 69, 50, 70),
    
    # Special
    "barronite mace":    (0, 0, 40, 40),
}

# --- Database Generation ---
WEAPON_DB = {}

for name, stats in EXACT_STATS.items():
    parts = name.split()
    if "2h" in name:
        w_type = "2h sword"
        material = parts[0]
    elif "barronite" in name:
        w_type = "mace"
        material = "rune"
    else:
        w_type = parts[-1]
        material = parts[0]
        
    type_data = WEAPON_TYPES.get(w_type, {"speed": 2.4})
    mat_data = MATERIALS.get(material, {"req": 1})
    if "barronite" in name: mat_data = {"req": 40}
    
    WEAPON_DB[name] = {
        "atk_req": mat_data["req"],
        "bonus": {
            "stab": stats[0],
            "slash": stats[1],
            "crush": stats[2]
        },
        "str": stats[3],
        "speed": type_data["speed"],
        "cost": 30.0
    }