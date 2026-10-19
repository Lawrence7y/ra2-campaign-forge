"""Red Alert 2 / Yuri's Revenge mission map builder.

Writes `.map` files in the modern (WAE-compatible) flavor verified against
official YR campaign maps and WorldAlteringEditor sources:

- [Preview]/[PreviewPack] dummy first (vanilla YR crashes without a preview)
- [Map] Size=0,0,W,H (diamond edge cell counts), LocalSize, Theater
- [Basic] with NextScenario chaining (campaign progression) + EndOfGame=yes on
  the campaign-ending mission; the NextScenario value is
  filled in by ra2forge.builder from the design's mission order (or from an
  explicit "next" field) and read back from disk after writing (build self-check)
- [Houses] = 14 standard countries; owners referenced by country name
- [IsoMapPack5] MiniLZO blocks of 11-byte tile records; flat clear cells
  (tile 0, level 0) are omitted entirely — the game fills them in
- [OverlayPack]/[OverlayDataPack] Format80-packed 512x512 arrays
- [Waypoints] packed as Y*1000+X
- [Structures]/[Units]/[Infantry] in the FA2/WAE field layouts
- [Triggers]/[Events]/[Actions]/[Tags]/[TaskForces]/[TeamTypes]/[ScriptTypes]

Cell coordinate system (ground truth from WAE Map.cs + official maps): the
cell grid is a parallelogram {1 <= y <= W, W+1 <= x+y <= W+H+1}; the visible
diamond is its isometric projection. Design code addresses cells by
(row, col): row in [0, W), col in [0, W) — cell(row, col) = (W + col - row,
row + 1). Square maps only.
"""

from __future__ import annotations

import base64
import struct

from .lzo import lzo1x_1_compress
from .format80 import encode as format80_encode

# tile indices valid in TEMPERATE theater (cross-checked with OpenRA ra2 tileset)
TILE_CLEAR = 0
TILE_WATER = 171

MAX_DIM = 512  # overlay array dimension (matches WAE Constants)

# The 14 standard RA2/YR house (country) entries, in canonical order.
STANDARD_HOUSES = [
    "Americans", "Alliance", "French", "Germans", "British",
    "Africans", "Arabs", "Confederation", "Russians", "YuriCountry",
    "GDI", "Nod", "Neutral", "Special",
]

# default sidebar colors per country (cross-checked with official campaign maps)
STANDARD_HOUSE_COLORS = {
    "Americans": "DarkBlue", "Alliance": "DarkBlue", "French": "DarkBlue",
    "Germans": "DarkBlue", "British": "DarkBlue",
    "Africans": "DarkRed", "Arabs": "DarkRed", "Confederation": "DarkRed",
    "Russians": "DarkRed", "YuriCountry": "Gold",
    "GDI": "Gold", "Nod": "DarkRed",
    "Neutral": "Grey", "Special": "DarkRed",
}

DUMMY_PREVIEW_SIZE = "0,0,106,61"
DUMMY_PREVIEW_PACK_1 = "yAsAIAXQ5PDQ5PDQ6JQATAEE6PDQ4PDI4JgBTAFEAkgAJyAATAG0AydEAEABpAJIA0wBVA"
DUMMY_PREVIEW_PACK_2 = "BIACcgAEwBtAMnRABAAaQCSANMAVQASAAnIABMAbQDJ0QAQAGkAkgDTAFUAEgAJyAATAG0"


class CellGrid:
    """Maps (row, col) design coordinates to diamond cell coordinates.

    Ground truth (WAE Map.cs new-map init + official maps): the file cell grid
    holds a parallelogram {1 <= y <= W, W+1 <= x+y <= W+H+1}; the on-screen
    diamond is this parallelogram under the isometric projection. Square maps
    only: cell(row, col) = (W + col - row, row + 1).
    """

    def __init__(self, width: int, height: int):
        if width != height:
            raise ValueError("only square maps are supported (width == height)")
        self.w = width
        self.h = height

    def to_cell(self, row: int, col: int) -> tuple[int, int]:
        """row in [0,W), col in [0,W) -> (x, y) cell inside the parallelogram."""
        if not (0 <= row < self.w and 0 <= col < self.w):
            raise ValueError(f"cell ({row},{col}) outside {self.w}x{self.w} map")
        return self.w + col - row, row + 1


class MissionMap:
    def __init__(self, name: str, width: int = 90, height: int = 90,
                 theater: str = "TEMPERATE"):
        if width % 2 or height % 2:
            raise ValueError("map width/height must be even")
        self.name = name
        self.w = width
        self.h = height
        self.theater = theater
        self.grid = CellGrid(width, height)
        self.water: list[tuple[int, int]] = []      # (row, col)
        self.terrain: list[tuple[int, int, str]] = []  # (row, col, tree type)
        self.smudges: list[tuple[int, int, str]] = []  # (row, col, smudge type)
        self.waypoints: dict[int, tuple[int, int]] = {}  # id -> (row, col)
        self.structures: list[dict] = []
        self.units: list[dict] = []
        self.infantry: list[dict] = []
        self.task_forces: list[dict] = []   # {name, entries:[(count, type)]}
        self.team_types: list[dict] = []    # {name, house, taskforce, script, waypoint}
        self.scripts: list[dict] = []       # {name, lines:[(action, param)]}
        self.triggers: list[dict] = []      # raw trigger dicts from triggers.py
        self.house_configs: list[dict] = []  # per-house sections (PlayerControl etc.)
        self.basic: dict[str, str] = {}
        self.next_scenario = ""
        # R5: set on the mission that ends the campaign (official final missions
        # write EndOfGame=yes, e.g. extracted/yr_maps/map_133A0CB2.map:267)
        self.end_of_game = False
        self.player_house = "Russians"

    # -- geometry helpers -------------------------------------------------
    def cell(self, row: int, col: int) -> tuple[int, int]:
        return self.grid.to_cell(row, col)

    # -- object placement -------------------------------------------------
    def add_structure(self, owner: str, type_id: str, row: int, col: int,
                      health: int = 256, facing: int = 64, tag: str = "None",
                      sellable: int = 1, rebuildable: int = 1, powered: int = 1,
                      upgrades: int = 0, spotlight: int = 0,
                      repairable: int = 1, nominal: int = 0):
        self.structures.append(dict(owner=owner, type=type_id, health=health,
                                    row=row, col=col, facing=facing, tag=tag,
                                    sellable=sellable, rebuildable=rebuildable,
                                    powered=powered, upgrades=upgrades,
                                    spotlight=spotlight, repairable=repairable,
                                    nominal=nominal))

    def add_unit(self, owner: str, type_id: str, row: int, col: int,
                 health: int = 256, facing: int = 0, mission: str = "Guard",
                 veteran: int = 0, group: int = -1):
        self.units.append(dict(owner=owner, type=type_id, health=health,
                               row=row, col=col, facing=facing, mission=mission,
                               tag="None", veteran=veteran, group=group,
                               high=0, follows=-1, auto_no=0, auto_yes=0))

    def add_infantry(self, owner: str, type_id: str, row: int, col: int,
                     sub_cell: int = 0, health: int = 256, facing: int = 0,
                     mission: str = "Guard", veteran: int = 0, group: int = -1):
        self.infantry.append(dict(owner=owner, type=type_id, health=health,
                                  row=row, col=col, sub_cell=sub_cell,
                                  mission=mission, facing=facing, tag="None",
                                  veteran=veteran, group=group, high=0,
                                  auto_no=0, auto_yes=0))

    def add_waypoint(self, wp_id: int, row: int, col: int):
        self.waypoints[wp_id] = (row, col)

    def add_water_rect(self, row0: int, col0: int, row1: int, col1: int):
        for r in range(row0, row1 + 1):
            for c in range(col0, col1 + 1):
                if 0 <= r < self.h and 0 <= c < self.w:
                    self.water.append((r, c))

    def scatter_trees(self, row0: int, col0: int, row1: int, col1: int,
                      density: float = 0.08, seed: int = 0):
        """Scatter forest terrain objects over a rect (skips water cells)."""
        import random
        rng = random.Random(seed or (row0 * 7919 + col0 * 31 + self.w))
        types = ["TREE21", "TREE31", "TREE22", "TREE04", "TREE13",
                 "TREE02", "TREE08", "TREE09", "TREE03", "TREE10"]
        for r in range(row0, row1 + 1):
            for c in range(col0, col1 + 1):
                if not (0 <= r < self.h and 0 <= c < self.w):
                    continue
                if (r, c) in set(self.water):
                    continue
                if rng.random() < density:
                    self.terrain.append((r, c, rng.choice(types)))

    def add_smudge(self, row: int, col: int, smudge_type: str):
        self.smudges.append((row, col, smudge_type))

    # -- triggers/teams ---------------------------------------------------
    def add_trigger(self, trigger: dict):
        """trigger dict from ra2forge.triggers helpers."""
        self.triggers.append(trigger)

    def add_reinforcement_team(self, team_name: str, house: str,
                               entries: list[tuple[int, str]],
                               script_lines: list[tuple[int, int]] | None = None,
                               waypoint_letter: str = "A"):
        """Registers TaskForce + TeamType + Script; returns the team name."""
        tf_name = team_name + "TF"
        script_name = team_name + "SC"
        self.task_forces.append(dict(name=tf_name, display=team_name,
                                     entries=entries))
        self.scripts.append(dict(name=script_name, display=team_name,
                                 lines=script_lines or [(0, 0)]))
        self.team_types.append(dict(name=team_name, house=house,
                                    taskforce=tf_name, script=script_name,
                                    waypoint=waypoint_letter))
        return team_name

    # -- output -----------------------------------------------------------
    def to_ini_text(self) -> str:
        out: list[str] = []
        w = out.append

        # preview must be the first sections (vanilla YR crashes otherwise)
        w("[Preview]")
        w(f"Size={DUMMY_PREVIEW_SIZE}")
        w("[PreviewPack]")
        w(f"1={DUMMY_PREVIEW_PACK_1}")
        w(f"2={DUMMY_PREVIEW_PACK_2}")
        w("")

        w("[Map]")
        w(f"Size=0,0,{self.w},{self.h}")
        w(f"Theater={self.theater}")
        w(f"LocalSize=1,1,{self.w - 2},{self.h - 2}")
        w("")

        w("[Basic]")
        w(f"Name={self.name}")
        w("Author=RA2 Campaign Forge")
        basic = self.basic
        w(f"NextScenario={self.next_scenario}")
        w("AltNextScenario=")
        w("NewINIFormat=4")
        w("CarryOverCap=0")
        w("CarryOverMoney=0.000000")
        w(f"EndOfGame={'yes' if self.end_of_game else 'no'}")
        w("SkipScore=no")
        w("OneTimeOnly=no")
        w("SkipMapSelect=no")
        w("Official=no")
        w("IgnoreGlobalAITriggers=yes")
        w("TruckCrate=no")
        w("TrainCrate=no")
        w("Percent=0")
        w("Theme=No theme")
        w(f"Player={self.player_house}")
        w("Intro=<none>")
        w("Brief=<none>")
        w("Win=<none>")
        w("Lose=<none>")
        w("Action=<none>")
        w("PostScore=<none>")
        w("PreMapSelect=<none>")
        w("TimerInherit=no")
        w("FillSilos=no")
        w("StartingDropships=0")
        w("HomeCell=0")
        w("AltHomeCell=0")
        w("MultiplayerOnly=0")
        w("TiberiumGrowthEnabled=yes")
        w("VeinGrowthEnabled=no")
        w("IceGrowthEnabled=no")
        w("TiberiumDeathToVisceroid=yes")
        w("FreeRadar=no")
        w("InitTime=10000")
        if basic.get("briefing"):
            w(f"Briefing={basic['briefing']}")
        w("")

        w("[SpecialFlags]")
        for key, val in [("Inert", "no"), ("FogOfWar", "no"), ("IonStorms", "no"),
                         ("MCVDeploy", "no"), ("Meteorites", "no"),
                         ("Visceroids", "no"), ("FixedAlliance", "no"),
                         ("TiberiumGrows", "no"), ("InitialVeteran", "no"),
                         ("HarvesterImmune", "no"), ("TiberiumSpreads", "no"),
                         ("TiberiumExplosive", "no"), ("DestroyableBridges", "yes")]:
            w(f"{key}={val}")
        w("")

        w("[Lighting]")
        for key, val in [("Red", "1.000000"), ("Blue", "1.000000"),
                         ("Green", "1.000000"), ("Level", "0.032000"),
                         ("Ground", "0.000000"), ("Ambient", "1.000000"),
                         ("IonRed", "1.000000"), ("IonBlue", "1.000000"),
                         ("IonGreen", "1.000000"), ("IonLevel", "0.032000"),
                         ("IonGround", "0.000000"), ("IonAmbient", "1.000000")]:
            w(f"{key}={val}")
        w("")

        w("[Houses]")
        for i, h in enumerate(STANDARD_HOUSES):
            w(f"{i}={h}")
        w("")

        # per-house sections — the game picks the player by PlayerControl=yes
        # and uses Country/Allies/Edge/Credits/IQ from here (format mirrors
        # official campaign maps, e.g. SOV01UMD.MAP).
        # CRITICAL: every house in [Houses] MUST have a section, otherwise
        # houses owning map objects (e.g. Neutral civilians) end up as null
        # pointers in the engine (rendering crash + trigger system death).
        configured = {hc["name"]: hc for hc in self.house_configs}
        for house in STANDARD_HOUSES:
            hc = configured.get(house, {
                "name": house, "player": False, "techlevel": 1,
                "credits": 0, "iq": 0, "edge": "North",
                "color": STANDARD_HOUSE_COLORS.get(house, "Grey"),
                "allies": house,
            })
            w(f"[{hc['name']}]")
            w(f"Country={hc['name']}")
            w(f"TechLevel={hc.get('techlevel', 10)}")
            w(f"Credits={hc.get('credits', 0)}")
            w(f"IQ={hc.get('iq', 2)}")
            w(f"Edge={hc.get('edge', 'North')}")
            w(f"PlayerControl={'yes' if hc.get('player') else 'no'}")
            w(f"Color={hc.get('color', 'DarkRed')}")
            w(f"Allies={hc.get('allies', hc['name'])}")
            w("PercentBuilt=100" if house == "Neutral" else "PercentBuilt=0")
            w("NodeCount=0")
            w("")

        # terrain
        w("[IsoMapPack5]")
        pack = self._build_iso_map_pack()
        for i, line in enumerate(_b64_lines(pack), start=1):
            w(f"{i}={line}")
        w("")

        # overlay: all-empty 512x512 arrays
        overlay = bytes([0xFF]) * (MAX_DIM * MAX_DIM)
        overlay_data = bytes(MAX_DIM * MAX_DIM)
        w("[OverlayPack]")
        for i, line in enumerate(_b64_lines(format80_encode(overlay)), start=1):
            w(f"{i}={line}")
        w("[OverlayDataPack]")
        for i, line in enumerate(_b64_lines(format80_encode(overlay_data)), start=1):
            w(f"{i}={line}")
        w("")

        w("[Waypoints]")
        for wp_id, (row, col) in sorted(self.waypoints.items()):
            x, y = self.grid.to_cell(row, col)
            w(f"{wp_id}={y * 1000 + x}")
        w("")

        if self.terrain:
            w("[Terrain]")
            for row, col, ttype in self.terrain:
                x, y = self.grid.to_cell(row, col)
                w(f"{y * 1000 + x}={ttype}")
            w("")

        if self.smudges:
            w("[Smudge]")
            for i, (row, col, stype) in enumerate(self.smudges):
                x, y = self.grid.to_cell(row, col)
                w(f"{i}={stype},{x},{y},0")
            w("")

        if self.task_forces:
            w("[TaskForces]")
            for i, tf in enumerate(self.task_forces):
                w(f"{i}={tf['name']}")
            w("")
            for tf in self.task_forces:
                w(f"[{tf['name']}]")
                w(f"Name={tf['display']}")
                for i, (count, unit) in enumerate(tf["entries"]):
                    w(f"{i}={count},{unit}")
                w("Group=-1")
                w("")

        if self.scripts:
            w("[ScriptTypes]")
            for i, sc in enumerate(self.scripts):
                w(f"{i}={sc['name']}")
            w("")
            for sc in self.scripts:
                w(f"[{sc['name']}]")
                w(f"Name={sc['display']}")
                for i, (action, param) in enumerate(sc["lines"]):
                    w(f"{i}={action},{param}")
                w("")

        if self.team_types:
            w("[TeamTypes]")
            for i, tt in enumerate(self.team_types):
                w(f"{i}={tt['name']}")
            w("")
            for tt in self.team_types:
                w(f"[{tt['name']}]")
                w(f"Name={tt['name']}")
                w("VeteranLevel=1")
                w("MindControlDecision=0")
                w("Loadable=no")
                w("Full=no")
                w("Annoyance=no")
                w("GuardSlower=no")
                w(f"House={tt['house']}")
                w("Recruiter=no")
                w("Autocreate=no")
                w("Prebuild=no")
                w("Reinforce=yes")
                w("Droppod=no")
                w("UseTransportOrigin=no")
                w("Whiner=no")
                w("LooseRecruit=no")
                w("Aggressive=no")
                w("Suicide=no")
                w("Priority=7")
                w("Max=1")
                w("TechLevel=0")
                w("Group=-1")
                w("OnTransOnly=no")
                w("AvoidThreats=no")
                w("IonImmune=no")
                w("TransportsReturnOnUnload=no")
                w("AreTeamMembersRecruitable=no")
                w("IsBaseDefense=no")
                w("OnlyTargetHouseEnemy=no")
                w(f"Waypoint={tt.get('waypoint', 'A')}")
                w(f"Script={tt['script']}")
                w(f"TaskForce={tt['taskforce']}")
                w("")

        if self.structures:
            w("[Structures]")
            for i, s in enumerate(self.structures):
                x, y = self.grid.to_cell(s["row"], s["col"])
                w(f"{i}={s['owner']},{s['type']},{s['health']},{x},{y},"
                  f"{s['facing']},{s['tag']},{s['sellable']},{s['rebuildable']},"
                  f"{s['powered']},{s['upgrades']},{s['spotlight']},"
                  f"None,None,None,{s['repairable']},{s['nominal']}")
            w("")

        if self.units:
            w("[Units]")
            for i, u in enumerate(self.units):
                x, y = self.grid.to_cell(u["row"], u["col"])
                w(f"{i}={u['owner']},{u['type']},{u['health']},{x},{y},"
                  f"{u['facing']},{u['mission']},{u['tag']},{u['veteran']},"
                  f"{u['group']},{u['high']},{u['follows']},{u['auto_no']},{u['auto_yes']}")
            w("")

        if self.infantry:
            w("[Infantry]")
            for i, inf in enumerate(self.infantry):
                x, y = self.grid.to_cell(inf["row"], inf["col"])
                w(f"{i}={inf['owner']},{inf['type']},{inf['health']},{x},{y},"
                  f"{inf['sub_cell']},{inf['mission']},{inf['facing']},"
                  f"{inf['tag']},{inf['veteran']},{inf['group']},{inf['high']},"
                  f"{inf['auto_no']},{inf['auto_yes']}")
            w("")

        triggers = [t for t in self.triggers]
        if triggers:
            w("[Triggers]")
            for t in triggers:
                w(f"{t['id']}={t['house']},{t['linked']},{t['name']},"
                  f"{t['disabled']},{t['easy']},{t['normal']},{t['hard']},0")
            w("")
            w("[Tags]")
            for t in triggers:
                w(f"{t['tag_id']}={t['repeating']},{t['tag_name']},{t['id']}")
            w("")
            w("[Events]")
            for t in triggers:
                parts = [str(len(t["events"]))]
                for ev_code, params in t["events"]:
                    parts.append(str(ev_code))
                    parts.extend(str(p) for p in params)
                w(f"{t['id']}={','.join(parts)}")
            w("")
            w("[Actions]")
            for t in triggers:
                parts = [str(len(t["actions"]))]
                for act_code, params in t["actions"]:
                    parts.append(str(act_code))
                    for p in params[:6]:
                        parts.append(str(p))
                    p7 = params[6] if len(params) > 6 else "A"
                    parts.append(str(p7))
                w(f"{t['id']}={','.join(parts)}")
            w("")

        return "\n".join(out) + "\n"

    def _build_iso_map_pack(self) -> bytes:
        buffer = bytearray()
        seen = set()
        for row, col in self.water:
            if (row, col) in seen:
                continue
            seen.add((row, col))
            x, y = self.grid.to_cell(row, col)
            buffer += struct.pack("<hhiBBB", x, y, TILE_WATER, 0, 0, 0)
        buffer += b"\x00\x00\x00\x00"  # 4-byte pad, as written by WAE

        # compress in <=8192-byte output blocks ([ushort comp][ushort raw][data])
        final = bytearray()
        pos = 0
        while pos < len(buffer):
            chunk = buffer[pos:pos + 8192]
            comp = lzo1x_1_compress(bytes(chunk))
            final += struct.pack("<HH", len(comp), len(chunk))
            final += comp
            pos += 8192
        return bytes(final)


def read_basic_section(map_text: str) -> dict[str, str]:
    """Parse the `[Basic]` section of a written .map back into a dict.

    Used by ra2forge.builder's write-then-read-back self-check: the NextScenario
    chain is asserted on the bytes that actually landed on disk, not on the
    in-memory model (a silent empty NextScenario is the FORGE-1 P0 breakage).
    """
    out: dict[str, str] = {}
    in_basic = False
    for line in map_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_basic = stripped.lower() == "[basic]"
            continue
        if not in_basic or not stripped or stripped.startswith(";"):
            continue
        key, sep, value = stripped.partition("=")
        if sep:
            out[key.strip()] = value.strip()
    return out


def _b64_lines(data: bytes, width: int = 70) -> list[str]:
    b64 = base64.b64encode(data).decode("ascii")
    return [b64[i:i + width] for i in range(0, len(b64), width)]
