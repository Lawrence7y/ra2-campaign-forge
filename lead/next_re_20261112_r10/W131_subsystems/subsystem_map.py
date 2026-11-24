#!/usr/bin/env python3
"""W131b: SUBSYSTEM MAP -- assign every function to a subsystem with explicit,
priority-ordered evidence. Milestone (3) of the whole-program RE goal.

Evidence layers (first hit wins; the layer is recorded so the call is auditable):
  L1  vtable membership -> class -> subsystem     (skips generic/template classes)
  L2  Westwood source file name -> subsystem
  L3  imported API signature -> subsystem
  L4  referenced string keywords -> subsystem
  L5  UNASSIGNED (never guessed from address alone)

Deliberate non-rules (documented so nobody re-adds them):
  * address adjacency alone is NOT used (a neighbour does not prove a subsystem)
  * generic containers (VectorClass/DynamicVectorClass/rc_ptr/...) are NOT mapped,
    because 396/988 classes are such containers and their methods belong to the
    container, not to any game subsystem.
"""
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE) + r"\W130_atlas"

SUBSYS = ["RENDER", "AUDIO", "NET", "UI", "MAP", "COMBAT", "AI_SCRIPT",
          "SAVE_CAMPAIGN", "RESOURCE_IO", "LOCOMOTION", "ENGINE_CORE",
          "WORLD_DOMINATION", "EXCEPTIONS"]

# ---------------------------------------------------------------- L1: classes
GENERIC = re.compile(
    r"(VectorClass|DynamicVectorClass|rc_ptr|TypeList|VectorCursor|CComObject|"
    r"TClassFactory|^\?\.\?AVNode|^\?\.\?AVList|Initializer|ReferenceCounted|"
    r"^\?\.\?AVCounterClass|^\.\?AVtype_info|^\.\?AVexception|bad_cast|"
    r"bad_typeid|__non_rtti_object|_com_error|^\.\?AVBase)")

CLASS_RULES = [
    # (regex on class name, subsystem)
    (r"Blit|Surface|BSurface|DSurface|XSurface|ConvertClass|LightConvert|PixelFX|"
     r"BitFont|BitText|^\.\?AVMS[A-Z]|BinkMovieHandle|MovieHandle|VQMovieHandle|"
     r"DisplayClass|Tactical|RadarClass|GScreenClass|LayerClass|"
     r"ScoreAnim|ScoreBigFont|ScoreFont|ScoreFullFont|ScorePrint|ScoreTime|"
     r"Animate|GraphicMenu|^\.\?AVAnimFile",
     "RENDER"),
    (r"WaveClass|^\.\?AVCD$|Audio|Sound|Voc", "AUDIO"),
    (r"Winsock|IPX|UDP|NullModem|WinModem|Dial8|ConnMan|Connection|CommBuffer|"
     r"LinkClass|WebBrowser|CNetUtilEventSink|CChatEventSink|CDownloadEventSink|"
     r"Multiplayer|PlayerProfile|WonlineStringDialogControl|SimpleWonlineDialogControl",
     "NET"),
    (r"ControlClass|Gadget|Gauge|Slider|^\.\?AVEdit|DropList|CheckList|ColorList|"
     r"^\.\?AVListClass|ScrollClass|TabClass|Sidebar|SBGadget|SelectClass|"
     r"ShapeButton|TextButton|StaticButton|TextLabel|ToggleClass|ToolTip|"
     r"Mouse|Cursor|CommandClass|DialogControl|OwnerDraw",
     "UI"),
    (r"CellClass|^\.\?AVMap|IsometricTile|WaypointPath|^\.\?AVTerrain|"
     r"^\.\?AVOverlay|^\.\?AVTube|MapSeed|RadSite|LightSource",
     "MAP"),
    (r"^\.\?AV(Object|Techno|Foot|Building|Unit|Infantry|Aircraft|Bullet|Anim|"
     r"Particle|VoxelAnim|Smudge|Bomb|DiskLaser|EMPulse|Parasite|Temporal|"
     r"VeinholeMonster|BuildingLight|AlphaShape|FoggedObject|Tiberium|"
     r"WarheadType|WeaponType|Wave|Factory|Power|CaptureManager|SlaveManager|"
     r"SpawnManager|Airstrike|Super|House|Side|Flasher|Bounce)",
     "COMBAT"),
    (r"Script|Team|TaskForce|Trigger|TAction|TEvent|TagClass|TagType|Neuron|"
     r"BrainClass|Mission|AITrigger", "AI_SCRIPT"),
    (r"Campaign|Carryover|StageClass|ProgressScreen|LoadOptions|LoadProgressMgr|"
     r"^\.\?AVScore", "SAVE_CAMPAIGN"),
    (r"FileClass|^\.\?AVINIClass|CCINIClass|INIEntry|INISection|MixFileClass|"
     r"Straw|^\.\?AVPipe|LCWPipe|LZOPipe|PKPipe|SHAPipe|BlowPipe|CacheStraw|"
     r"RandomStraw", "RESOURCE_IO"),
    (r"Locomotion", "LOCOMOTION"),
    (r"WorldDominationTour|WDTState|WDTTerritory|FactionSelectDialogControl|"
     r"MapSizeGameOption|FlagGameOption|ValueGameOption|GameOption@",
     "WORLD_DOMINATION"),
    (r"ApplicationClass|LogicClass|VersionClass", "ENGINE_CORE"),
    # SwizzleManagerClass = pointer relocation for object tables (save-load / any
    # table that moves). NOT rendering: 0x006CF240 is the push used by the bullet
    # container (ledger §3'1), which is a swizzle-managed pointer array.
    (r"Swizzle", "ENGINE_CORE"),
]


def class_subsys(cls):
    if GENERIC.search(cls):
        return None
    for rx, sub in CLASS_RULES:
        if re.search(rx, cls):
            return sub
    return None


# ------------------------------------------------- L2: Westwood source modules
MODULE_RULES = [
    (r"wonline|netdlg|netshare|netutil|Connect\.CPP|Session\.CPP|WOLPersona|"
     r"ModemHst|ModemGst|SerialEd|PhoneEd|SendFile|MPCoop|MPSiegeTeam|Skirmish|"
     r"WOL", "NET"),
    (r"Scenario|House\.CPP|Infantry\.CPP|AbsType|Unit|Aircraft|Building|Weapon|"
     r"Bullet|Warhead|Anim|Particle|Overlay|Terrain|Smudge|Dropship",
     "COMBAT"),
    (r"MapGen|MapSel|Cell|Iso|Tube|Waypoint|LdPrgMgr", "MAP"),
    (r"Sidebar|UICmnds|GDlgSupp|NullDlg|GameDlg|LoadDlg|WDTSel|OwnrDraw|"
     r"Control|Gadget|ToolTip|Mouse|wwmous|Command", "UI"),
    (r"Ini\.CPP|Init\.CPP|Mix|File|Straw|Pipe|Lzo|Lcw|Pk|Sha|Blow", "RESOURCE_IO"),
    (r"CampScor|Credits|Carryover|Score", "SAVE_CAMPAIGN"),
    (r"Ion\.CPP|Super|Trigger|Team|Script|Mission|AI", "AI_SCRIPT"),
    (r"Display|Draw|Blit|Surface|Font|Voxel|Tactical|Radar", "RENDER"),
    (r"Audio|Sound|Voc|Wav|Bink", "AUDIO"),
]


def module_subsys(mod):
    m = mod.rsplit("\\", 1)[-1]
    for rx, sub in MODULE_RULES:
        if re.search(rx, m, re.I):
            return sub
    return None


# --------------------------------------------------------- L3: import groups
IMPORT_RULES = [
    (r"DirectDraw|^Blit|SetPixel|StretchBlt|CreateDIBSection|TextOut|"
     r"GetDeviceCaps|SetBkMode|SelectObject|CreateFont|GetStockObject|"
     r"DeleteObject|SetViewport|ModifyWorldTransform|SaveDC|RestoreDC", "RENDER"),
    (r"DirectSound|^Bink|PlaySound|waveOut|sndPlaySound|mixer", "AUDIO"),
    (r"^WSA|socket|connect|send|recv|gethostby|inet_|select$|"
     r"FindWindow|wsprintf", "NET"),
    (r"CreateWindowEx|RegisterClass|MessageBox|DialogBox|SendMessage|"
     r"PostMessage|GetDlgItem|SetWindowLong|GetWindowLong|SetTimer|KillTimer|"
     r"ShowWindow|EnableWindow|SetFocus|GetCursorPos|SetCursor|"
     r"GetAsyncKeyState|SetCapture|ReleaseCapture|InvalidateRect|UpdateWindow|"
     r"BeginPaint|EndPaint|GetClientRect|ClientToScreen|ScreenToClient", "UI"),
    (r"RegOpenKey|RegQueryValue|RegSetValue|RegCreateKey|RegCloseKey|"
     r"RegEnumKey|RegDelete", "RESOURCE_IO"),
    (r"CreateFile|ReadFile|WriteFile|FindFirstFile|FindNextFile|FindClose|"
     r"GetFileSize|SetFilePointer|SetEndOfFile|CreateDirectory|GetTempFileName|"
     r"CopyFile|DeleteFile|CreateFileMapping|MapViewOfFile|HeapCreate|"
     r"VirtualAlloc|VirtualFree|GlobalAlloc|GlobalFree", "RESOURCE_IO"),
]

STRING_RULES = [
    (r"DDRAW|DirectDraw|\.shp|\.vxl|\.pal|palette|blit|surface|voxel|cameo|"
     r"\.pcx|\.tga|resolution|windowed", "RENDER"),
    (r"\.wav|\.voc|\.aud|sound|audio|music|BINK|\.bik|volume|stereo",
     "AUDIO"),
    (r"wol|WOL|winsock|IPX|modem|TCP|UDP|connection|socket|server|"
     r"game server|ping|latency|serial", "NET"),
    (r"TXT_|dialog|button|checkbox|scroll|tooltip|sidebar|menu|Dialog|"
     r"Tool ?Tip|gadget|cursor", "UI"),
    (r"scenario|Scenario|\.map|\.mpr|\.yrm|isometric|tile|terrain|overlay|"
     r"cell|waypoint", "MAP"),
    (r"weapon|weapon|warhead|damage|armor|bullet|infantry|vehicle|building|"
     r"harvester|unit |aircraft|veteran|elite", "COMBAT"),
    (r"trigger|team|script|mission|AI |aistrike|taskforce|tag", "AI_SCRIPT"),
    (r"save|load game|carryover|campaign|score|\.sav", "SAVE_CAMPAIGN"),
    (r"\.mix|\.ini|MIX|rulesmd|artmd|\.csf|load file|csf", "RESOURCE_IO"),
]


def import_subsys(imp):
    if not imp:
        return None
    for rx, sub in IMPORT_RULES:
        if re.search(rx, imp):
            return sub
    return None


def string_subsys(strings):
    if not strings:
        return None
    votes = collections.Counter()
    for s in strings.split(" | "):
        if not s:
            continue
        for rx, sub in STRING_RULES:
            if re.search(rx, s):
                votes[sub] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]


# --------------------------------------------------------------------- main
def main():
    atlas = os.path.join(SRC, "function_atlas.tsv")
    fns = []
    with io.open(atlas, encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            fns.append(dict(zip(hdr, p)))
    print("functions: %d" % len(fns))

    # L1: function -> class set (from W131 vtable membership)
    fn_classes = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "fn_class.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            entry = int(p[0], 16)
            for c in p[1].split(","):
                if c:
                    fn_classes[entry].add(c)

    # L2: function -> source modules
    fn_mods = collections.defaultdict(set)
    with io.open(os.path.join(SRC, "module_attribution.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            entry = int(p[0], 16)
            for m in p[3].split(","):
                if m:
                    fn_mods[entry].add(m)

    out = []
    stat = collections.Counter()
    sub_fns = collections.Counter()
    sub_bytes = collections.Counter()
    sub_range = {}
    for r in fns:
        entry = int(r["entry"], 16)
        size = int(r["size"])
        sub = None
        why = None

        # L1
        votes = collections.Counter()
        for c in fn_classes.get(entry, ()):
            s = class_subsys(c)
            if s:
                votes[s] += 1
        if votes:
            sub = votes.most_common(1)[0][0]
            why = "L1:vtable-class"
        # L2
        if sub is None:
            v2 = collections.Counter()
            for m in fn_mods.get(entry, ()):
                s = module_subsys(m)
                if s:
                    v2[s] += 1
            if v2:
                sub = v2.most_common(1)[0][0]
                why = "L2:source-module"
        # L3
        if sub is None:
            s = import_subsys(r.get("first_import", ""))
            if s:
                sub, why = s, "L3:import"
        # L4
        if sub is None:
            s = string_subsys(r.get("strings", ""))
            if s:
                sub, why = s, "L4:string"
        if sub is None:
            sub, why = "UNASSIGNED", "-"

        stat[why] += 1
        if sub != "UNASSIGNED":
            sub_fns[sub] += 1
            sub_bytes[sub] += size
            lo, hi = sub_range.get(sub, (entry, entry))
            sub_range[sub] = (min(lo, entry), max(hi, entry))
        out.append((entry, size, sub, why, r.get("n_callers", "0")))

    with io.open(os.path.join(HERE, "fn_subsystem.tsv"), "w", encoding="utf-8") as f:
        f.write("entry\tsize\tsubsystem\tevidence\tn_callers\n")
        for e, s, sub, why, nc in out:
            f.write("0x%08X\t%d\t%s\t%s\t%s\n" % (e, s, sub, why, nc))

    tot_bytes = sum(s for _e, s, _sub, _w, _c in out)
    assigned = sum(v for k, v in stat.items() if not k.startswith("-"))
    print("\n=== evidence layer usage ===")
    for k, v in stat.most_common():
        print("  %-22s %d" % (k, v))
    print("\nassigned %d/%d functions (%.1f%%); bytes %d/%d (%.1f%%)"
          % (assigned, len(out), 100.0 * assigned / len(out),
             sum(sub_bytes.values()), tot_bytes,
             100.0 * sum(sub_bytes.values()) / tot_bytes))

    print("\n=== subsystem table ===")
    rows = []
    for sub in SUBSYS:
        if sub_fns[sub] == 0:
            continue
        lo, hi = sub_range[sub]
        rows.append({"subsystem": sub, "n_functions": sub_fns[sub],
                     "n_bytes": sub_bytes[sub], "addr_lo": "0x%08X" % lo,
                     "addr_hi": "0x%08X" % hi})
        print("  %-17s fn=%-5d bytes=%-9d 0x%08X..0x%08X"
              % (sub, sub_fns[sub], sub_bytes[sub], lo, hi))
    json.dump({"subsystems": rows,
               "evidence": dict(stat),
               "coverage": {"assigned_functions": assigned,
                            "total_functions": len(out),
                            "assigned_bytes": sum(sub_bytes.values()),
                            "total_bytes": tot_bytes}},
              open(os.path.join(HERE, "subsystem_map.json"), "w"), indent=1)
    with io.open(os.path.join(HERE, "subsystems.tsv"), "w", encoding="utf-8") as f:
        f.write("subsystem\tn_functions\tn_bytes\taddr_lo\taddr_hi\n")
        for r in rows:
            f.write("%s\t%d\t%d\t%s\t%s\n" % (r["subsystem"], r["n_functions"],
                                              r["n_bytes"], r["addr_lo"], r["addr_hi"]))
    print("\nwrote fn_subsystem.tsv / subsystems.tsv / subsystem_map.json")


if __name__ == "__main__":
    main()
