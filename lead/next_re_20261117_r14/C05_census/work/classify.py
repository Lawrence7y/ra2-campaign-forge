#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C05 按 PLAN §1 S01-S22 分类（可复跑）。
多信号加权 + 确定性规则；输出 coverage_delta.tsv + EVIDENCE/classification_trace.tsv。
信号优先级（强→弱）：self_known(YRpp/kb 地址名) > vtable 类 > module 源文件 > 字符串关键词 > 已知名亲戚投票 > 导入API。
grade: [已证]=有明确地址名(YRpp/kb); [静态推断]=vtable类唯一映射/模块; [未证]=弱信号/零证据。
high 判据（与 C01/C02/C04 同规格）:
  (A) self_known 且 clean 后有名 → high（[已证]，名字来自 YRpp/kb 地址名）;
  (B) vtable 类唯一映射到某 Sxx 且 core=True → high（[静态推断]）。
本片地址 0x54a290..0x5cbd1f，主类族：LocomotionClass(整族 S11)、MPGameMode 系(S18)、
MissionClass(S10)、MapClass/MapSeedClass(S06/S21)、RadioClass(S14)、UI 控件(S09)、
VQ/BinkMovie(S19)、LightSource/Convert/LaserDraw/LineTrail(S07/S20)、压缩管线(S03)。
"""
import os, json, re
from collections import Counter, defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C05_census")
WORK  = os.path.join(CARD, "work")
EVID  = os.path.join(CARD, "EVIDENCE")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

SUBSYS_NAME = {
 "S01":"启动/主循环/帧时钟","S02":"CRT/内存池/异常守卫","S03":"文件系统/MIX/压缩加密",
 "S04":"INI/规则加载","S05":"对象模型/虚表布局","S06":"地图/Cell/地形/矿石",
 "S07":"渲染/Blitter/SHP/VXL/调色板","S08":"迷雾/可见性/雷达","S09":"UI/侧栏/菜单/对话框/输入/命令派发",
 "S10":"Mission/单位行为AI","S11":"Locomotor/寻路","S12":"生产/经济/工厂/建造放置",
 "S13":"战斗/Weapon/Warhead/Bullet","S14":"House/AI/Team/Script","S15":"触发器/Tag/TEvent/TAction",
 "S16":"超级武器","S17":"存档/序列化/Swizzle","S18":"网络/事件队列/联机","S19":"音频/EVA/音乐/VQA",
 "S20":"粒子/Anim/特效","S21":"战役/关卡/得分/剧情","S22":"随机数/数学/字符串/第三方库/通用容器",
}

# ---- 类 -> (Sxx, core) 有序包含匹配（具体在前，通用容器兜底在后）----
CLASS_RULES = [
  # S11 Locomotor 整族（本片最大类族）
  (["JumpjetLocomotionClass","MechLocomotionClass","RocketLocomotionClass",
    "DropPodLocomotionClass","TeleportLocomotionClass","WalkLocomotionClass",
    "HoverLocomotionClass","FlyLocomotionClass","TunnelLocomotionClass",
    "DriveLocomotionClass","ShipLocomotionClass","LocomotionClass"], "S11", True),
  # S18 多人游戏模式（MPGameMode 系 + 团队）
  (["MPCooperative","MultiplayerSiege","FreeForAll","UnholyAlliance","Megawealth",
    "MultiplayerManBattle","MultiplayerBattle","MultiplayerGameMode","MPGameModeClass",
    "MPTeams","MultiplayerTeam","MultiplayerObserverTeam","MultiplayerSiegeAttackerTeam",
    "MultiplayerSiegeDefenderTeam","Selection_WorldDominationTour"], "S18", True),
  # S10 Mission / 单位行为
  (["MissionClass"], "S10", True),
  # S14 House/Team/Radio（RadioClass=单位间无线电链路基础设施）
  (["RadioClass","HouseClass","HouseTypeClass","TeamTypeClass","TeamClass","House"], "S14", True),
  # S03 文件/压缩管线
  (["BlowStraw","Base64Straw","Base64Pipe","CacheStraw","FileStraw","FilePipe",
    "CCFileClass","CDFileClass","MixFileClass","LCWPipe","LCWStraw","LZOPipe","LZOStraw",
    "PKPipe","HVA"], "S03", True),
  # S15 触发器 / Tag
  (["TActionClass","TEventClass","TagClass"], "S15", True),
  # S06 地图 / 地形 / 覆盖物
  (["MapClass","IsometricTileTypeClass","IsometricTileClass","CellClass","Theater",
    "PendingCellClass","MapRegionClass","SubzoneConnectionStruct","SubzoneTrackingStruct",
    "ZoneConnectionClass","PassabilityType"], "S06", True),
  # S04 INI
  (["INIClass","INIEntry","INISection","CCINIClass"], "S04", True),
  # S21 战役/随机地图生成/得分/继承
  (["MapSeedClass","CarryoverClass","CoopCampaignClass","MPlayerScoreType",
    "ScenarioClass","CampaignClass"], "S21", True),
  # S19 电影/视频
  (["VQMovieHandle","BinkMovieHandle","VocClass"], "S19", True),
  # S01 帧时钟/主循环
  (["FPSCounter","LoadProgressMgr"], "S01", True),
  # S09 UI / 命令派发（控件家族 + Sidebar/Radar/Mouse）
  (["CommandClass","GScreenClass","MouseClass","TabClass","SidebarClass","PowerClass",
    "RadarClass","ScrollClass","GraphicMenu","StripClass","GadgetClass","ControlClass",
    "EditClass","SliderClass","GaugeClass","DropListClass","CheckListClass",
    "ColorListClass","TextLabelClass","TextButtonClass","ShapeButtonClass",
    "StaticButtonClass","ToggleClass","TriColorGaugeClass","Dial8Class","ListClass",
    "SBGadgetClass","SelectClass","MapSelect","LoadOptionsClass","InputManagerClass"], "S09", True),
  # S07 渲染显示（Display / Tactical / Convert 光色）
  (["DisplayClass","TacticalClass","ConvertClass","LightConvertClass","LightSourceClass",
    "VRGBClass","Blitter","Blit"], "S07", True),
  # S20 粒子/Anim/激光轨迹
  (["LaserDrawClass","LineTrail","AnimClass","AnimTypeClass","Particle",
    "MSEngine","MSFadeAnim","MSOverlayAnim","MSShapeAnim","VeinholeMonsterClass"], "S20", True),
  # S17 存档/序列化
  (["Swizzle"], "S17", True),
  # S05 对象模型 / 类型类（Techno/Object 基类与类型类）
  (["TechnoClass","FootClass","ObjectClass","AbstractTypeClass","AbstractClass",
    "InfantryTypeClass","UnitTypeClass","AircraftTypeClass","TechnoTypeClass",
    "ObjectTypeClass","BuildingTypeClass","CaptureManagerClass"], "S05", True),
  # S10 单位实例（Unit/Infantry/Aircraft）
  (["InfantryClass","UnitClass","AircraftClass"], "S10", True),
  # S12 建筑
  (["BuildingClass"], "S12", True),
  # S13 战斗（Kamikaze 自杀机控制）
  (["Kamikaze","BulletClass","BulletTypeClass","WeaponTypeClass","WarheadTypeClass","DamageGroup"], "S13", True),
  # S16 超级武器
  (["IonBlast","IonClass","Dominator"], "S16", True),
  # S22 通用容器兜底（元素类型无关的模板容器 / 节点 / 矩形）
  (["VectorClass","DynamicVectorClass","TypeList","VectorCursor","Point3D","T_List",
    "T_Node","rc_ptr","LinkClass","LayerClass","LogicClass","TRect","NodeNameType"], "S22", False),
]
def class_to_sub(cls):
    for keys, s, core in CLASS_RULES:
        for k in keys:
            if k in cls:
                return s, core
    return None, False

# ---- 已知名 -> Sxx（按命名空间/类前缀，有序）----
NAME_CLASS_RULES = [
  (r"^Kamikaze", "S13"),
  (r"^InputManagerClass|^MouseClass|^SidebarClass|^TabClass|^PowerClass|^RadarClass|^ScrollClass|^CommandClass|CommandClass::|^LoadOptionsClass|^MapSelect|^LoadProgress", "S09"),
  (r"^FPSCounter", "S01"),
  (r"^FileSystem|^MixFileClass|^HVA::|^BlowStraw|^LCW|^LZO|^CCFileClass", "S03"),
  (r"^MPGameModeClass|^MPTeams|^Multiplayer|^FreeForAll|^UnholyAlliance|^Megawealth|^MPBattle|^MPSiege|^MPCoop", "S18"),
  (r"^MapSeedClass", "S21"),
  (r"^MapClass::", "S06"),
  (r"^MissionClass::", "S10"),
  (r"^RadioClass::", "S14"),
  (r"^LocomotionClass|^.*LocomotionClass::|^.*Locomotion::", "S11"),
  (r"^LaserDrawClass::|^LineTrail::", "S20"),
  (r"^LightSourceClass::|^ConvertClass::|^DisplayClass::|^TacticalClass::", "S07"),
  (r"^VQMovie|^BinkMovie|^VocClass::|^EVA|^Audio", "S19"),
  (r"^Bullet|^Weapon|^Warhead|^DamageGroup", "S13"),
  (r"^InfantryTypeClass::|^UnitTypeClass::|^AircraftTypeClass::|^ObjectTypeClass::|^Abstract", "S05"),
  (r"^BuildingClass::|^BuildingTypeClass::|^TechnoClass::|^CaptureManagerClass::", "S12"),
  (r"^HouseTypeClass::|^HouseClass::|^GeneralStructures::|^TeamTypeClass::|^TeamClass::", "S14"),
  (r"^CCINIClass::|^INIClass::", "S04"),
  (r"^DisplayClass::|^TacticalClass::|^ConvertClass::|^Surface::|^Drawing::", "S07"),
]
BAD_TOKENS = {"setne","this","ReadString","WriteString","ReadInteger","WriteInteger","sete","noinit_t"}
def clean_known(names):
    out = []
    for n in names:
        if n in BAD_TOKENS: continue
        if n.endswith("::noinit_t"): continue
        if n.startswith("Unsorted::sub_"): continue
        if "::" not in n and n not in ("Here_I_Am",): continue
        out.append(n)
    return out
def name_to_sub(nm):
    if nm == "Here_I_Am": return "S17"
    for pat, s in NAME_CLASS_RULES:
        if re.search(pat, nm): return s
    return None

# ---- 字符串关键词 -> Sxx ----
STR_SPECIFIC = [
  ("Ion.cpp","S16"),("LightningStorm","S16"),("Dominator","S16"),
  ("Init.CPP","S09"),("Cmnd:","S09"),("TXT_","S09"),("GUI:","S09"),("Sidebar.CPP","S09"),
  ("UICmnds.cpp","S09"),("LoadDlg.CPP","S09"),("MapSel.CPP","S09"),("Beacon.CPP","S09"),
  ("Display.CPP","S07"),("Tactical.CPP","S07"),("PROGBAR2.SHP","S07"),
  ("House.CPP","S14"),("Infantry.CPP","S10"),("Unit.CPP","S10"),
  ("wonline.cpp","S18"),("netshare.cpp","S18"),("netdlg","S18"),("Session.CPP","S18"),
  ("Connect.CPP","S18"),("Multiplayer.cpp","S18"),("Modem","S18"),("MPCoop","S18"),
  ("MPSiegeTeam","S18"),("MPLayer","S18"),("MPObserver","S18"),("MPScore","S18"),
  ("SendFile","S18"),("WOL","S18"),("SerialEd","S18"),("NullMgr","S18"),("NullDlg","S18"),
  ("Ini.CPP","S04"),("TAction.CPP","S15"),("Event.CPP","S15"),
  ("Scenario.CPP","S21"),("MapGen.cpp","S21"),("PlanMgr.cpp","S21"),("CampScor","S21"),("coopcamp","S21"),
  ("MapSel.CPP","S06"),
  ("MainLoop.CPP","S01"),("Startup.CPP","S01"),("Conquer.CPP","S01"),("Credits.CPP","S09"),
  ("LdPrgMgr.cpp","S01"),("FPS :","S01"),
  ("CACHE.MIX","S03"),("LOCAL.MIX","S03"),("CONQMD.MIX","S03"),("CONQUER.MIX","S03"),
  ("loadmd.MIX","S03"),("LOADMD.MIX","S03"),("RMGMD.INI","S03"),(".MIX","S03"),
  ("EVA_","S19"),("VoxClass","S19"),("voxels.vpl","S19"),
  ("FOG.SHP","S08"),("SHROUD.SHP","S08"),
  (".SHP","S07"),(".SHA","S07"),("Image","S07"),("ToTile","S07"),("Palette","S07"),
]
def str_to_sub(s):
    for k, sub in STR_SPECIFIC:
        if k in s: return sub
    return None

# ---- 源文件模块 -> Sxx ----
MOD_RULES = {
  "Init.CPP":"S09","UICmnds.cpp":"S09","Sidebar.CPP":"S09","GameDlg.CPP":"S09",
  "Options.CPP":"S09","ToolTip.cpp":"S09","GDlgSupp.cpp":"S09","MapSel.CPP":"S09",
  "WDTSel.cpp":"S09","WDTGameOptions.cpp":"S09","WDTProps.cpp":"S09","WDTTerr.cpp":"S09",
  "Credits.CPP":"S09","LoadDlg.CPP":"S09","Beacon.CPP":"S09","Restate.cpp":"S09",
  "House.CPP":"S14","Infantry.CPP":"S10","Ion.cpp":"S16","Ini.CPP":"S04",
  "Display.CPP":"S07","Tactical.CPP":"S07","ownrdraw.cpp":"S07","Radar.CPP":"S09","Power.CPP":"S09",
  "TAction.CPP":"S15","Event.CPP":"S15","Super.CPP":"S16",
  "Scenario.CPP":"S21","MapGen.cpp":"S21","PlanMgr.cpp":"S21","CampScor.cpp":"S21","coopcamp.cpp":"S21",
  "MPScore.cpp":"S21","MPObserver.cpp":"S18","MPSiegeTeam.cpp":"S18","MPCoop.cpp":"S18",
  "wonline.cpp":"S18","netshare.cpp":"S18","netdlg2.cpp":"S18","NetDlg.CPP":"S18",
  "Session.CPP":"S18","Connect.CPP":"S18","ModemHst.cpp":"S18","ModemGst.cpp":"S18",
  "Multiplayer.cpp":"S18","SendFile.CPP":"S18","WOLPersonaInformation.cpp":"S18",
  "SerialEd.cpp":"S18","NullMgr.CPP":"S18","NullDlg.CPP":"S18","Dropship.cpp":"S18",
  "MPLayer.CPP":"S18",
  "MainLoop.CPP":"S01","Startup.CPP":"S01","Conquer.CPP":"S01","LdPrgMgr.cpp":"S01",
  "AbsType.cpp":"S05","Unit.CPP":"S10","WorldDom.cpp":"S09","LoadDlg.CPP":"S09",
}
# ---- 导入 API -> Sxx ----
IMP_RULES = {
  "MessageBoxA":"S09","GetDlgItem":"S09","SetWindowLongA":"S09","GetWindowLongA":"S09",
  "GetClientRect":"S09","GetCursorPos":"S09","GetKeyState":"S09","GetAsyncKeyState":"S09",
  "FindResourceA":"S09","ShowWindow":"S09","SendMessageA":"S09","MapVirtualKeyA":"S09",
  "SetWindowPos":"S09","InvalidateRect":"S09","RegEnumKeyExA":"S09","GetDC":"S09",
  "ClientToScreen":"S09","GetSystemMetrics":"S09",
  "FindFirstFileA":"S03","FindNextFileA":"S03","FindClose":"S03","DeleteFileA":"S03",
  "DeviceIoControl":"S03","GetWindowsDirectoryA":"S03",
  "CoCreateInstance":"S18","OleLoadFromStream":"S17","OleSaveToStream":"S17",
  "MapViewOfFileEx":"S17","UnmapViewOfFile":"S17",
  "timeGetTime":"S01","GetSystemTime":"S01","QueryPerformanceFrequency":"S01","timeBeginPeriod":"S01",
  "InterlockedIncrement":"S02","InterlockedDecrement":"S02","EnterCriticalSection":"S02",
  "InitializeCriticalSection":"S02","GlobalMemoryStatus":"S02",
  "MultiByteToWideChar":"S22","wsprintfA":"S22","WideCharToMultiByte":"S22",
  "SetBkColor":"S07","DeleteObject":"S07",
  "RegOpenKeyExA":"S09","Sleep":"S01",
}
IMPORTANT_STR = ["Ion.cpp","Init.CPP","House.CPP","Cmnd:","EVA_","CACHE.MIX","TXT_","GUI:","MapGen.cpp"]

def rel_vote(f):
    c = Counter()
    for _, nms in f["callers_known"] + f["callees_known"]:
        for nm in clean_known(nms):
            s = name_to_sub(nm)
            if s: c[s] += 1
    return c

rows = []
trace = []
for f in F:
    e = f["entry"]
    selfk = clean_known(f["self_known"])
    vt = f["vt"]
    module = f["module"]
    strings = f["strings"]
    imp = f["first_import"]
    vote = rel_vote(f)

    sub = None; conf = None; grade = None; source = None; name = ""; sem = ""

    # 1) 明确地址名（YRpp/kb）
    if selfk:
        nm = selfk[0]
        sub = name_to_sub(nm)
        if sub is None and vt:
            sub, _ = class_to_sub(vt[0][0])
        name = nm
        sub = sub or "S05"
        conf = "high"; grade = "[已证]"; source = "self_known"
        sem = "%s：YRpp/kb 地址名；归属 %s（名字已证，语义据名）" % (nm, SUBSYS_NAME[sub])
    # 2) vtable 类
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
            name = "%s::slot%d" % (cls, slot)
            source = "vtable"
            sem = "%s 虚表槽 %d(+0x%X)：%s 方法（槽语义未证）" % (cls, slot, slot*4, SUBSYS_NAME[sub])
        else:
            sub, conf, grade, source = "S22", "low", "[未证]", "vtable-unmapped"
            cls, slot = vt[0][0], vt[0][1]
            name = "%s::slot%d" % (cls, slot)
            sem = "%s 虚表槽，类名无法映射到 S01-S22（待人工）" % cls
    # 3) 源文件模块
    elif module and module in MOD_RULES:
        sub = MOD_RULES[module]; conf = "med"; grade = "[静态推断]"; source = "module"
        name = "sub_%08X" % e
        sem = "源文件 %s 归属 %s（模块线索）" % (module, SUBSYS_NAME[sub])
    # 4) 强字符串
    elif strings and str_to_sub(strings):
        sub = str_to_sub(strings)
        strong = any(k in strings for k in IMPORTANT_STR)
        conf = "med" if strong else "low"
        grade = "[未证]"; source = "string"
        name = "sub_%08X" % e
        kw = next((k for k,_ in STR_SPECIFIC if k in strings), "")
        sem = "引用 '%s' → %s（字符串线索）" % (kw, SUBSYS_NAME[sub])
    # 5) 亲戚名投票
    elif vote:
        sub, n = vote.most_common(1)[0]
        conf = "low"; grade = "[未证]"; source = "relay_vote"
        name = "sub_%08X" % e
        sem = "调用图邻居 %d 票指向 %s（弱信号）" % (n, SUBSYS_NAME[sub])
    # 6) 导入 API
    elif imp in IMP_RULES:
        sub = IMP_RULES[imp]; conf = "low"; grade = "[未证]"; source = "import"
        name = "sub_%08X" % e
        sem = "导入 %s → %s（弱信号）" % (imp, SUBSYS_NAME[sub])
    # 7) 零证据
    else:
        sub, conf, grade, source = "S22", "low", "[未证]", "none"
        name = "sub_%08X" % e
        sem = "无可用静态信号，归 S22 兜底（无法归类）[未证]"

    evpath = "EVIDENCE/classification_trace.tsv#%08X" % e
    rows.append((e, sub, name, sem, grade, evpath))
    trace.append(dict(entry=e, sub=sub, conf=conf, grade=grade, source=source,
                      name=name, sem=sem,
                      self_known="|".join(selfk), vt=";".join("%s:%d"%(c,s) for c,s,_ in vt),
                      module=module, strings=strings[:120], imp=imp,
                      vote=";".join("%s:%d"%(k,v) for k,v in vote.most_common())))

# 写 coverage_delta.tsv（6 列，无表头）
with open(os.path.join(CARD, "coverage_delta.tsv"), "w", encoding="utf-8") as f:
    for e, sub, name, sem, grade, ev in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (e, sub, name, sem.replace("\t"," "), grade, ev))

# 写 trace（带表头）
with open(os.path.join(EVID, "classification_trace.tsv"), "w", encoding="utf-8") as f:
    cols = ["entry","sub","conf","grade","source","name","sem","self_known","vt","module","strings","imp","vote"]
    f.write("\t".join(cols)+"\n")
    for t in trace:
        f.write("\t".join(str(t[c]).replace("\t"," ") for c in cols)+"\n")

print("total", len(rows))
print("\n== by subsystem ==")
for s, n in sorted(Counter(r[1] for r in rows).items()):
    hi = sum(1 for t in trace if t["sub"]==s and t["conf"]=="high")
    print("%s %4d  high=%d  %s" % (s, n, hi, SUBSYS_NAME[s]))
print("\n== confidence ==", dict(Counter(t["conf"] for t in trace)))
print("== grade ==", dict(Counter(t["grade"] for t in trace)))
print("== source ==", dict(Counter(t["source"] for t in trace)))
print("high count =", sum(1 for t in trace if t["conf"]=="high"))
print("无法归类(source=none) =", sum(1 for t in trace if t["source"]=="none"))

json.dump(dict(rows=rows, trace=trace), open(os.path.join(WORK,"classification.json"),"w",encoding="utf-8"), ensure_ascii=False)
