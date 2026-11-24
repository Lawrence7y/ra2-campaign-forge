#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C02 按 PLAN §1 S01-S22 分类（可复跑）。
多信号加权 + 确定性规则；输出 coverage_delta.tsv + EVIDENCE/classification_trace.tsv。
信号优先级（强→弱）：self_known(YRpp/kb 地址名) > vtable 类 > module 源文件 > 字符串关键词 > 亲戚名投票 > 导入API。
grade: [已证]=有明确地址名且类属一致; [静态推断]=类名/模块/强字符串; [未证]=弱信号/零证据。
"""
import os, json, re
from collections import Counter, defaultdict

ROOT  = r"D:\Project\ra2-campaign-forge"
CARD  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C02_census")
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

# ---- 类 -> (Sxx, 是否核心高置信) 有序包含匹配 ----
CLASS_RULES = [
 (["CampaignScoreClass","CampaignEndScoreClass","CarryoverClass","CampaignClass"], "S21", True),
 (["BulletClass","BulletTypeClass","DamageGroup"], "S13", True),
 (["ConnectionPointClass","EnumConnectionPointsClass","EnumConnectionsClass","IPXGlobalConnClass",
   "IPXConnClass","NullModemConnClass","ConnectionClass","CONNECTDATA","ControlNode","Reestablish"], "S18", True),
 (["CStreamClass","CommBufferClass"], "S17", True),
 (["CCINIClass"], "S04", True),
 (["CDFileClass","CCFileClass","FileStraw","FilePipe","Base64Pipe","BlowPipe","BufferPipe",
   "LCWPipe","LZOPipe","PKPipe","SHAPipe"], "S03", True),
 (["ShapeButtonClass","StaticButtonClass","TextButtonClass","ToggleClass","EditClass","GaugeClass",
   "TriColorGaugeClass","DropListClass","SliderClass","CheckListClass","ColorListClass","TextLabelClass",
   "SidebarClass","StripClass","SelectClass","ListClass","SBGadgetClass","GadgetClass","CCToolTip",
   "ControlClass","CounterClass","Dial8Class"], "S09", True),
 (["FoggedObjectClass"], "S08", True),
 (["ParticleSystemTypeClass"], "S20", True),
 (["MapClass","CellClass","Theater"], "S06", True),
 (["ConvertClass","VRGBClass","TacticalClass","DisplayClass","DDSURFACEDESC","Blitter","Blit"], "S07", True),
 (["BuildingTypeClass","CaptureManagerClass"], "S12", True),
 (["BuildingClass","TechnoTypeClass","TechnoClass","ObjectClass"], "S05", True),
 (["InfantryClass","UnitClass","AircraftClass"], "S10", True),
 (["VectorClass","DynamicVectorClass","TypeList","Point3D"], "S22", False),  # 通用容器兜底
]
def class_to_sub(cls):
    # 剥离模板容器前缀后仍对元素匹配（元素类型优先）
    for keys, s, core in CLASS_RULES:
        for k in keys:
            if k in cls:
                return s, core
    if cls == "CD": return "S03", True
    return None, False

# ---- 已知名 -> Sxx（按命名空间/类前缀） ----
NAME_CLASS_RULES = [
 (r"^Campaign|^CampaignScore|^Carryover", "S21"),
 (r"^Bullet|^DamageGroup|^Weapon|^Warhead", "S13"),
 (r"^CStream|^Here_I_Am|^Swizzle", "S17"),
 (r"^CCINIClass::", "S04"),
 (r"^CCFileClass::|^FileSystem::|^CDFileClass::", "S03"),
 (r"^CellClass::|^MapClass::|^Theater::", "S06"),
 (r"^ConvertClass::|^Surface::|^Drawing::|^YRDDraw::|^TacticalClass::", "S07"),
 (r"^BuildingClass::|^BuildingTypeClass::|^TechnoClass::|^CaptureManagerClass::", "S12"),
 (r"^UI::|^StringTable::|^TransitionTimer::", "S09"),
 (r"^VocClass::|^Audio|^EVA", "S19"),
 (r"^AbstractClass::", "S05"),
]
BAD_TOKENS = {"setne","this","ReadString","WriteString","ReadInteger","WriteInteger","this"}
def clean_known(names):
    out = []
    for n in names:
        if n in BAD_TOKENS: continue
        if "::" not in n and n not in ("Here_I_Am","noinit_t"): continue
        out.append(n)
    return out
def name_to_sub(nm):
    if nm == "Here_I_Am": return "S17"
    for pat, s in NAME_CLASS_RULES:
        if re.match(pat, nm): return s
    return None

# ---- 字符串关键词 -> Sxx ----
STR_RULES = [
 ("EVA_", "S19"), ("VocClass","S19"),
 ("CampScor","S21"),("coopsave","S21"),("coopcamp","S21"),("Campaign","S21"),
 ("CurrentMap","S21"),("Map%d","S21"),("Score","S21"),("Kills","S21"),("Built","S21"),
 ("Connect","S18"),("wolhost","S18"),("wolacpt","S18"),
 ("Conquer","S01"),("TXT_","S01"),
 ("Credits","S09"),
 ("FOG.SHP","S08"),("SHROUD.SHP","S08"),
 ("DDRAW.DLL","S07"),(".SHP","S07"),(".SHA","S07"),("Image","S07"),("ToTile","S07"),
 ("Digest","S02"),("%08X","S02"),
 ("BUILDNGZ","S12"),("WRENCH","S12"),("Foundation","S12"),("Power","S12"),
 ("BuildCat","S04"),("Tiberium","S06"),("House","S04"),("Color","S04"),
]
def str_to_sub(s):
    for k, sub in STR_RULES:
        if k in s: return sub
    return None

# ---- 源文件模块 -> Sxx ----
MOD_RULES = {"CampScor.cpp":"S21","coopcamp.cpp":"S21","Connect.CPP":"S18",
             "Conquer.CPP":"S01","Credits.CPP":"S09"}
# ---- 导入 API -> Sxx ----
IMP_RULES = {"MessageBoxA":"S09","GetDlgItem":"S09","FindFirstFileA":"S03","FindNextFileA":"S03",
             "FindClose":"S03","FindResourceA":"S09","DeviceIoControl":"S03","CoCreateInstance":"S18",
             "MapViewOfFileEx":"S17","UnmapViewOfFile":"S17","timeGetTime":"S01",
             "InterlockedIncrement":"S02","InterlockedDecrement":"S02"}
IMPORTANT_STR = ["CampScor","coopcamp","Campaign","Conquer","Connect","Credits","DDRAW.DLL","EVA_","FOG.SHP","SHROUD.SHP"]

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
    selfk = clean_known(f["self_known"])
    vt = f["vt"]                      # [[cls,slot,vt],...]
    module = f["module"]
    strings = f["strings"]
    imp = f["first_import"]
    vote = rel_vote(f)

    sub = None; conf = None; grade = None; source = None; name = ""; sem = ""

    # 1) 明确地址名
    if selfk:
        nm = selfk[0]
        sub = name_to_sub(nm)
        # 若类名也能定位且名字归属弱，用类名补强
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
            # 取最具代表性的 (cls,slot)：优先该类==sub
            pick = next((x for x in cands if x[0][0] == sub), cands[0])
            cls, slot = pick[1], pick[2]
            name = "%s::slot%d" % (cls, slot)
            source = "vtable"
            sem = "%s 虚表槽 %d(+0x%X)：%s 方法（槽语义未证）" % (cls, slot, slot*4, SUBSYS_NAME[sub])
        else:
            sub, conf, grade, source = "S22","low","[未证]","vtable-unmapped"
            cls, slot = vt[0][0], vt[0][1]
            name = "%s::slot%d" % (cls, slot)
            sem = "%s 虚表槽，类名无法映射到 S01-S22（待人工）" % cls
    # 3) 源文件模块
    elif module in MOD_RULES:
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
        kw = next((k for k,_ in STR_RULES if k in strings), "")
        sem = "引用 '%s' → %s（字符串线索）" % (kw, SUBSYS_NAME[sub])
    # 5) 亲戚投票
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

# 写 coverage_delta.tsv（卡要求 6 列，无表头）
with open(os.path.join(CARD, "coverage_delta.tsv"), "w", encoding="utf-8") as f:
    for e, sub, name, sem, grade, ev in rows:
        f.write("%08X\t%s\t%s\t%s\t%s\t%s\n" % (e, sub, name, sem.replace("\t"," "), grade, ev))

# 写 trace（带表头）
with open(os.path.join(EVID, "classification_trace.tsv"), "w", encoding="utf-8") as f:
    cols = ["entry","sub","conf","grade","source","name","sem","self_known","vt","module","strings","imp","vote"]
    f.write("\t".join(cols)+"\n")
    for t in trace:
        f.write("\t".join(str(t[c]).replace("\t"," ") for c in cols)+"\n")

# 统计
print("total", len(rows))
print("\n== by subsystem ==")
for s, n in Counter(r[1] for r in rows).most_common():
    hi = sum(1 for t in trace if t["sub"]==s and t["conf"]=="high")
    print("%s %4d  high=%d  %s" % (s, n, hi, SUBSYS_NAME[s]))
print("\n== confidence ==", Counter(t["conf"] for t in trace))
print("== grade ==", Counter(t["grade"] for t in trace))
print("== source ==", Counter(t["source"] for t in trace))
print("high count =", sum(1 for t in trace if t["conf"]=="high"))

json.dump(dict(rows=rows, trace=trace), open(os.path.join(WORK,"classification.json"),"w",encoding="utf-8"), ensure_ascii=False)
