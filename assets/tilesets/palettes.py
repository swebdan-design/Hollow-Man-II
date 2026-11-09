"""Background palette sets.  Each set = 6 environment palettes (roles 0..5)
+ palette 6 (HUD) + palette 7 (dialogue/UI).  Colour index 0 = lightest."""
from gfx import hexcol


def P(*hs):
    return [hexcol(h) for h in hs]


HUD = P('e8dcc0', '8c1c1c', 'a02020', '1a1614')    # fg glyph=3 -> we invert below
# NOTE: font glyph pixels use colour 3, background colour 0.
HUD = P('1a1614', '6a5038', 'b02424', 'e8dcc0')       # dark HUD, cream glyphs, crimson hearts
DLG = P('e8dcc0', 'b49a74', '8c2a1e', '181210')       # cream paper, black ink

BASE = {
    'city': [
        P('8a8070', '5c5448', '3c362e', '1c1814'),   # ground
        P('a88060', '7a4a34', '542c20', '1e1210'),   # brick
        P('b89868', '806040', '4c3624', '1c140c'),   # wood
        P('8c8a58', '5e6038', '3a3c24', '161810'),   # foliage
        P('9aa0a0', '5e6c70', '34404a', '12161a'),   # metal/water
        P('e8d890', 'b89040', '8c2420', '1c1010'),   # light/sign
    ],
    'interior': [
        P('a08460', '74583c', '4a3624', '1e140c'),   # floor wood
        P('8c7c64', '6a5a48', '463a2e', '1c1610'),   # wall
        P('b08c5c', '7c5a38', '4a3420', '1a120a'),   # furniture
        P('a05a48', '7a2c24', '4c1a16', '1c0c0a'),   # fabric/crimson
        P('a0a098', '6c6c68', '3e3e3c', '161616'),   # metal/stone
        P('ecdc98', 'c0a050', '8c3024', '1c1010'),   # light
    ],
    'under': [
        P('7c7868', '545246', '34342c', '141410'),   # concrete
        P('6c685a', '4c483e', '2e2c26', '100e0c'),   # wall
        P('9a7a58', '6a4c34', '3e2c1e', '140e08'),   # rust metal
        P('6c8070', '3e5246', '22302a', '0c1410'),   # water
        P('d0d4d0', '9ca4a4', '5c6668', '1c2024'),   # frost/bone
        P('e0c070', 'a82c20', '601810', '180808'),   # light/crimson
    ],
}


def mix(c, t, a):
    return tuple(int(c[i] * (1 - a) + t[i] * a) for i in range(3))


def mood(pals, tint=None, amt=0.0, bright=1.0, roles=None):
    out = []
    for i, p in enumerate(pals):
        if roles is not None and i not in roles:
            out.append(p)
            continue
        q = []
        for c in p:
            c = tuple(min(255, int(v * bright)) for v in c)
            if tint:
                c = mix(c, hexcol(tint), amt)
            q.append(c)
        out.append(q)
    return out


def S(pals):
    return pals + [HUD, DLG]


SETS = {
    # name: (tileset, palettes)
    'city_night': ('city', S(BASE['city'])),
    'city_mercy': ('city', S(mood(BASE['city'], '806848', 0.35, 0.92))),
    'city_strip': ('city', S(mood(BASE['city'], '5a6070', 0.15, 0.95))),
    'city_indust': ('city', S(mood(BASE['city'], '6a6a40', 0.30, 0.9))),
    'city_neon': ('city', S(mood(BASE['city'], '902030', 0.25, 0.9))),
    'city_old': ('city', S(mood(BASE['city'], '485870', 0.30, 0.85))),
    'city_ward': ('city', S(mood(BASE['city'], '5c7058', 0.35, 0.85))),
    'city_canal': ('city', S(mood(BASE['city'], '3c5850', 0.30, 0.85))),
    'int_warm': ('interior', S(BASE['interior'])),
    'int_motel': ('interior', S(mood(BASE['interior'], '903040', 0.20, 0.9))),
    'int_church': ('interior', S(mood(BASE['interior'], '485068', 0.35, 0.85))),
    'int_records': ('interior', S(mood(BASE['interior'], 'c0c090', 0.25, 1.0))),
    'int_ward': ('interior', S(mood(BASE['interior'], '88a088', 0.35, 0.92))),
    'int_dark': ('interior', S(mood(BASE['interior'], '201820', 0.35, 0.8))),
    'und_sewer': ('under', S(BASE['under'])),
    'und_cold': ('under', S(mood(BASE['under'], '8098b0', 0.35, 1.05))),
    'und_crypt': ('under', S(mood(BASE['under'], '504860', 0.30, 0.85))),
    'und_basement': ('under', S(mood(BASE['under'], '705038', 0.30, 0.85))),
    'und_ward': ('under', S(mood(BASE['under'], '506850', 0.30, 0.85))),
}
