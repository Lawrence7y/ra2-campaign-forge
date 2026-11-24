# -*- coding: utf-8 -*-
"""
classify.py v2 — 证据驱动的子系统切分 (基于 12,916 函数 atlas @2026-11-15 11:47)
证据优先级:
  P0a assert __FILE__ 路径字符串 → 西木源文件 → 子系统          [高]
  P1  虚表槽归属(vtable class) → 类名规则                        [高]
  P2  导入 API 指纹(排除 CRT 区间)                               [高/中]
  P3  字符串规则(有序首中) + CRT 区间规则                          [高/中/低]
  P4  调用图传播(已归类邻边>=70%多数, 排除 Crt/Runtime 票)         [中]
  P5  地址簇填充(gap>=512, dom>=0.75, 多数>=5, 排除 CRT 票)        [低/中]
未匹配 → UNASSIGNED。
"""
import json, re
from collections import Counter, defaultdict

ATLAS_DIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas"
OUT = ATLAS_DIR + r"\glm_seg"
CRT_LO = 0x7C8900            # .text 内 MSVC CRT 区域起点(字符串指纹证实)

SS = [
 "Main_Init_Flow", "Menus_Main_Intro", "Render_DDraw_Display", "Graphics_Blit_Shape",
 "Video_Bink", "Audio_Sound_Music", "Text_Language_Table", "File_Mix_FS",
 "File_Stream_Crypto", "Config_Registry", "Net_Transport", "MP_Lobby_Session",
 "WOL_Online", "WDT_WorldDom", "UI_Gadget_Dialog", "Input_Commands_Mouse",
 "Sidebar_Radar_HUD", "Tactical_MapView", "GameObj_Logic", "Ini_Rules_DB",
 "AI_Team_Script", "Movement_Locomotion", "Scenario_Map", "SaveLoad",
 "Superweapon_Special", "Campaign_Meta", "Misc_Util_Mem", "Crt_Runtime", "UNASSIGNED"]

FILE2SS = {
 "abstype.cpp":"Ini_Rules_DB","ini.cpp":"Ini_Rules_DB",
 "beacon.cpp":"GameObj_Logic","conquer.cpp":"GameObj_Logic","house.cpp":"GameObj_Logic",
 "infantry.cpp":"GameObj_Logic","unit.cpp":"GameObj_Logic","power.cpp":"Sidebar_Radar_HUD",
 "queue.cpp":"Sidebar_Radar_HUD","radar.cpp":"Sidebar_Radar_HUD","sidebar.cpp":"Sidebar_Radar_HUD",
 "campscor.cpp":"Campaign_Meta","mpscore.cpp":"Campaign_Meta","dropship.cpp":"Campaign_Meta",
 "cd.cpp":"File_Mix_FS","connect.cpp":"Net_Transport","sendfile.cpp":"Net_Transport",
 "modemgst.cpp":"Net_Transport","modemhst.cpp":"Net_Transport","nullmgr.cpp":"Net_Transport",
 "event.cpp":"Net_Transport",
 "multiplayer.cpp":"MP_Lobby_Session","session.cpp":"MP_Lobby_Session",
 "netshare.cpp":"MP_Lobby_Session","netdlg.cpp":"MP_Lobby_Session","netdlg2.cpp":"MP_Lobby_Session",
 "mplayer.cpp":"MP_Lobby_Session","mpcoop.cpp":"MP_Lobby_Session","mpobserver.cpp":"MP_Lobby_Session",
 "mpsiegeteam.cpp":"MP_Lobby_Session","mschoice.cpp":"MP_Lobby_Session","skirmish.cpp":"MP_Lobby_Session",
 "mapsel.cpp":"MP_Lobby_Session","gdlgsupp.cpp":"MP_Lobby_Session",
 "nulldlg.cpp":"MP_Lobby_Session","serialed.cpp":"MP_Lobby_Session","phoneed.cpp":"MP_Lobby_Session",
 "coopcamp.cpp":"MP_Lobby_Session",
 "wonline.cpp":"WOL_Online","wolpersonainformation.cpp":"WOL_Online",
 "worlddom.cpp":"WDT_WorldDom","wdtsel.cpp":"WDT_WorldDom","wdtgameoptions.cpp":"WDT_WorldDom",
 "wdtprops.cpp":"WDT_WorldDom","wdtterr.cpp":"WDT_WorldDom",
 "gamedlg.cpp":"UI_Gadget_Dialog","options.cpp":"UI_Gadget_Dialog","tooltip.cpp":"UI_Gadget_Dialog",
 "uicmnds.cpp":"Input_Commands_Mouse","wwmous.cpp":"Input_Commands_Mouse",
 "ownrdraw.cpp":"Menus_Main_Intro","credits.cpp":"Menus_Main_Intro","egos.cpp":"Menus_Main_Intro",
 "init.cpp":"Main_Init_Flow","startup.cpp":"Main_Init_Flow","mainloop.cpp":"Main_Init_Flow",
 "ion.cpp":"Superweapon_Special","super.cpp":"Superweapon_Special",
 "display.cpp":"Render_DDraw_Display","tactical.cpp":"Tactical_MapView",
 "scenario.cpp":"Scenario_Map","mapgen.cpp":"Scenario_Map","taction.cpp":"Scenario_Map",
 "loaddlg.cpp":"SaveLoad","ldprgmgr.cpp":"SaveLoad","restate.cpp":"SaveLoad",
 "planmgr.cpp":"AI_Team_Script",
}

VT_RULES = [
 (r"Straw|Pipe\b|Base64|Blow|LCW|LZO|\bPK\b|SHA|XOR", "File_Stream_Crypto"),
 (r"RawFile|BufferIO|FileClass|CCFile|CDFile|Cache|MixFile", "File_Mix_FS"),
 (r"IPX|Winsock|UDPInterface|NullModem|Connection", "Net_Transport"),
 (r"Locomotion|WaypointPath", "Movement_Locomotion"),
 (r"Team|TaskForce|Script|AITrigger|Neuron", "AI_Team_Script"),
 (r"Trigger|Tag|TEvent|TAction", "Scenario_Map"),
 (r"Gadget|Control|Dialog|Gauge|Button|List|Edit|Static|ToolTip|MetaClass", "UI_Gadget_Dialog"),
 (r"Sidebar|Radar", "Sidebar_Radar_HUD"),
 (r"Mouse|Cursor", "Input_Commands_Mouse"),
 (r"Theme|Sound|Voc|Speech|Audio", "Audio_Sound_Music"),
 (r"Bink|Movie", "Video_Bink"),
 (r"Surface|Blit|LightConvert|AlphaShape|Font", "Graphics_Blit_Shape"),
 (r"Session|Campaign|Score", "Campaign_Meta"),
 (r"Scenario", "Scenario_Map"),
 (r"INI\b|IniClass", "Ini_Rules_DB"),
 (r"Tactical", "Tactical_MapView"),
 (r"WOL|Chat", "WOL_Online"),
 (r"VectorClass|DynamicVectorClass|StackClass|QueueClass|IndexClass|HashClass|IndexListClass|PointerClass|Array",
   "Misc_Util_Mem"),
 (r"TypeClass", "Ini_Rules_DB"),          # 剩余 *TypeClass → 规则/类型库
 (r"Object|Techno|Unit|Infantry|Building|Aircraft|Foot|Cell|Anim|Overlay|Smudge|Terrain|Tiberium|Voxel|Wave|Tube|Bullet|Warhead|Bomb|Parasite|Slave|Capture|Fogged|RadSite|LightSource|BuildingLight|DiskLaser|EMPulse|Temporal|Airstrike|Super|Factory|Mission|Radio|Particle|IsometricTile|Beacon|House|Player|Veinhole|Spawn|Emp|Wave",
   "GameObj_Logic"),
]

IMP_RULES = [
 ("DirectDrawCreate", "Render_DDraw_Display", "高"),
 ("Bink",             "Video_Bink",           "高"),
 ("DirectSound",      "Audio_Sound_Music",    "高"),
 ("waveOut",          "Audio_Sound_Music",    "中"),
 ("mciSend",          "Audio_Sound_Music",    "中"),
 ("WSOCK32!",         "Net_Transport",        "高"),
 ("RegOpenKey|RegCloseKey|RegQueryValue|RegCreateKey|RegSetValue|RegQueryInfoKey|RegEnumKey|RegDeleteKey",
                      "Config_Registry",      "高"),
 ("FindFirstFile|FindNextFile|FindClose|CreateFile|SetFilePointer|ReadFile|WriteFile|DeleteFile|SetCurrentDirectory|GetCurrentDirectory|GetDriveType|GetDiskFreeSpace|GetVolumeInformation",
                      "File_Mix_FS",          "中"),
 ("CoCreateInstance|OleRun|OleSaveToStream|StgCreateDocfile|CoTaskMem|PropVariant|OleInitialize|OleUninitialize|CoFreeUnusedLibraries",
                      "WOL_Online",           "中"),
 ("ImageList",        "WOL_Online",           "中"),
 ("ImmGet",           "UI_Gadget_Dialog",     "中"),
]

STR_RULES = [
 (r"LC_[A-Z]+|1#SNAN|1#IND|__LIBDATA|typeid of NUL|dynamic_cast", "Crt_Runtime", "高"),
 (r"DDRAW\.DLL|Direct X", "Render_DDraw_Display", "高"),
 (r"Bink|RENEGADE\.BIK|\.BIK\b", "Video_Bink", "高"),
 (r"WSOCK|Winsock|mangler1\.westwood|Packet Loss|Rtry delta|FSPS|Multicast|PortPool|PortBase|IPX",
   "Net_Transport", "高"),
 (r"taunts\\|Invalid Voc|\.VOC\b|\.AUD\b|EVA Stream|Sound bank|Music Stream|AUDIOMD\.MIX|AUDIO\.MIX|SOUNDS?\.MIX|Audio Stream|Taunt Stream|THEME",
   "Audio_Sound_Music", "高"),
 (r"Themes|No theme|Repeating", "Audio_Sound_Music", "高"),
 (r"wolinfoMD|WOLAPI|WOL:|DefaultPersona|ob_41_|wolhost|wolacpt|TXT_CANT_CONNECT|TXT_JOINLOB|TXT_YOURE_DISCON|AllowPage|LangFilter|LobMusic|HTMLPath|BadPage|frame\.htm",
   "WOL_Online", "高"),
 (r"SOFTWARE\\Westwood", "Config_Registry", "中"),
 (r"\.MIX\b", "File_Mix_FS", "高"),
 (r"coopsave|loadmd\.MIX|LOADMD\.MIX|LOAD\.MIX|SaveGame|SAVEGAME|GAME\.SAV", "SaveLoad", "高"),
 (r"IsoMapPack|OverlayPack|CellTags|TXT_RANDOM_MAP|RandMap|MapGen|\[Map\]|PreviewPack", "Scenario_Map", "高"),
 (r"AITrigger|TeamTypes|TaskForces|ScriptTypes|NoThreat|Zombie|MindControlDecision", "AI_Team_Script", "高"),
 (r"LANGRULE\.INI|ColorAdd|SpecialWeapons|Countries|UIName|Prerequisite|LandTargeting|NavalTargeting|SpeedType|CanBeHidden|TypeImmune|WalkRate|ContentScan|Buildup|Cameo|BehavesLike|Railgun|CellSpread|CellInset|PercentAtMax|CausesDelayKill|DelayKillFrames|IsVeinhole|WaterBound|SpawnsTiberium|IsFlammable|Foundation|Landable|AirportBound|Carryall|Rotors|BARRACKS|POWER\b|FACTORY\b|CrateTrigger|Explodes|ElevationModel|ElevationIncrement|WallModel",
   "Ini_Rules_DB", "高"),
 (r"STT:MainButton|CREDITSMD|dbak6440|gdii\.pcx|nodi\.pcx|rani\.pcx|usai\.pcx|japi\.pcx|mpascrnlbar", "Menus_Main_Intro", "中"),
 (r"Semi-persistant|Volatile\b|VariableNames|Waypoints\b", "Scenario_Map", "中"),
 (r"\.SHP\b|\.SHA\b", "Graphics_Blit_Shape", "中"),
 (r"\.PCX\b", "Graphics_Blit_Shape", "中"),
 (r"\.WAV\b", "Audio_Sound_Music", "中"),
 (r"AMBIENT|VIOLENT|LOWEST", "Audio_Sound_Music", "中"),
 (r"MOUSE\.SHA|KEYBOARDMD", "Input_Commands_Mouse", "高"),
  (r"GUI:", "MP_Lobby_Session", "中"),
 (r"<Player @ |Sending observer slot|Looking for %s|GAPLUG|Forcing House|@Open@|@Closed@|@EasyAI@|@MediumAI@|MinPlayers|MaxPlayers|GameMode|No Digest|\[Digest\]|MAPSELMD\.INI|TextRect|FreeForAll|Unholy|ManBattle",
   "MP_Lobby_Session", "中"),
 (r"SYNC%01d", "Net_Transport", "中"),
 (r"%d\.%d\.%d\.%d", "Net_Transport", "中"),
 (r"Ra2ts_s|Ra2ts_l|PENGO|THETEAM", "Net_Transport", "中"),
 (r"MapViewOfFile|48BC11BD|D6E7FC97", "WOL_Online", "中"),
 (r"TXT_QUEUE_FULL|SELL\.SHP|GCLOCK|DARKEN\.SHP|SIDEGDI|EVA_ConstructionComplete|EVA_Canceled|EVA_SelectTarget|EVA_OnHold|EVA_NewConstructionOption|Cost: N/A|Cost: %d",
   "Sidebar_Radar_HUD", "中"),
 (r"TXT_KILLS_COLON|TXT_NAME_COLON", "Sidebar_Radar_HUD", "中"),
 (r"WDT|WorldDom|TerritorySelect", "WDT_WorldDom", "高"),
 (r"CLSID\\|WW\.TiberianSun", "WOL_Online", "高"),
 (r"PrivateKey|PublicKey|Bootstrap\.\.\.", "Net_Transport", "中"),
 (r"Sunday|Monday|January|February|SunMonTueWed", "Crt_Runtime", "高"),
 (r"RA2MD\.INI", "Main_Init_Flow", "中"),
 (r"shroud|Shroud", "Tactical_MapView", "中"),
 (r"BeginMovie|EndMovie|subtitlemd|\.VQA", "Video_Bink", "中"),
 (r"MultiMissile|IronCurtain|PsychicDominator|LightningStorm", "Superweapon_Special", "高"),
 (r"AlliedLoad|SovietLoad", "Campaign_Meta", "中"),
 (r"Winner|Loser", "Campaign_Meta", "中"),
 (r"ActiveRect|HighlightSound", "UI_Gadget_Dialog", "中"),
 (r"String Manager failed|MISSING:'%hs'", "Text_Language_Table", "高"),
 (r"Scenario\b", "Scenario_Map", "中"),
 (r"ToolTip|Tip:", "UI_Gadget_Dialog", "中"),
 (r"AttackMove", "Input_Commands_Mouse", "低"),
 (r"ScrollBar|ListBox|ComboBox|msctls_", "UI_Gadget_Dialog", "低"),
 (r"VarFileInfo|StringFileInfo|VERSION\.TXT", "Misc_Util_Mem", "低"),
 (r"%%0%dd|%02x %02x", "Misc_Util_Mem", "低"),
 (r"SYSTEM MEMORY|CPU: %d Mhz|VRAM reported|RAM reported", "Main_Init_Flow", "高"),
 (r"InfantryTypes|VehicleTypes|AircraftTypes|BuildingTypes|Colors\b", "Ini_Rules_DB", "高"),
 (r"Animations|VoxelAnims|Particles\b|ParticleSystems|Powerups", "Ini_Rules_DB", "高"),
 (r"<random>", "Ini_Rules_DB", "低"),
 (r"Taunt_%d", "WOL_Online", "中"),
 (r"StructureTab|DefenseTab", "UI_Gadget_Dialog", "低"),
 (r"StartX|StartY", "Scenario_Map", "中"),
 (r"QUEUED_INTERRUPT", "Audio_Sound_Music", "中"),
 (r"ObserverMode|Preview\.bin", "MP_Lobby_Session", "高"),
 (r"bleep1", "MP_Lobby_Session", "中"),
 (r"PageUser", "WOL_Online", "中"),
 (r"LightGrey", "Sidebar_Radar_HUD", "低"),
 (r"GAME\.FNT", "Graphics_Blit_Shape", "中"),
 (r"%sSounds", "GameObj_Logic", "中"),
 (r"Cheer\b", "Input_Commands_Mouse", "低"),
 (r"EVA_", "GameObj_Logic", "低"),
 (r"TXT_", "UI_Gadget_Dialog", "低"),
]

# 区间种子: 局部证据充分的小区域 (P3 级, 先于 P4/P5, 不被 P2 覆盖)
REGION_SEEDS = [
 (0x403ED0, 0x409E00, "Audio_Sound_Music",  "中"),   # 音频引擎: Audio Stream/AUDIOMD.MIX/AMBIENT/VIOLENT/LOWEST
 (0x505180, 0x510A20, "MP_Lobby_Session",   "中"),   # MP 会话初始化: <Player @>/GAPLUG/Forcing House
 (0x720590, 0x721300, "Audio_Sound_Music",  "中"),   # 主题引擎: Themes/Music Stream/No theme/Repeating
 (0x752290, 0x754800, "Audio_Sound_Music",  "中"),   # 语音引擎: EVA Stream/Taunt Stream/QUEUE/INTERRUPT
 (0x734120, 0x735180, "Text_Language_Table", "中"),   # 字符串管理器: FATAL/MISSING + 0x734E60 入度1073
 (0x7C5BC0, 0x7C8900, "Misc_Util_Mem",       "中"),   # 内存/串原语: 0x7C5F00 入度543, 无导入
 (0x7BD690, 0x7C39B8, "Video_Bink",          "低"),   # Bink 播放辅助: 被 Video_Bink 调用 20 边, 自封闭
 (0x7B2DB0, 0x7B4170, "Misc_Util_Mem",       "低"),   # 格式化/调试辅助(%%0%dd, %02x)
 (0x7B57A0, 0x7B90B6, "Misc_Util_Mem",       "低"),   # 格式化/调试辅助
 (0x7BA420, 0x7BA8BD, "Input_Commands_Mouse","低"),   # wwmous.cpp 游标区
]

# ---------------- 载入 ----------------
funcs = []
with open(ATLAS_DIR + r"\function_atlas.tsv", encoding="utf-8") as f:
    f.readline()
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 8: continue
        funcs.append({"entry": int(c[0], 16), "size": int(c[1]), "n_callers": int(c[3]),
                      "n_callees": int(c[4]), "is_fnptr": int(c[5]),
                      "strings": c[8] if len(c) > 8 else ""})
funcs.sort(key=lambda d: d["entry"])
N = len(funcs)
TOT_B = sum(f["size"] for f in funcs)
print("atlas rows: %d  total bytes: %d" % (N, TOT_B))
ev = {int(k): v for k, v in json.load(open(OUT + r"\evidence.json")).items()}
assert len(ev) == N, "evidence/atlas mismatch: %d vs %d" % (len(ev), N)

assign = {}
PRIO = {"P0a":0, "P1":1, "P2":2, "P3":3, "P4":4, "P5":5}
def put(e, ss, kind, conf, detail):
    if ss is None or ss not in SS: ss = "UNASSIGNED"
    old = assign.get(e)
    if old is not None and PRIO.get(old[1].split("+")[0], 9) <= PRIO.get(kind.split("+")[0], 9):
        return
    assign[e] = (ss, kind, conf, detail)

# ---- P0a 源文件 ----
attr = {}
with open(ATLAS_DIR + r"\module_attribution.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) >= 4 and c[0].startswith("004"):
            attr[int(c[0], 16)] = c[3].replace("D:\\ra2mdpost\\", "")
for f in funcs:
    src = None
    if f["entry"] in attr: src = attr[f["entry"]]
    else:
        m = re.search(r"ra2mdpost\\([A-Za-z0-9_]+)\.\w+", f["strings"])
        if m: src = m.group(1) + ".cpp"
    if not src: continue
    tgt = FILE2SS.get(src.lower())
    if tgt: put(f["entry"], tgt, "P0a+module", "高", "src=" + src)
    elif re.match(r"^wdt", src, re.I): put(f["entry"], "WDT_WorldDom", "P0a+module", "高", "src=" + src)

# ---- P1 虚表 ----
for f in funcs:
    if f["entry"] in assign: continue
    vcs = ev.get(f["entry"], {}).get("vclasses", [])
    if not vcs: continue
    name = re.sub(r"^\.?\?\?[ACV]", "", vcs[0]).split("@@")[0]
    for pat, ss in VT_RULES:
        if re.search(pat, name):
            put(f["entry"], ss, "P1+vtable", "高", "vt=" + name); break

# ---- P2 导入 ----
for f in funcs:
    e = f["entry"]
    if e in assign or e >= CRT_LO: continue
    imps = ev.get(e, {}).get("imports", [])
    if not imps: continue
    blob = "|".join(imps)
    for pat, ss, conf in IMP_RULES:
        if re.search(pat, blob):
            put(e, ss, "P2+import", conf, "imp=" + imps[0]); break

# ---- P3 区间 + 字符串 ----
for f in funcs:
    e = f["entry"]
    if e >= CRT_LO:
        put(e, "Crt_Runtime", "P3+region", "高", "range>=0x7C8900"); continue
    for lo, hi, ss, conf in REGION_SEEDS:
        if lo <= e < hi:
            put(e, ss, "P3+region", conf, "region %08X-%08X" % (lo, hi)); break
    if e in assign: continue
    for s in re.split(r" \| ", f["strings"]):
        for pat, ss, conf in STR_RULES:
            if re.search(pat, s):
                put(e, ss, "P3+string", conf, "str=" + s[:40]); break
        if e in assign: break

# ---- P4 调用图传播 ----
callers = defaultdict(list)
for e, d in ev.items():
    for c in d.get("callees", []): callers[c].append(e)
NO_SPREAD = {"Crt_Runtime", "UNASSIGNED"}
for rnd in range(4):
    grew = 0
    for f in funcs:
        e = f["entry"]
        if e in assign: continue
        votes = Counter()
        for c in ev.get(e, {}).get("callees", []):
            a = assign.get(c)
            if a and a[0] not in NO_SPREAD: votes[a[0]] += 1
        for p in callers.get(e, []):
            a = assign.get(p)
            if a and a[0] not in NO_SPREAD: votes[a[0]] += 1
        if not votes: continue
        ss, n = votes.most_common(1)[0]
        tot = sum(votes.values())
        if tot >= 3 and n / tot >= 0.70:
            put(e, ss, "P4+callgraph", "中", "vote=%d/%d r%d" % (n, tot, rnd)); grew += 1
    print("P4 round %d: +%d" % (rnd, grew))
    if grew == 0: break

# ---- P5 地址簇填充 ----
clusters, cur = [], [funcs[0]]
for a, b in zip(funcs, funcs[1:]):
    if b["entry"] - (a["entry"] + a["size"]) >= 512:
        clusters.append(cur); cur = []
    cur.append(b)
clusters.append(cur)
grew5 = 0
for cl in clusters:
    if len(cl) < 4: continue
    votes = Counter()
    for f in cl:
        a = assign.get(f["entry"])
        if a and a[0] not in NO_SPREAD: votes[a[0]] += 1
    if not votes: continue
    ss, n = votes.most_common(1)[0]
    nass = sum(votes.values())
    if ss in NO_SPREAD: continue
    dom = n / nass
    if dom >= 0.75 and n >= 5:
        conf = "中" if (dom >= 0.85 and len(cl) >= 20) else "低"
        for f in cl:
            if f["entry"] not in assign:
                put(f["entry"], ss, "P5+cluster", conf,
                    "cluster %d/%d@%08X" % (n, nass, cl[0]["entry"])); grew5 += 1
print("P5 cluster fill: +%d" % grew5)

# ---------------- 输出 ----------------
ass_n = len(assign)
ass_b = sum(f["size"] for f in funcs if f["entry"] in assign)
print("assigned %d/%d (%.1f%%) bytes %d/%d (%.1f%%)"
      % (ass_n, N, 100*ass_n/N, ass_b, TOT_B, 100*ass_b/TOT_B))

with open(OUT + r"\function_assign.tsv", "w", encoding="utf-8") as fo:
    fo.write("entry\tsubsystem\tevidence_kind\tconfidence\n")
    for f in funcs:
        a = assign.get(f["entry"], ("UNASSIGNED", "-", "-", "-"))
        fo.write("%08X\t%s\t%s\t%s\n" % (f["entry"], a[0], a[1], a[2]))

agg = defaultdict(lambda: {"n":0, "b":0, "lo":None, "hi":None, "kinds":Counter(),
                           "conf":Counter(), "ev":[]})
for f in funcs:
    a = assign.get(f["entry"])
    if not a: continue
    g = agg[a[0]]
    g["n"] += 1; g["b"] += f["size"]
    lo, hi = f["entry"], f["entry"] + f["size"]
    g["lo"] = lo if g["lo"] is None else min(g["lo"], lo)
    g["hi"] = hi if g["hi"] is None else max(g["hi"], hi)
    g["kinds"][a[1]] += 1; g["conf"][a[2]] += 1
    g["ev"].append((f["entry"], a[3]))

CORDER = ["高", "中", "低"]
with open(OUT + r"\subsystems.tsv", "w", encoding="utf-8") as fo:
    fo.write("subsystem\tn_functions\tn_bytes\taddr_lo\taddr_hi\tevidence\tconfidence\n")
    rows = []
    for ss in SS:
        if ss not in agg: continue
        g = agg[ss]
        kinds = ",".join("%s:%d" % kv for kv in g["kinds"].most_common())
        conf = min(g["conf"].items(), key=lambda kv: CORDER.index(kv[0]))[0]
        samples = "; ".join("%08X %s" % t for t in g["ev"][:3])
        rows.append((ss, g["n"], g["b"], "%08X" % g["lo"], "%08X" % g["hi"],
                     "%s | e.g. %s" % (kinds, samples), conf))
        fo.write("\t".join(str(x) for x in rows[-1]) + "\n")
json.dump({str(k): v for k, v in assign.items()}, open(OUT + r"\assign_debug.json", "w"), indent=0)

print("\n=== 子系统规模 ===")
for r in rows:
    print(" %-22s n=%5d b=%8d %s-%s conf=%s" % (r[0], r[1], r[2], r[3], r[4], r[6]))
print("\n=== UNASSIGNED 残余 (簇>=15) ===")
for cl in clusters:
    un = [f for f in cl if f["entry"] not in assign]
    if len(un) >= 15:
        b = sum(f["size"] for f in un)
        strs = Counter()
        for f in un:
            for s in re.split(r" \| ", f["strings"]):
                if s: strs[s] += 1
        print(" %08X-%08X un=%d bytes=%d str=%s" %
              (un[0]["entry"], un[-1]["entry"]+un[-1]["size"], len(un), b,
               ";".join(s[:22] for s,_ in strs.most_common(5))[:100]))
