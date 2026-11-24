#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C03 按 PLAN §1 S01-S22 分类（可复跑）。
多信号加权 + 确定性规则；输出 coverage_delta.tsv + EVIDENCE/classification_trace.tsv。
信号优先级（强→弱）：self_strong(YRpp/kb 地址名) > self_ledger(台账名) > vtable 类 > module > 字符串 > 亲戚名投票 > 导入API。
grade: [已证]=YRpp/kb 明确地址名且归属一致; [静态推断]=台账名/核心类 vtable/模块/强字符串; [未证]=弱信号/零证据。

与 C02 的一致性约定（便于合并员合表）：同一类在两卡映射到同一 Sxx：
  BuildingClass/TechnoClass/ObjectClass/Abstract* -> S05
  InfantryClass/UnitClass/AircraftClass + FootClass -> S10
  UI gadget 族 -> S09 ; MapClass/CellClass -> S06 ; Convert/Surface/Display/Blitter -> S07
  CCINIClass -> S04 ; FileClass/pipe/straw -> S03 ; FoggedObject/Radar -> S08
  NetworkEvents/ConnMan -> S18 ; Vector/DynamicVector/TypeList 容器 -> S22
本卡新增（C02 片未出现）：Locomotion 族 -> S11 ; FactoryClass -> S12 ;
  DiskLaser/EBolt/EMPulse -> S20 ; MovieHandle -> S19 ; MissionClass -> S10。
容器模板（T_VectorClass/T_DynamicVectorClass）优先判为 S22，避免元素类型子串误配。
"""
import os, json, re
from collections import Counter, defaultdict

ROOT  = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C03_census")
WORK  = os.path.join(CARD, "work")
EVID  = os.path.join(CARD, "EVIDENCE")
D = json.load(open(os.path.join(WORK, "evidence.json"), encoding="utf-8"))
F = D["funcs"]

SUBSYS_NAME = {
 "S01":"启动/主循环/帧时钟","S02":"CRT/内存池/异常守卫","S03":"文件系统/MIX/压缩加密",
 "S04":"INI/规则加载","S05":"对象模型/虚表布局","S06":"地图/Cell/地形/矿石",
 "S07":"渲染/Blitter/SHP/VXL/调色板","S08":"迷雾/可见性/雷达","S09":"UI/侧栏/菜单/对话框/输入",
 "S10":"Mission/单位行为AI","S11":"Locomotor/寻路","S12":"生产/经济/工厂/建造放置",
 "S13":"战斗/Weapon/Warhead/Bullet","S14":"House/AI/Team/Script","S15":"触发器/Tag/TEvent/TAction",
 "S16":"超级武器","S17":"存档/序列化/Swizzle","S18":"网络/事件队列","S19":"音频/EVA/音乐/VQA",
 "S20":"粒子/Anim/特效","S21":"战役/关卡/得分/剧情","S22":"随机数/数学/字符串/第三方库",
}

# ---- 容器模板前缀：命中即 S22（core=False），优先于元素类型 ----
CONTAINER_MARK = ("VectorClass", "DynamicVectorClass", "TypeList", "T_VectorClass", "T_DynamicVectorClass")

# ---- 类 -> (Sxx, core高置信) 有序包含匹配（顺序：专用类在前，通用基类在后）----
CLASS_RULES = [
 # S11 Locomotor（含各派生）——必须在 Foot/Techno 之前（LocomotionClass 名不含这些，但稳妥）
 (["DriveLocomotionClass","DropPodLocomotionClass","FlyLocomotionClass","RocketLocomotionClass",
   "TunnelLocomotionClass","HoverLocomotionClass","MechLocomotionClass","TeleportLocomotionClass",
   "JumpjetLocomotionClass","WalkLocomotionClass","ShipLocomotionClass","LocomotionClass"], "S11", True),
 # S09 UI 控件/侧栏/选择/命令
 (["DropListClass","TriColorGaugeClass","GaugeClass","EditClass","SliderClass","GadgetClass",
   "StaticButtonClass","TextLabelClass","SBGadgetClass","ShapeButtonClass","ToggleClass","ControlClass",
   "Dial8Class","TextButtonClass","TabClass","CheckListClass","ColorListClass","ListClass","ScrollClass",
   "SidebarClass","SelectClass","StripClass","PowerClass","GScreenClass","DialogControl","CommandClass"], "S09", True),
 # S08 雷达/迷雾
 (["RTacticalClass_RadarClass","RadarClass","FoggedObjectClass"], "S08", True),
 # S07 渲染/表面/屏幕/层/Blitter/光照
 (["TacticalClass_DisplayClass","DisplayClass","DSurface","XSurface","Surface","Blitter","RLEBlitter",
   "LayerClass","MouseClass","Mouse"], "S07", True),
 # S06 地图/Cell
 (["MapClass","CellClass","Theater","ScenarioClass"], "S06", True),
 # S03 文件/管道/Straw
 (["FileClass","BufferPipe","BufferStraw","Pipe","Straw"], "S03", True),
 # S04 INI
 (["CCINIClass"], "S04", True),
 # S12 生产/工厂
 (["FactoryClass","BuildingTypeClass","CaptureManagerClass"], "S12", True),
 # S18 网络/连接/事件接收器
 (["ConnManClass","ConnectionClass","CChatEventSink","CNetUtilEventSink","RadioClass"], "S18", True),
 # S20 特效/Anim/粒子
 (["DiskLaserClass","EBolt","EMPulseClass","ParticleSystemTypeClass","ParticleSystemClass","ParticleClass",
   "ParticleTypeClass","AnimClass","Animate","VoxelAnimTypeClass","MSAnim","WaveClass"], "S20", True),
 # S19 音视频/VQA
 (["MovieHandle"], "S19", True),
 # S14 House/AI/Team/Script/TaskForce/AITrigger
 (["HouseClass","HouseTypeClass","TeamClass","TeamTypeClass","ScriptTypeClass","TaskForceClass",
   "AITriggerTypeClass","TagClass","TriggerClass","TriggerTypeClass"], "S14", True),
 # S15 触发器/Tag/事件/动作
 (["TEvent","TAction"], "S15", True),
 # S16 超级武器
 (["SuperClass","SuperWeaponTypeClass"], "S16", True),
 # S21 战役/关卡/得分
 (["CampaignClass","CarryoverClass","CampaignScoreClass"], "S21", True),
 # S17 序列化/Swizzle
 (["CStreamClass","Swizzle"], "S17", True),
 # S13 战斗（本片 BulletType 仅容器元素出现；保留兜底）
 (["BulletClass","BulletTypeClass","WeaponTypeClass","WarheadTypeClass"], "S13", True),
 # S05 对象模型基类（Abstract->Object->Techno）；BuildingClass 与 C02 一致归 S05
 (["AbstractTypeClass","AbstractClass","ObjectTypeClass","ObjectClass","TechnoTypeClass","TechnoClass",
   "BuildingClass","BuildingLightClass","SideClass","TubeClass"], "S05", True),
 # S10 Foot/Unit/Infantry/Aircraft（C02 派生类归 S10；FootClass 为其基类，行为/AI 主导）
 (["FootClass","UnitClass","InfantryClass","AircraftClass","MissionClass","UnitTypeClass",
   "InfantryTypeClass","AircraftTypeClass"], "S10", True),
 # S22 通用容器兜底（非模板的裸容器）
 (["VectorClass","DynamicVectorClass","TypeList","Point3D","DiscreteSelectionClass",
   "DiscreteDistributionClass","ArrayClass"], "S22", False),
]
def class_to_sub(cls):
    # 容器模板优先（元素类型不代表槽语义）
    for mk in CONTAINER_MARK:
        if mk in cls:
            return "S22", False
    for keys, s, core in CLASS_RULES:
        for k in keys:
            if k in cls:
                return s, core
    return None, False

# ---- 已知名 -> Sxx（按命名空间/类前缀）----
NAME_CLASS_RULES = [
 (r"^NetworkEvents::|^ConnMan|^CNetUtil|^RadioClass::", "S18"),
 (r"^FactoryClass::", "S12"),
 (r"^FlyLocomotionClass::|^DriveLocomotionClass::|^.*LocomotionClass::", "S11"),
 (r"^FootClass::|^UnitClass::|^InfantryClass::|^AircraftClass::|^MissionClass::", "S10"),
 (r"^DiskLaserClass::|^EBolt::|^EMPulseClass::|^AnimClass::", "S20"),
 (r"^MovieHandle::|^VocClass::|^Audio|^EVA", "S19"),
 (r"^DisplayClass::|^Surface::|^Drawing::|^DSurface::|^TacticalClass::|^ConvertClass::|^Blitter", "S07"),
 (r"^MapClass::|^CellClass::|^ScenarioClass::|^Theater::", "S06"),
 (r"^CCINIClass::", "S04"),
 (r"^CCFileClass::|^FileClass::|^FileSystem::|^CD::|^CDFileClass::", "S03"),
 (r"^UI::|^StringTable::|^SidebarClass::|^.*GadgetClass::|^EditClass::|^GaugeClass::", "S09"),
 (r"^FoggedObjectClass::|^RadarClass::", "S08"),
 (r"^CStreamClass::|^Here_I_Am|^Swizzle", "S17"),
 (r"^Campaign|^CampaignScore|^Carryover", "S21"),
 (r"^Bullet|^DamageGroup|^Weapon|^Warhead", "S13"),
 (r"^HouseClass::|^TeamClass::|^ScriptTypeClass::|^AITriggerTypeClass::", "S14"),
 (r"^AbstractClass::|^ObjectClass::|^TechnoClass::|^AbstractTypeClass::", "S05"),
]
BAD_TOKENS = {"setne","this","ReadString","WriteString","ReadInteger","WriteInteger","this",
              "noinit_t"}
def clean_known(names, allow_bare=False):
    out = []
    for n in names:
        if n in BAD_TOKENS: continue
        if "::" not in n and n not in ("Here_I_Am","noinit_t","AbstractClass") and not allow_bare:
            continue
        out.append(n)
    return out
def name_to_sub(nm):
    if nm == "Here_I_Am": return "S17"
    if nm in ("AbstractClass","noinit_t"): return None
    for pat, s in NAME_CLASS_RULES:
        if re.match(pat, nm): return s
    return None

# ---- 字符串关键词 -> Sxx ----
STR_RULES = [
 ("EVA_", "S19"), ("VocClass","S19"), (".VQA","S19"),("MOVIE","S19"),
 ("SAVEGAME.NET","S18"),("wolhost","S18"),("wolacpt","S18"),("Connect","S18"),
 ("CampScor","S21"),("coopsave","S21"),("coopcamp","S21"),("Campaign","S21"),
 ("CurrentMap","S21"),("Map%d","S21"),("Score","S21"),("CREDITSMD","S21"),
 ("IMAGEHLP.DLL","S02"),("Digest","S02"),("%08X","S02"),
 ("Conquer","S01"),("TXT_","S01"),
 ("Credits","S09"),("DROPLIST","S09"),("DLG","S09"),
 ("FOG.SHP","S08"),("SHROUD.SHP","S08"),
 ("DDRAW.DLL","S07"),(".SHP","S07"),(".SHA","S07"),(".PAL","S07"),("Image","S07"),
 ("PLACE.SHP","S07"),("TXT_SHADOW","S07"),
 ("BUILDNGZ","S12"),("WRENCH","S12"),("Foundation","S12"),("Power","S12"),
 ("IsoMapPack","S06"),("CellTags","S06"),("LocalSize","S06"),("Theater","S06"),("Tiberium","S06"),
 ("BuildCat","S04"),("House","S04"),("Color","S04"),
]
def str_to_sub(s):
    for k, sub in STR_RULES:
        if k in s: return sub
    return None

# ---- 源文件模块 -> Sxx ----
MOD_RULES = {"Conquer.CPP":"S01","Credits.CPP":"S09","GameDlg.CPP":"S09","Event.CPP":"S15",
             "House.CPP":"S14","Display.CPP":"S07","Dropship.cpp":"S07","CD.CPP":"S03"}
# ---- 导入 API -> Sxx ----
IMP_RULES = {"MessageBoxA":"S09","GetDlgItem":"S09","SetDlgItemTextA":"S09","GetActiveWindow":"S09",
             "FindFirstFileA":"S03","FindNextFileA":"S03","FindClose":"S03","LoadLibraryA":"S03",
             "DeviceIoControl":"S03","CoCreateInstance":"S18","MapViewOfFileEx":"S17",
             "UnmapViewOfFile":"S17","timeGetTime":"S01",
             "SymCleanup":"S02","SymGetSymFromAddr":"S02",
             "InterlockedIncrement":"S02","InterlockedDecrement":"S02","wsprintfA":"S22"}
IMPORTANT_STR = ["CREDITSMD","Campaign","Conquer","Connect","DDRAW.DLL","EVA_","FOG.SHP","SHROUD.SHP",
                 "IsoMapPack","GameDlg.CPP","Display.CPP","House.CPP","IMAGEHLP.DLL","SAVEGAME.NET"]

# ---- 亲戚名投票 ----
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
    selfstrong = clean_known(f["self_strong"])
    selfledger = clean_known(f["self_ledger"])
    vt = f["vt"]
    module = f["module"]
    strings = f["strings"]
    imp = f["first_import"]
    vote = rel_vote(f)

    sub = None; conf = None; grade = None; source = None; name = ""; sem = ""

    # 1) YRpp/kb 明确地址名（高可信）
    if selfstrong:
        nm = selfstrong[0]
        sub = name_to_sub(nm)
        if sub is None and vt:
            sub, _ = class_to_sub(vt[0][0])
        name = nm
        sub = sub or "S05"
        conf = "high"; grade = "[已证]"; source = "self_strong"
        sem = "%s：YRpp/kb 地址名；归属 %s（名字已证，语义一行据名推断[未证]）" % (nm, SUBSYS_NAME[sub])
    # 2) 台账显式地址名（补充，不升 [已证]）
    elif selfledger:
        nm = selfledger[0]
        sub = name_to_sub(nm)
        if sub is None and vt:
            sub, _ = class_to_sub(vt[0][0])
        name = nm
        sub = sub or "S05"
        conf = "med"; grade = "[静态推断]"; source = "self_ledger"
        sem = "%s：台账显式名；归属 %s（语义据名推断[未证]）" % (nm, SUBSYS_NAME[sub])
    # 3) vtable 类
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
            sem = "%s 虚表槽 %d(+0x%X)：%s 方法（槽语义未证[未证]）" % (cls, slot, slot*4, SUBSYS_NAME[sub])
        else:
            sub, conf, grade, source = "S22","low","[未证]","vtable-unmapped"
            cls, slot = vt[0][0], vt[0][1]
            name = "%s::slot%d" % (cls, slot)
            sem = "%s 虚表槽，类名无法映射到 S01-S22（待人工）[未证]" % cls
    # 4) 源文件模块
    elif module in MOD_RULES:
        sub = MOD_RULES[module]; conf = "med"; grade = "[静态推断]"; source = "module"
        name = "sub_%08X" % e
        sem = "源文件 %s 归属 %s（模块线索，语义[未证]）" % (module, SUBSYS_NAME[sub])
    # 5) 强字符串
    elif strings and str_to_sub(strings):
        sub = str_to_sub(strings)
        strong = any(k in strings for k in IMPORTANT_STR)
        conf = "med" if strong else "low"
        grade = "[未证]"; source = "string"
        name = "sub_%08X" % e
        kw = next((k for k,_ in STR_RULES if k in strings), "")
        sem = "引用 '%s' → %s（字符串线索，语义[未证]）" % (kw, SUBSYS_NAME[sub])
    # 6) 亲戚投票
    elif vote:
        sub, n = vote.most_common(1)[0]
        conf = "low"; grade = "[未证]"; source = "relay_vote"
        name = "sub_%08X" % e
        sem = "调用图邻居 %d 票指向 %s（弱信号[未证]）" % (n, SUBSYS_NAME[sub])
    # 7) 导入 API
    elif imp in IMP_RULES:
        sub = IMP_RULES[imp]; conf = "low"; grade = "[未证]"; source = "import"
        name = "sub_%08X" % e
        sem = "导入 %s → %s（弱信号[未证]）" % (imp, SUBSYS_NAME[sub])
    # 8) 零证据
    else:
        sub, conf, grade, source = "S22", "low", "[未证]", "none"
        name = "sub_%08X" % e
        sem = "无可用静态信号，归 S22 兜底（无法归类）[未证]"

    evpath = "EVIDENCE/classification_trace.tsv#%08X" % e
    rows.append((e, sub, name, sem, grade, evpath))
    trace.append(dict(entry=e, sub=sub, conf=conf, grade=grade, source=source,
                      name=name, sem=sem,
                      self_strong="|".join(selfstrong), self_ledger="|".join(selfledger),
                      vt=";".join("%s:%d"%(c,s) for c,s,_ in vt),
                      module=module, strings=strings, imp=imp,
                      vote=";".join("%s:%d"%(k,v) for k,v in vote.most_common())))

# 写 coverage_delta.tsv（6 列，无表头）
with open(os.path.join(CARD, "coverage_delta.tsv"), "w", encoding="utf-8") as f:
    for e, sub, name, sem, grade, ev in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (e, sub, name, sem.replace("\t"," "), grade, ev))

# 写 trace（带表头）
with open(os.path.join(EVID, "classification_trace.tsv"), "w", encoding="utf-8") as f:
    cols = ["entry","sub","conf","grade","source","name","sem","self_strong","self_ledger",
            "vt","module","strings","imp","vote"]
    f.write("\t".join(cols)+"\n")
    for t in trace:
        f.write("\t".join(str(t[c]).replace("\t"," ") for c in cols)+"\n")

print("total", len(rows))
print("\n== by subsystem ==")
by = Counter(r[1] for r in rows)
for s in sorted(by):
    hi = sum(1 for t in trace if t["sub"]==s and t["conf"]=="high")
    print("%s %4d  high=%d  %s" % (s, by[s], hi, SUBSYS_NAME[s]))
print("\n== confidence ==", dict(Counter(t["conf"] for t in trace)))
print("== grade ==", dict(Counter(t["grade"] for t in trace)))
print("== source ==", dict(Counter(t["source"] for t in trace)))
print("high count =", sum(1 for t in trace if t["conf"]=="high"))

json.dump(dict(rows=rows, trace=trace), open(os.path.join(WORK,"classification.json"),"w",encoding="utf-8"), ensure_ascii=False)
