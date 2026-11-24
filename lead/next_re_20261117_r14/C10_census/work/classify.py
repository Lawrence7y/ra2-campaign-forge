#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 按 PLAN §1 S01-S22 分类（可复跑）。规格与 C01-C09 同；追加 C10 本片（0x77-0x7E 镜像尾部）类族规则。

信号优先级：self_known(YRpp/kb) > vtable 类 > module 源文件 > 字符串关键词 > 已知名亲戚投票 > 导入API。
grade: [已证]=明确地址名(YRpp/kb); [静态推断]=vtable类唯一映射/模块; [未证]=弱信号/零证据。
high 判据: (A) self_known clean 后有名; (B) vtable 类唯一映射到某 Sxx 且 core=True。

本片主类族：Westwood Online / wonline.cpp / Chat/Winsock/Modem/Web/Dialog(S18)、
WWMouseClass/wwmous.cpp/控件(S09)、BSurface/XSurface/DSurface/T_Blit*(S07)、
CRT::* 运行时字符串/内存函数(S02)、FilePipe/FileStraw/Buffer*(S03)、
异常 RTTI 类 bad_cast/bad_typeid/exception(S02)、T_DynamicVector/Vector 泛型(S22)。
"""
import os, json, re
from collections import Counter, defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
WORK = os.path.join(CARD, "work")
EVID = os.path.join(CARD, "EVIDENCE")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

SUBSYS_NAME = {
    "S01": "启动/主循环/帧时钟", "S02": "CRT/内存池/异常守卫", "S03": "文件系统/MIX/压缩加密",
    "S04": "INI/规则加载", "S05": "对象模型/虚表布局", "S06": "地图/Cell/地形/矿石",
    "S07": "渲染/Blitter/SHP/VXL/调色板", "S08": "迷雾/可见性/雷达", "S09": "UI/侧栏/菜单/对话框/输入/命令派发",
    "S10": "Mission/单位行为AI", "S11": "Locomotor/寻路", "S12": "生产/经济/工厂/建造放置",
    "S13": "战斗/Weapon/Warhead/Bullet", "S14": "House/AI/Team/Script", "S15": "触发器/Tag/TEvent/TAction",
    "S16": "超级武器", "S17": "存档/序列化/Swizzle", "S18": "网络/事件队列/联机", "S19": "音频/EVA/音乐/VQA",
    "S20": "粒子/Anim/特效", "S21": "战役/关卡/得分/剧情", "S22": "随机数/数学/字符串/第三方库/通用容器",
}

# ---- 通用模板包装器优先判据（先于 core，避免按实例化 T 虚高分级；同 C08 纪律）----
# VectorClass<T>/DynamicVectorClass<T>/VectorCursor/rc_ptr 是容器/智能指针，类名嵌的 T 只是参数。
GENERIC_WRAPPERS = ["TClassFactory", "VectorClass", "DynamicVectorClass", "VectorCursor",
                    "T_rc_ptr", "DiscreteDistributionClass", "DistributionObject", "TypeList",
                    "T_List", "T_Node", "Point3D", "TRect", "LinkClass", "LayerClass", "LogicClass"]

# ---- 类 -> (Sxx, core) 有序包含匹配（具体在前，通用容器已在上面拦截）----
CLASS_RULES = [
    # C10+ Westwood Online / 网络整族（本片主力：wonline.cpp / Chat/Winsock/Modem/Web/Dialog）
    (["CChatEventSink", "T_CComObject_VCChatEventSink___ATL", "T_CComObject_VCNetUtilEventSink___ATL",
      "CNetUtilEventSink", "T_CComObject_VCDownloadEventSink___ATL", "UDPInterfaceClass",
      "IPXInterfaceClass", "WinsockInterfaceClass", "WinModemClass", "WebBrowser", "PlayerProfile",
      "SimpleWonlineDialogControl", "WonlineStringDialogControl", "CreateGameDialogControl",
      "FactionSelectDialogControl_WorldDominationTour"], "S18", True),
    # C10+ 渲染曲面/Blitter（BSurface/XSurface/DSurface/T_Blit*）
    (["BSurface", "XSurface", "DSurface", "T_BlitTrans_E", "T_BlitPlain_E",
      "T_BlitTrans_G", "T_BlitPlain_G"], "S07", True),
    # C10+ UI 鼠标/控件
    (["WWMouseClass", "Mouse", "CCToolTip"], "S09", True),
    # C10+ 文件管道/straw
    (["BufferPipe", "BufferStraw"], "S03", True),
    # C10+ CRT/异常 RTTI 类
    (["bad_typeid", "bad_cast", "__non_rtti_object", "type_info", "exception", "_com_error"], "S02", True),
    # C09+ WorldDominationTour(WDT) 战役/游戏选项/UI 状态族 —— 本片主力
    (["GameOption_WorldDominationTour", "FlagGameOption_WorldDominationTour",
      "MapSizeGameOption_WorldDominationTour", "T_ValueGameOption", "ValueGameOption",
      "ToolTipManager", "TextButtonClass", "TextLabelClass", "ShapeButtonClass", "ToggleClass",
      "Anim_Voices_WorldDominationTour"], "S09", True),
    (["Campaign_WorldDominationTour", "CampaignProperties_WorldDominationTour",
      "History_WorldDominationTour", "State_WorldDominationTour", "Territory_WorldDominationTour",
      "Conflict_WorldDominationTour", "Map_WorldDominationTour", "Selection_WorldDominationTour",
      "WDTTerritory", "WDTState", "Centroid_WorldDominationTour", "WorldDominationTour"], "S21", True),
    # S16 超级武器
    (["TemporalClass", "SuperWeaponTypeClass", "SuperClass", "SuperWeaponClass",
      "EMPulseClass", "TemporalClass", "ChronoClass", "IronCurtainClass",
      "NuclearMissileClass", "PsychicDominatorClass", "LightningStormClass"], "S16", True),
    # S11 Locomotor 整族
    (["WalkLocomotionClass", "TunnelLocomotionClass", "TeleportLocomotionClass",
      "JumpjetLocomotionClass", "MechLocomotionClass", "RocketLocomotionClass",
      "DropPodLocomotionClass", "HoverLocomotionClass", "FlyLocomotionClass",
      "DriveLocomotionClass", "ShipLocomotionClass", "LocomotionClass"], "S11", True),
    # S15 触发器 / Tag / Action / Event
    (["TActionClass", "TEventClass", "TagTypeClass", "TagClass", "TriggerTypeClass", "TriggerClass"], "S15", True),
    # S13 战斗（Weapon/Warhead 本片主）
    (["WeaponTypeClass", "WarheadTypeClass", "BulletClass", "BulletTypeClass", "DamageGroup",
      "ParasiteClass", "SlaveManagerClass", "BombClass", "DiskLaserClass", "AirstrikeClass",
      "RadSiteClass", "SpawnManagerClass"], "S13", True),
    # S19 音频（Voc/Vox 本片主）/VQA
    (["VocClass", "VoxClass", "VQMovieHandle", "BinkMovieHandle", "SubTitle"], "S19", True),
    # S20 粒子/Anim/激光轨迹/特效（VoxelAnim/Wave/Veinhole/MS*Anim 本片主）
    (["VoxelAnimClass", "VoxelAnimTypeClass", "WaveClass", "VeinholeMonsterClass",
      "MSFrameAnim", "MSAnim", "MSSfxEntry", "LaserDrawClass", "LineTrail",
      "AnimClass", "AnimTypeClass", "Particle"], "S20", True),
    # S07 渲染显示（Convert/VXL 本片主）
    (["ConvertClass", "LightConvertClass", "VXL", "DisplayClass", "TacticalClass",
      "VRGBClass", "Blitter", "Blit", "DirtyAreaStruct", "ShadowControlClass",
      "FoggedObjectClass", "LightSourceClass", "SpotlightClass", "SpotLightClass",
      "BuildingLightClass"], "S07", True),
    # S06 地图 / 地形 / 覆盖物 / 矿石（Terrain/Tiberium/WaypointPath/Tube 本片主）
    (["TerrainClass", "TerrainTypeClass", "TiberiumClass", "WaypointPathClass", "TubeClass",
      "MapClass", "IsometricTileTypeClass", "IsometricTileClass", "CellClass",
      "OverlayTypeClass", "OverlayClass", "SmudgeTypeClass", "SmudgeClass",
      "Subzone", "Theater"], "S06", True),
    # S03 文件/压缩
    (["BlowStraw", "Base64Straw", "Base64Pipe", "CacheStraw", "FileStraw", "FilePipe",
      "CCFileClass", "CDFileClass", "MixFileClass", "LCWPipe", "LCWStraw", "LZOPipe", "LZOStraw", "PKPipe"], "S03", True),
    # S04 INI
    (["INIClass", "INIEntry", "INISection", "CCINIClass"], "S04", True),
    # S17 存档/序列化
    (["SwizzleManagerClass", "Swizzle"], "S17", True),
    # S18 多人游戏模式 / 网络
    (["MPCooperative", "MultiplayerSiege", "FreeForAll", "UnholyAlliance", "Megawealth",
      "MultiplayerGameMode", "MPGameModeClass", "MPTeams", "MultiplayerTeam",
      "NetworkEvents", "NullModemClass", "MessageListClass"], "S18", True),
    # S14 House/Team/TaskForce/Script/AI
    (["TeamTypeClass", "TaskForceClass", "TeamClass", "HouseClass", "HouseTypeClass", "RadioClass",
      "ScriptClass", "ScriptTypeClass", "AITriggerTypeClass", "NeuronClass",
      "PlanningTokenClass", "PlanningBranchClass"], "S14", True),
    # S09 UI / 命令派发（其它控件）
    (["CommandClass", "GScreenClass", "MouseClass", "SidebarClass", "PowerClass",
      "RadarClass", "ScrollClass", "GraphicMenu", "StripClass", "GadgetClass", "ControlClass",
      "EditClass", "SliderClass", "GaugeClass", "DropListClass", "CheckListClass",
      "ColorListClass", "TabClass", "StaticButtonClass", "TriColorGaugeClass", "Dial8Class",
      "ListClass", "SBGadgetClass", "SelectClass", "MapSelect", "LoadOptionsClass",
      "InputManagerClass", "GameOptionsClass", "SideClass"], "S09", True),
    # S12 建筑
    (["BuildingClass", "FactoryClass"], "S12", True),
    # S05 对象模型 / 类型类（UnitType/Abstract/Object 本片主）
    (["UnitTypeClass", "TechnoClass", "FootClass", "ObjectClass", "AbstractTypeClass",
      "AbstractClass", "InfantryTypeClass", "AircraftTypeClass", "TechnoTypeClass",
      "ObjectTypeClass", "BuildingTypeClass", "CaptureManagerClass"], "S05", True),
    # S10 单位实例
    (["UnitClass", "InfantryClass", "AircraftClass", "MissionClass"], "S10", True),
    # S22 通用容器/工厂兜底（元素类型无关模板容器/节点/工厂）
    (["StringTable", "StringTableClass"], "S22", False),
]


def class_to_sub(cls):
    for g in GENERIC_WRAPPERS:
        if g in cls:
            return "S22", False
    for keys, s, core in CLASS_RULES:
        for k in keys:
            if k in cls:
                return s, core
    return None, False


# ---- 已知名 -> Sxx（按命名空间/类前缀，有序）----
NAME_CLASS_RULES = [
    # C10+ 本片具名：CRT 运行时、鼠标、DirectDraw 封装
    (r"^CRT::", "S02"),
    (r"^WWMouseClass::|^Unsorted::CenterWindowIn", "S09"),
    (r"^Drawing::|^YRDDraw::", "S07"),
    (r"^Unsorted::RaiseError", "S02"),
    (r"^WorldDominationTour|^WDTSel|^WDTGameOptions|^WDTProps|^WDTTerr", "S09"),
    (r"^TemporalClass::|^SuperClass::|^SuperWeaponTypeClass::|^SuperWeaponClass::", "S16"),
    (r"^.*LocomotionClass::|^.*Locomotion::", "S11"),
    (r"^TActionClass::|^TagClass::|^TagTypeClass::|^TEventClass::|^TriggerClass::|^TriggerTypeClass::", "S15"),
    (r"^WeaponTypeClass::|^WarheadTypeClass::|^Bullet|^Weapon|^DamageGroup|^ParasiteClass::|^SlaveManager|^BombClass|^DiskLaser|^Airstrike|^RadSite", "S13"),
    (r"^VocClass::|^VoxClass::|^VQMovie|^BinkMovie|^EVA|^Audio|^SubTitle", "S19"),
    (r"^VoxelAnimClass::|^VoxelAnimTypeClass::|^WaveClass::|^VeinholeMonsterClass::|^MSFrameAnim|^MSAnim|^AnimClass::|^LineTrail::|^LaserDrawClass::", "S20"),
    (r"^VXL::|^ConvertClass::|^TacticalClass::|^DisplayClass::|^LightSourceClass::", "S07"),
    (r"^TerrainClass::|^TerrainTypeClass::|^TiberiumClass::|^WaypointPathClass::|^MapClass::|^CellClass::", "S06"),
    (r"^ToolTip|^TextButton|^TextLabel|^ShapeButton|^ToggleClass|^InputManagerClass|^MouseClass|^SidebarClass|^TabClass|^PowerClass|^RadarClass|^ScrollClass|^CommandClass|^StaticButtonClass|^UI::|^GameOptionsClass::|^MapSelect|^LoadProgress", "S09"),
    (r"^SwizzleManagerClass::|^Here_I_Am", "S17"),
    (r"^StringTable::", "S22"),
    (r"^UnitTypeClass::|^InfantryTypeClass::|^AircraftTypeClass::|^ObjectTypeClass::|^Abstract|^ObjectClass::|^FootClass::|^TechnoClass::|^TechnoTypeClass::", "S05"),
    (r"^BuildingClass::|^BuildingTypeClass::|^CaptureManagerClass::|^FactoryClass::", "S12"),
    (r"^MissionClass::|^UnitClass::|^InfantryClass::|^AircraftClass::", "S10"),
    (r"^TeamClass::|^TeamTypeClass::|^TaskForceClass::|^ScriptClass::|^HouseClass::|^HouseTypeClass::|^AITrigger", "S14"),
    (r"^NetworkEvents::|^MPGameModeClass::|^MPTeams|^Multiplayer|^NullModem|^MessageList", "S18"),
    (r"^Campaign_WorldDominationTour|^History_WorldDominationTour|^State_WorldDominationTour|^Territory_WorldDominationTour|^Conflict_WorldDominationTour|^Map_WorldDominationTour|^ScenarioClass::|^CampaignClass::", "S21"),
    (r"^CCINIClass::|^INIClass::", "S04"),
    (r"^FPSCounter", "S01"),
]

BAD_TOKENS = {"setne", "this", "ReadString", "WriteString", "ReadInteger", "WriteInteger", "sete", "changed"}


def clean_known(names):
    out = []
    for n in names:
        if n in BAD_TOKENS:
            continue
        if n.endswith("::noinit_t") or n.endswith("::int") or n.endswith("::setne"):
            continue
        if n.startswith("Unsorted::sub_"):
            continue
        if "::" not in n and n not in ("Here_I_Am",):
            continue
        out.append(n)
    return out


def name_to_sub(nm):
    if nm == "Here_I_Am":
        return "S17"
    for pat, s in NAME_CLASS_RULES:
        if re.search(pat, nm):
            return s
    return None


# ---- 字符串关键词 -> Sxx ----
STR_SPECIFIC = [
    ("WDTSel.cpp", "S09"), ("WDTGameOptions.cpp", "S09"), ("WDTProps.cpp", "S09"),
    ("WDTTerr.cpp", "S21"), ("ToolTip.cpp", "S09"), ("UICmnds.cpp", "S09"),
    ("Super.CPP", "S16"), ("TAction.CPP", "S15"), ("Event.CPP", "S15"),
    ("Tactical.CPP", "S07"), ("ownrdraw", "S07"), ("DirtyArea", "S07"),
    ("Techno.CPP", "S05"), ("AbsType.cpp", "S05"),
    ("Init.CPP", "S09"), ("Cmnd:", "S09"), ("GUI:", "S09"), ("Sidebar.CPP", "S09"),
    ("EVA_", "S19"), ("VoxClass", "S19"),
    ("MainLoop.CPP", "S01"), ("Startup.CPP", "S01"),
    ("CACHE.MIX", "S03"), (".MIX", "S03"),
    ("wonline.cpp", "S18"), ("netshare.cpp", "S18"),
    ("Infantry.CPP", "S10"), ("Unit.CPP", "S10"), ("House.CPP", "S14"),
    ("Scenario.CPP", "S21"), ("MapGen.cpp", "S21"),
]


def str_to_sub(s):
    for k, sub in STR_SPECIFIC:
        if k in s:
            return sub
    return None


MOD_RULES = {
    "Super.CPP": "S16", "Tactical.CPP": "S07", "TAction.CPP": "S15", "Techno.CPP": "S05",
    "AbsType.cpp": "S05", "Init.CPP": "S09", "Infantry.CPP": "S10", "Unit.CPP": "S10",
    "House.CPP": "S14", "MainLoop.CPP": "S01", "Scenario.CPP": "S21", "MapGen.cpp": "S21",
    "Ini.CPP": "S04", "WDTSel.cpp": "S09", "WDTGameOptions.cpp": "S09",
    # C10+
    "wonline.cpp": "S18", "WOLPersonaInformation.cpp": "S18", "WorldDom.cpp": "S18",
    "wwmous.cpp": "S09",
}

IMP_RULES = {
    "OleLoadFromStream": "S17", "OleSaveToStream": "S17", "MapViewOfFileEx": "S17",
    "UnmapViewOfFile": "S17", "CoCreateInstance": "S17",
    "InterlockedIncrement": "S02", "InterlockedDecrement": "S02", "EnterCriticalSection": "S02",
    "MessageBoxA": "S09", "GetDlgItem": "S09", "SendMessageA": "S09", "GetCursorPos": "S09",
    "GetAsyncKeyState": "S09", "TranslateMessage": "S09",
    "FindFirstFileA": "S03", "FindNextFileA": "S03", "FindClose": "S03", "DeleteFileA": "S03",
    "GetModuleFileNameA": "S03",
    "timeGetTime": "S01", "GetSystemTime": "S01", "QueryPerformanceFrequency": "S01",
    "KillTimer": "S01",
    "MultiByteToWideChar": "S22", "wsprintfA": "S22", "WideCharToMultiByte": "S22",
    # C10+ winsock/modem -> S18; DirectDraw -> S07; 线程同步 -> S02; locale -> S22
    "socket": "S18", "bind": "S18", "sendto": "S18", "recvfrom": "S18", "setsockopt": "S18",
    "getsockopt": "S18", "WSAStartup": "S18", "WSACleanup": "S18", "WSAGetLastError": "S18",
    "gethostbyname": "S18", "gethostname": "S18", "inet_ntoa": "S18", "htonl": "S18",
    "htons": "S18", "ntohl": "S18", "ntohs": "S18", "closesocket": "S18",
    "WSAAsyncSelect": "S18", "EnumProtocolsA": "S18", "GetCommModemStatus": "S18",
    "EscapeCommFunction": "S18", "PurgeComm": "S18",
    "DirectDrawCreate": "S07",
    "InitializeCriticalSection": "S02", "LeaveCriticalSection": "S02", "DeleteCriticalSection": "S02",
    "WaitForSingleObject": "S02", "SetEvent": "S02", "ResetEvent": "S02",
    "WaitForMultipleObjects": "S02", "Sleep": "S02",
    "LCMapStringW": "S22", "GetCPInfo": "S22", "EnumSystemLocalesA": "S22",
    "CompareStringW": "S22", "GetLocaleInfoW": "S22", "GetStringTypeW": "S22",
}
IMPORTANT_STR = ["Super.CPP", "Tactical.CPP", "TAction.CPP", "Techno.CPP", "EVA_", "Init.CPP",
                 "WDTSel.cpp", "WDTGameOptions.cpp",
                 "wonline.cpp", "WOLPersonaInformation.cpp", "WorldDom.cpp", "wwmous.cpp"]


def rel_vote(f):
    c = Counter()
    for _, nms in f["callers_known"] + f["callees_known"]:
        for nm in clean_known(nms):
            s = name_to_sub(nm)
            if s:
                c[s] += 1
    return c


rows = []; trace = []
for f in F:
    e = f["entry"]
    selfk = clean_known(f["self_known"])
    vt = f["vt"]; module = f["module"]; strings = f["strings"]; imp = f["first_import"]
    vote = rel_vote(f)

    sub = conf = grade = source = None; name = ""; sem = ""
    if selfk:
        nm = selfk[0]
        sub = name_to_sub(nm)
        if sub is None and vt:
            sub, _ = class_to_sub(vt[0][0])
        name = nm; sub = sub or "S05"
        conf = "high"; grade = "[已证]"; source = "self_known"
        sem = "%s：YRpp/kb 地址名；归属 %s（名字已证，语义据名）[未证]" % (nm, SUBSYS_NAME[sub])
    elif vt:
        cands = [(class_to_sub(cl), cl, slot) for cl, slot, vtv in vt]
        subs = [x[0][0] for x in cands if x[0][0]]
        core_subs = [x[0][0] for x in cands if x[0][0] and x[0][1]]
        if subs:
            sub, n = Counter(subs).most_common(1)[0]
            coreflag = any(cs == sub for cs in core_subs)
            conf = "high" if coreflag else "med"
            grade = "[静态推断]" if coreflag else "[未证]"
            pick = next((x for x in cands if x[0][0] == sub), cands[0])
            cls, slot = pick[1], pick[2]
            name = "%s::slot%d" % (cls, slot); source = "vtable"
            sem = "%s 虚表槽 %d(+0x%X)：%s 方法（槽语义未证）" % (cls, slot, slot * 4, SUBSYS_NAME[sub])
        else:
            sub, conf, grade, source = "S22", "low", "[未证]", "vtable-unmapped"
            cls, slot = vt[0][0], vt[0][1]
            name = "%s::slot%d" % (cls, slot)
            sem = "%s 虚表槽，类名无法映射到 S01-S22（待人工）" % cls
    elif module and module in MOD_RULES:
        sub = MOD_RULES[module]; conf = "med"; grade = "[静态推断]"; source = "module"
        name = "sub_%08X" % e
        sem = "源文件 %s 归属 %s（模块线索）" % (module, SUBSYS_NAME[sub])
    elif strings and str_to_sub(strings):
        sub = str_to_sub(strings)
        strong = any(k in strings for k in IMPORTANT_STR)
        conf = "med" if strong else "low"; grade = "[未证]"; source = "string"
        name = "sub_%08X" % e
        kw = next((k for k, _ in STR_SPECIFIC if k in strings), "")
        sem = "引用 '%s' → %s（字符串线索）" % (kw, SUBSYS_NAME[sub])
    elif vote:
        sub, n = vote.most_common(1)[0]
        conf = "low"; grade = "[未证]"; source = "relay_vote"
        name = "sub_%08X" % e
        sem = "调用图邻居 %d 票指向 %s（弱信号）" % (n, SUBSYS_NAME[sub])
    elif imp in IMP_RULES:
        sub = IMP_RULES[imp]; conf = "low"; grade = "[未证]"; source = "import"
        name = "sub_%08X" % e
        sem = "导入 %s → %s（弱信号）" % (imp, SUBSYS_NAME[sub])
    else:
        sub, conf, grade, source = "S22", "low", "[未证]", "none"
        name = "sub_%08X" % e
        sem = "无可用静态信号，归 S22 兜底（无法归类）[未证]"

    evpath = "EVIDENCE/classification_trace.tsv#%08X" % e
    rows.append((e, sub, name, sem, grade, evpath))
    trace.append(dict(entry=e, sub=sub, conf=conf, grade=grade, source=source,
                      name=name, sem=sem,
                      self_known="|".join(selfk), vt=";".join("%s:%d" % (c, s) for c, s, _ in vt),
                      module=module, source_file=f.get("source", ""), strings=strings[:120], imp=imp,
                      vote=";".join("%s:%d" % (k, v) for k, v in vote.most_common())))

with open(os.path.join(CARD, "coverage_delta.tsv"), "w", encoding="utf-8") as f:
    for e, sub, name, sem, grade, ev in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (e, sub, name, sem.replace("\t", " "), grade, ev))

with open(os.path.join(EVID, "classification_trace.tsv"), "w", encoding="utf-8") as f:
    cols = ["entry", "sub", "conf", "grade", "source", "name", "sem", "self_known", "vt", "module", "source_file", "strings", "imp", "vote"]
    f.write("\t".join(cols) + "\n")
    for t in trace:
        f.write("\t".join(str(t[c]).replace("\t", " ") for c in cols) + "\n")

print("total", len(rows))
print("\n== by subsystem ==")
for s, n in sorted(Counter(r[1] for r in rows).items()):
    hi = sum(1 for t in trace if t["sub"] == s and t["conf"] == "high")
    print("%s %4d  high=%d  %s" % (s, n, hi, SUBSYS_NAME[s]))
print("\n== confidence ==", dict(Counter(t["conf"] for t in trace)))
print("== grade ==", dict(Counter(t["grade"] for t in trace)))
print("== source ==", dict(Counter(t["source"] for t in trace)))
print("high count =", sum(1 for t in trace if t["conf"] == "high"))
print("无法归类(source=none) =", sum(1 for t in trace if t["source"] == "none"))

json.dump(dict(rows=rows, trace=trace), open(os.path.join(WORK, "classification.json"), "w", encoding="utf-8"), ensure_ascii=False)
