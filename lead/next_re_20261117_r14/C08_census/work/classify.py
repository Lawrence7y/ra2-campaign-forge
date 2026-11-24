#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C08 按 PLAN §1 S01-S22 分类（可复跑）。
规格与 C01/C02/C04/C05/C06 一致；追加 C08 本片（0x6B-0x71）类族规则，标 '# C08+'。

信号优先级（强→弱）：self_known(YRpp/kb) > vtable 类 > module 源文件 > 字符串关键词 > 已知名亲戚投票 > 导入API。
grade: [已证]=明确地址名(YRpp/kb); [静态推断]=vtable类唯一映射/模块; [未证]=弱信号/零证据。
high 判据: (A) self_known clean 后有名; (B) vtable 类唯一映射到某 Sxx 且 core=True。

本片主类族：SuperClass/SuperWeaponTypeClass(S16 超级武器)、
Techno/Foot/Building/Aircraft/Infantry/Unit(S05/S10/S12 对象模型)、
TAction/Tag/TagType(S15 触发器)、Team/TeamType/TaskForce(S14)、
SwizzleManager(S17 存档)、Tactical/DirtyArea/Shadow(S07)、
TeleportLocomotion(S11)、Tab/Scroll/Mouse/StaticButton(S09)、TClassFactory 模板(S22)。
"""
import os, json, re
from collections import Counter, defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C08_census")
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

# ---- 类 -> (Sxx, core) 有序包含匹配（具体在前，通用容器/工厂兜底在后）----
CLASS_RULES = [
  # S16 超级武器（C08+ 本片主力）
  (["SuperWeaponTypeClass","SuperClass","SuperWeaponClass","EMPulseClass","TemporalClass",
    "ChronoClass","IronCurtainClass","NuclearMissileClass","PsychicDominatorClass",
    "LightningStormClass","WallGuardClass","GasPartyClass"], "S16", True),
  # S11 Locomotor 整族
  (["JumpjetLocomotionClass","MechLocomotionClass","RocketLocomotionClass",
    "DropPodLocomotionClass","TeleportLocomotionClass","WalkLocomotionClass",
    "HoverLocomotionClass","FlyLocomotionClass","TunnelLocomotionClass",
    "DriveLocomotionClass","ShipLocomotionClass","LocomotionClass"], "S11", True),
  # S14 House/Team/TaskForce/Script/AI + C08+
  (["TeamTypeClass","TaskForceClass","TeamClass","HouseClass","HouseTypeClass","RadioClass",
    "ScriptClass","ScriptTypeClass","AITriggerTypeClass","NeuronClass","House",
    "PlanningTokenClass","PlanningBranchClass"], "S14", True),
  # S15 触发器 / Tag / Action / Event
  (["TActionClass","TEventClass","TagTypeClass","TagClass","TriggerTypeClass","TriggerClass"], "S15", True),
  # S17 存档/序列化
  (["SwizzleManagerClass","Swizzle"], "S17", True),
  # S18 多人游戏模式 / 网络
  (["MPCooperative","MultiplayerSiege","FreeForAll","UnholyAlliance","Megawealth",
    "MultiplayerGameMode","MPGameModeClass","MPTeams","MultiplayerTeam",
    "NetworkEvents","NullModemClass","MessageListClass"], "S18", True),
  # S03 文件/压缩
  (["BlowStraw","Base64Straw","Base64Pipe","CacheStraw","FileStraw","FilePipe",
    "CCFileClass","CDFileClass","MixFileClass","LCWPipe","LCWStraw","LZOPipe","LZOStraw","PKPipe"], "S03", True),
  # S06 地图 / 地形 / 覆盖物 / 矿石
  (["MapClass","IsometricTileTypeClass","IsometricTileClass","CellClass","Theater",
    "OverlayTypeClass","OverlayClass","TerrainTypeClass","TerrainClass","SmudgeTypeClass","SmudgeClass",
    "WaypointPathClass","TubeClass","TiberiumClass","Subzone"], "S06", True),
  # S04 INI
  (["INIClass","INIEntry","INISection","CCINIClass"], "S04", True),
  # S21 战役/随机地图/得分 + C08+ Campaign
  (["MapSeedClass","CarryoverClass","CoopCampaignClass","CampaignClass","ScenarioClass",
    "MPlayerScoreType","MapStage","MapSelection"], "S21", True),
  # S19 电影/视频/音频 + C08+ SubTitle
  (["VQMovieHandle","BinkMovieHandle","VocClass","SubTitle"], "S19", True),
  # S01 帧时钟
  (["FPSCounter","LoadProgressMgr"], "S01", True),
  # S09 UI / 命令派发（控件家族）+ C08+ Tab/Scroll/Mouse/StaticButton
  (["CommandClass","GScreenClass","MouseClass","TabClass","SidebarClass","PowerClass",
    "RadarClass","ScrollClass","GraphicMenu","StripClass","GadgetClass","ControlClass",
    "EditClass","SliderClass","GaugeClass","DropListClass","CheckListClass",
    "ColorListClass","TextLabelClass","TextButtonClass","ShapeButtonClass",
    "StaticButtonClass","ToggleClass","TriColorGaugeClass","Dial8Class","ListClass",
    "SBGadgetClass","SelectClass","MapSelect","LoadOptionsClass","InputManagerClass",
    "GameOptionsClass","SideClass"], "S09", True),
  # S07 渲染显示（Display/Tactical/Convert/光色/脏区/阴影/灯光）+ C08+
  (["DisplayClass","TacticalClass","Tactical","ConvertClass","LightConvertClass","LightSourceClass",
    "VRGBClass","Blitter","Blit","DirtyAreaStruct","ShadowControlClass","FoggedObjectClass",
    "AlphaShapeClass","BuildingLightClass","SpotlightClass","SpotLightClass"], "S07", True),
  # S20 粒子/Anim/激光轨迹/特效
  (["LaserDrawClass","LineTrail","AnimClass","AnimTypeClass","Particle",
    "VoxelAnimClass","VoxelAnimTypeClass","WaveClass","VeinholeMonsterClass"], "S20", True),
  # S13 战斗（Bullet/Warhead/Weapon/Damage/Slave/Bomb/Parasite/DiskLaser/Airstrike/RadSite）
  (["Kamikaze","BulletClass","BulletTypeClass","WeaponTypeClass","WarheadTypeClass","DamageGroup",
    "ParasiteClass","SlaveManagerClass","BombClass","DiskLaserClass","AirstrikeClass","RadSiteClass",
    "SpawnManagerClass"], "S13", True),
  # S12 建筑
  (["BuildingClass","FactoryClass"], "S12", True),
  # S05 对象模型 / 类型类（基类与类型类）
  (["TechnoClass","FootClass","ObjectClass","AbstractTypeClass","AbstractClass",
    "InfantryTypeClass","UnitTypeClass","AircraftTypeClass","TechnoTypeClass",
    "ObjectTypeClass","BuildingTypeClass","CaptureManagerClass"], "S05", True),
  # S10 单位实例
  (["InfantryClass","UnitClass","AircraftClass","MissionClass"], "S10", True),
  # S22 通用容器/工厂兜底（元素类型无关模板容器/节点/工厂）
  (["TClassFactory","VectorClass","DynamicVectorClass","TypeList","VectorCursor","Point3D",
    "T_List","T_Node","rc_ptr","LinkClass","LayerClass","LogicClass","TRect","NodeNameType",
    "DiscreteDistributionClass","DistributionObject"], "S22", False),
]
# C08+ 通用模板包装器优先判据：TClassFactory<T> 四法逐字节同构（已验 0x6BF750/0x6BF8D0/0x6BFA50
# slot0 md5 相同），VectorClass<T>/DynamicVectorClass<T> 是容器 —— 类名嵌的 T 只是实例化参数，
# 不能据此把方法判成 T 子系统的 core high（分级虚高）。先于 core 规则识别，一律 S22 core=False。
GENERIC_WRAPPERS = ["TClassFactory", "VectorClass", "DynamicVectorClass",
                    "DiscreteDistributionClass", "DistributionObject"]
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
  (r"^SuperClass::|^SuperWeaponTypeClass::|^SuperWeaponClass::", "S16"),
  (r"^TeleportLocomotionClass|^.*LocomotionClass::|^.*Locomotion::", "S11"),
  (r"^TActionClass::|^TagClass::|^TagTypeClass::|^TEventClass::|^TriggerClass::", "S15"),
  (r"^TeamClass::|^TeamTypeClass::|^TaskForceClass::|^ScriptClass::|^HouseClass::|^HouseTypeClass::|^AITrigger", "S14"),
  (r"^NetworkEvents::|^MPGameModeClass::|^MPTeams|^Multiplayer|^NullModem|^MessageList", "S18"),
  (r"^SwizzleManagerClass::|^Here_I_Am", "S17"),
  (r"^TacticalClass::|^DisplayClass::|^ConvertClass::|^LightSourceClass::|^SpotlightClass::|^BuildingLightClass::", "S07"),
  (r"^InputManagerClass|^MouseClass|^SidebarClass|^TabClass|^PowerClass|^RadarClass|^ScrollClass|^CommandClass|^StaticButtonClass|^UI::|^GameOptionsClass::|^MapSelect|^LoadProgress", "S09"),
  (r"^VQMovie|^BinkMovie|^VocClass::|^EVA|^Audio|^SubTitle", "S19"),
  (r"^Bullet|^Weapon|^Warhead|^DamageGroup|^ParasiteClass::|^SlaveManager|^BombClass|^DiskLaser|^Airstrike|^RadSite", "S13"),
  (r"^InfantryTypeClass::|^UnitTypeClass::|^AircraftTypeClass::|^ObjectTypeClass::|^Abstract|^ObjectClass::|^FootClass::|^TechnoClass::|^TechnoTypeClass::", "S05"),
  (r"^BuildingClass::|^BuildingTypeClass::|^CaptureManagerClass::|^FactoryClass::", "S12"),
  (r"^ParticleClass::|^VoxelAnimClass::|^AnimClass::|^WaveClass::|^LineTrail::|^LaserDrawClass::", "S20"),
  (r"^MissionClass::|^InfantryClass::|^UnitClass::|^AircraftClass::", "S10"),
  (r"^MapClass::|^MapSeedClass::|^ScenarioClass::|^CampaignClass::", "S06"),
  (r"^CCINIClass::|^INIClass::", "S04"),
  (r"^FPSCounter", "S01"),
]
BAD_TOKENS = {"setne","this","ReadString","WriteString","ReadInteger","WriteInteger","sete","noinit_t","changed"}
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
  ("Super.CPP","S16"),("TXT_FIRESTORM_ON","S16"),("TXT_CHARGING","S16"),("TXT_READY","S16"),("TXT_HOLD","S16"),
  ("TAction.CPP","S15"),("Event.CPP","S15"),
  ("Tactical.CPP","S07"),("ownrdraw","S07"),("DirtyArea","S07"),("SHROUD","S07"),
  ("Techno.CPP","S05"),("AbsType.cpp","S05"),
  ("Init.CPP","S09"),("Cmnd:","S09"),("TXT_","S09"),("GUI:","S09"),("Sidebar.CPP","S09"),("UICmnds.cpp","S09"),
  ("MapSel.CPP","S09"),("EVA_","S19"),("VoxClass","S19"),
  ("MainLoop.CPP","S01"),("Startup.CPP","S01"),
  ("CACHE.MIX","S03"),(".MIX","S03"),
  ("wonline.cpp","S18"),("netshare.cpp","S18"),
  ("Infantry.CPP","S10"),("Unit.CPP","S10"),("House.CPP","S14"),
  ("Scenario.CPP","S21"),("MapGen.cpp","S21"),
]
def str_to_sub(s):
    for k, sub in STR_SPECIFIC:
        if k in s: return sub
    return None

MOD_RULES = {
  "Super.CPP":"S16","Tactical.CPP":"S07","TAction.CPP":"S15","Techno.CPP":"S05",
  "AbsType.cpp":"S05","Init.CPP":"S09","Infantry.CPP":"S10","Unit.CPP":"S10","House.CPP":"S14",
  "MainLoop.CPP":"S01","Scenario.CPP":"S21","MapGen.cpp":"S21","Ini.CPP":"S04",
}

IMP_RULES = {
  "OleLoadFromStream":"S17","OleSaveToStream":"S17","MapViewOfFileEx":"S17","UnmapViewOfFile":"S17",
  "InterlockedIncrement":"S02","InterlockedDecrement":"S02","EnterCriticalSection":"S02",
  "InitializeCriticalSection":"S02","GlobalMemoryStatus":"S02",
  "MessageBoxA":"S09","GetDlgItem":"S09","SendMessageA":"S09","GetCursorPos":"S09","GetAsyncKeyState":"S09",
  "FindFirstFileA":"S03","FindNextFileA":"S03","FindClose":"S03","DeleteFileA":"S03",
  "timeGetTime":"S01","GetSystemTime":"S01","QueryPerformanceFrequency":"S01",
  "MultiByteToWideChar":"S22","wsprintfA":"S22","WideCharToMultiByte":"S22","CharToOemBuffA":"S22",
}
IMPORTANT_STR = ["Super.CPP","Tactical.CPP","TAction.CPP","Techno.CPP","EVA_","Init.CPP"]

def rel_vote(f):
    c = Counter()
    for _, nms in f["callers_known"] + f["callees_known"]:
        for nm in clean_known(nms):
            s = name_to_sub(nm)
            if s: c[s] += 1
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
            sem = "%s 虚表槽 %d(+0x%X)：%s 方法（槽语义未证）" % (cls, slot, slot*4, SUBSYS_NAME[sub])
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
        kw = next((k for k,_ in STR_SPECIFIC if k in strings), "")
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
                      self_known="|".join(selfk), vt=";".join("%s:%d"%(c,s) for c,s,_ in vt),
                      module=module, source_file=f.get("source",""), strings=strings[:120], imp=imp,
                      vote=";".join("%s:%d"%(k,v) for k,v in vote.most_common())))

with open(os.path.join(CARD, "coverage_delta.tsv"), "w", encoding="utf-8") as f:
    for e, sub, name, sem, grade, ev in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (e, sub, name, sem.replace("\t"," "), grade, ev))

with open(os.path.join(EVID, "classification_trace.tsv"), "w", encoding="utf-8") as f:
    cols = ["entry","sub","conf","grade","source","name","sem","self_known","vt","module","source_file","strings","imp","vote"]
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
