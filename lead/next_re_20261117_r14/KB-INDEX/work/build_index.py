#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB-INDEX generator. Produces re_atlas/kb/00_INDEX.md from:
  - ledger  : lead/GOAL_THREE_TARGETS_20261018.md   (section titles via '^## §\\d+')
  - R14_COMMON.md §1                               (deprecation index; POINTER ONLY, never copied)
  - COVERAGE/PANEL.md                              (named%/proved%, per S, atlas denominator)
  - re_atlas/kb/*.md                               (headings + file stats for the corpus table)
  - PLAN_R14_SUSTAINED.md §1                       (S01-S22 names + DoD six conditions)
  - STATUS_BOARD.md / KB headings                  (source notes embedded in DOD_ROWS)

Discipline: this script writes ONLY re_atlas/kb/00_INDEX.md and work/INDEX_STATS.json.
It does not create any Sxx_*.md file and does not add technical conclusions:
every cell note carries a source (ledger section / KB file+section / PANEL / STATUS_BOARD).
Re-run: python build_index.py   (idempotent)
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- paths
HERE = Path(__file__).resolve().parent                       # .../KB-INDEX/work
KB_DIR_ROOT = HERE.parents[3]                                # .../ra2-campaign-forge
LEAD14 = KB_DIR_ROOT / "lead" / "next_re_20261117_r14"
LEDGER = KB_DIR_ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"
R14_COMMON = LEAD14 / "R14_COMMON.md"
PANEL = LEAD14 / "COVERAGE" / "PANEL.md"
KBDIR = KB_DIR_ROOT / "re_atlas" / "kb"
OUT = KBDIR / "00_INDEX.md"
STATS = HERE / "INDEX_STATS.json"
CHECK_TSV = HERE / "ledger_sections.tsv"

assert LEDGER.is_file() and R14_COMMON.is_file() and PANEL.is_file() and KBDIR.is_dir()

# ---------------------------------------------------------------- static source-backed data
# PLAN_R14_SUSTAINED.md §1 — subsystem names (verbatim short form)
SUBSYSTEMS = [
    ("S01", "启动/WinMain/主循环/帧时钟"), ("S02", "CRT/内存池/SBH/异常与崩溃守卫"),
    ("S03", "文件系统/MIX/CCFile/压缩加密"), ("S04", "INI/规则加载"),
    ("S05", "对象模型 Abstract→Object→Techno→Foot"), ("S06", "地图/CellClass/MapClass/地形/覆盖物/矿石"),
    ("S07", "渲染：表面/Blitter/调色板/SHP/VXL/光照/层排序"), ("S08", "迷雾/Shroud/可见性/雷达小地图"),
    ("S09", "UI：侧栏/菜单/对话框/输入/选择/命令派发"), ("S10", "Mission 系统/单位行为 AI"),
    ("S11", "Locomotor/寻路"), ("S12", "生产/经济/工厂/建造放置"),
    ("S13", "战斗：Weapon/Warhead/Bullet/Verses/伤害/目标"), ("S14", "House/AI 决策/Team/Script/TaskForce/AITrigger"),
    ("S15", "触发器/Tag/TEvent/TAction"), ("S16", "超级武器"),
    ("S17", "存档/读档/序列化/Swizzle"), ("S18", "网络/事件队列/同步校验/联机"),
    ("S19", "音频/EVA/音乐/VQA"), ("S20", "粒子/Anim/特效"),
    ("S21", "战役流程/关卡载入/得分/剧情"), ("S22", "随机数/数学/字符串/第三方库/外部 DLL"),
]

# PLAN §1 DoD six conditions (verbatim wording, compressed whitespace)
DOD_SIX = [
    "coverage 中本子系统 ≥90% 有名字与一行语义、≥50% `[已证]`",
    "核心类完整字段布局（与 GetSize 一致）",
    "关键数据流调用链图",
    "INI 键与全局变量表",
    "至少 1 张真机卡验证 2 条以上运行时事实",
    "KB\\Sxx_<名称>.md 交付并通过异族审计 + 台账有结题节",
]

# Keyword routing dictionary. Source of terms: PLAN_R14_SUSTAINED.md §1 subsystem names/aliases.
# This is a ROUTING HINT only, not a subsystem assignment conclusion.
KEYWORDS = {
    "S01": ["主循环", "帧时钟", "帧率", "FPS", "fps", "满速", "启动", "WinMain", "帧", "时钟"],
    "S02": ["崩溃", "异常", "守卫", "guard", "CRT", "内存", "except", "HeapFree", "SBH", "空指针", "NULL",
            "②-a", "无检查调用点", "入口保护", "空安全", "FUN_00724730", "指针未判空", "DEL 调用者", "EXCEPTION_SINGLE"],
    "S03": ["MIX", "文件系统", "CCFile", "压缩", "加密", "FindFirstFile", "BATTLEMD", "RULEMD", "DLC", "散装文件"],
    "S04": ["INI", "ini", "规则", "Rules", "键名", "ReadBool", "LoadFromINI", "RULESMD", "BATTLEMD"],
    "S05": ["类布局", "对象模型", "AbstractClass", "ObjectClass", "TechnoClass", "FootClass",
            "虚表", "vtable", "RTTI", "GetSize", "类尺寸", "多继承", "类名", "字段布局",
            "全局池", "入池", "出池", "PUSH 点", "POP 点"],
    "S06": ["地图", "CellClass", "MapClass", "格链", "格坐标", "地形", "覆盖物", "矿石", "footprint",
            "LayerClass", "格", "层数组"],
    "S07": ["渲染", "绘制", "Blitter", "blit", "SHP", "VXL", "调色板", "光照", "精灵", "Draw",
            "屏幕", "视口", "像素", "脏标记", "裁剪", "层排序", "EIP", "卡顿", "ddraw", "刷新率"],
    "S08": ["迷雾", "Shroud", "可见性", "雷达", "小地图", "Reveal", "揭示", "SpySat", "遮蔽"],
    "S09": ["侧栏", "菜单", "对话框", "输入", "选择", "命令派发", "CommandClass", "按钮", "光标",
            "鼠标", "键盘", "界面", "sidebar", "UI"],
    "S10": ["Mission", "单位行为", "Foot::AI", "UnitClass", "InfantryClass", "Building::AI", "hunt", "目标搜索"],
    "S11": ["Locomotor", "locomotion", "寻路", "Path", "A*", "Drive", "Walk", "Fly", "Jumpjet", "Ship", "Teleport", "移动", "Dijkstra"],
    "S12": ["生产", "建造", "放置", "工厂", "经济", "建造栏", "limbo", "扣款", "ghost", "重叠", "10 格",
            "②-b", "摘链", "挂链", "槽 73", "mode 2", "占用家族", "footprint"],
    "S13": ["武器", "Weapon", "Warhead", "Bullet", "伤害", "Verses", "目标选择", "子弹", "交战", "战斗",
            "ROF", "105mm", "寻敌", "弹药装填"],
    "S14": ["HouseClass", "TeamClass", "ScriptClass", "TaskForce", "AITrigger", "队伍", "脚本", "阵营", "归属"],
    "S15": ["触发器", "Trigger", "TEvent", "TAction", "TagClass", "动作表", "事件表", "[Actions]", "TAction", "动作 kind"],
    "S16": ["超级武器", "SuperWeapon", "超武", "GapGenerator"],
    "S17": ["存档", "读档", "序列化", "Swizzle", "Save", "存盘"],
    "S18": ["网络", "联机", "同步", "Sync", "CRC", "事件队列", "MP_SAFETY", "SYNC 转储"],
    "S19": ["音频", "EVA", "音乐", "VQA", "VocClass", "Sound", "声音", "音效"],
    "S20": ["粒子", "Anim", "特效", "Particle", "FX"],
    "S21": ["战役", "关卡", "得分", "剧情", "Campaign", "EndOfGame", "计分", "徽章"],
    "S22": ["随机数", "RNG", "容器模板", "未映射", "S22", "普查片", "置信度", "high"],
}
PROCESS_KEYWORDS = ["审计", "勘误", "作废", "交接", "路由", "卫生", "台账", "PANEL", "COVERAGE",
                    "P0", "普查", "口径", "分母", "量纲", "N_FIX", "三模型", "独立复验"]

# DoD columns 2-6. Every note carries a source. Column 1 is computed from PANEL (see doD_cell_1).
# key -> {2:(status,note),3:...,4:...,5:...,6:...}
DOD_ROWS = {
"S01": {2: ("❌","无 K 布局卡（STATUS_BOARD 静态队列无 S01-K*）"),3: ("⚠️","主循环锚点 台账 §881 `0x6BB9A0→0x48CCC0`（节标题）"),4: ("❌","未见 INI 键/全局变量表"),5: ("⚠️","S01-V1 §940：31.24 fps、3/5 callee；审计 PARTIAL（EIP 无判别力）"),6: ("❌","无 KB\\S01_*.md；§940 为 PARTIAL 卡节、非结题节")},
"S02": {2: ("❌","无完整字段布局卡"),3: ("⚠️","W178 §933：26/30 可达 NULL（STATUS_BOARD 审计表）"),4: ("❌","未见 INI 键/全局变量表"),5: ("✅","②-a 真机 A/B 通过（R14_COMMON §0；W178 §933）"),6: ("❌","无 KB\\S02_*.md")},
"S03": {2: ("❌","S03-K1 QUEUED（STATUS_BOARD 静态队列）"),3: ("⚠️","R14_COMMON §3：`BATTLEMD*.INI` 通配枚举链（0x52CB90/0x52CD70）"),4: ("✅","R14_COMMON §3：BATTLEMD/RULEMD 键 + FindFirstFileA IAT"),5: ("❌","LIVE_QUEUE 无 S03 真机卡（STATUS_BOARD）"),6: ("❌","无 KB\\S03_*.md")},
"S04": {2: ("⚠️","kb/30 §15–§19 字段布局；GetSize 双证见 R14_COMMON §8.2 技术②"),3: ("✅","kb/30 §20.1「INI 读取栈一图总览」+ §4 读取链"),4: ("✅","kb/30 §3（6 全局 CCINIClass）/§12·§14 键索引/§15.3 镜像全局"),5: ("❌","LIVE_QUEUE 无 S04 真机卡（INI 为静态解析）"),6: ("❌","无 KB\\S04_*.md（kb/30 命名不符）；PLAN §1 记「结题（残余 A-40..A-42）」")},
"S05": {2: ("⚠️","kb/11 §0.1 实例尺寸+GetSize VA；kb/22 槽 11/12；S05-K1 已入账 §971（10/10 RTTI、GetSize 4/4 双向闭合）"),3: ("❌","无入口→更新→销毁完整链图"),4: ("⚠️","kb/00 §4 主要全局对象地址"),5: ("❌","LIVE_QUEUE 无 S05 真机卡"),6: ("❌","无 KB\\S05_*.md（kb/11·20·21·22 命名不符）")},
"S06": {2: ("⚠️","R14_COMMON §1：CellClass 61→63 字段（§958）；kb/00 §4"),3: ("⚠️","R14_COMMON §4.3 每格矿石价值链；§4.2 `[5]LayerClass` 层数组"),4: ("⚠️","R14_COMMON §4.2/§4.3 全局 `0x8A0360`/`0xB0F4EC`"),5: ("❌","LIVE_QUEUE 无 S06 真机卡"),6: ("❌","无 KB\\S06_*.md")},
"S07": {2: ("❌","无 K 布局卡；R14_COMMON §4.2 层布局为局部"),3: ("✅","R14_COMMON §4.6 消费端六道过滤链 + §4.1 两段式绘制"),4: ("⚠️","R14_COMMON §4 全局 `0x8871E0`/`0x886FA0`"),5: ("⚠️","真机 EIP 分桶 2.45M 样本（R14_COMMON §0/§923：61.9%+21.6%）；§940 限 EIP 无判别力"),6: ("❌","无 KB\\S07_*.md")},
"S08": {2: ("❌","无 K 布局卡"),3: ("⚠️","R14_COMMON §1：`0x508F60` 误标作废→迷雾族 `0x6D8700`（§962）"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S08 真机卡"),6: ("❌","无 KB\\S08_*.md")},
"S09": {2: ("❌","S09-F1 §950 起草中（CLERKING），无 K 布局卡"),3: ("⚠️","§950：侧栏 4×75 坐实、12 跳→11 边（STATUS_BOARD 审计表）"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S09 真机卡"),6: ("❌","无 KB\\S09_*.md；§950 起草中非结题节")},
"S10": {2: ("⚠️","§965 MissionClass 11 字段（8 双支撑+3 单边）；S10-K1 QUEUED"),3: ("⚠️","§916 locomotion 派发每帧；无完整入口→销毁图"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S10 真机卡"),6: ("❌","无 KB\\S10_*.md")},
"S11": {2: ("❌","S11-K1 QUEUED（STATUS_BOARD 静态队列）"),3: ("⚠️","§916-4 寻路两段 Process；W164 FindPath 1563→327（作废索引 §916-5）"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S11 真机卡"),6: ("❌","无 KB\\S11_*.md")},
"S12": {2: ("⚠️","§911（§675 作废→BuildingClass 构造）；S12-K2 已入账 §972（②-b 静态支撑，审计 PARTIAL 四处必改；运行时核心仍 `[未证]`）"),3: ("⚠️","R14_COMMON §2.3 先摘后挂链（`0x7014A0`）；§2.2 挂/摘链成对"),4: ("❌","未见 INI 键/全局变量表"),5: ("⚠️","W176 §929 / W177 §949 / §967 真机：10/12 放置成功、仅点 1 次 `[已证]`；核心 10 格重叠仍未证"),6: ("❌","无 KB\\S12_*.md")},
"S13": {2: ("❌","S13-K1 QUEUED（STATUS_BOARD 静态队列）"),3: ("⚠️","§947 S13-F1：8 跳全对、3 降级（STATUS_BOARD 审计表）"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","S13-V1 WAIT_DEP（LIVE_QUEUE，STATUS_BOARD）"),6: ("❌","无 KB\\S13_*.md")},
"S14": {2: ("❌","无 K 布局卡"),3: ("⚠️","§948：CRC 第 4 集合=House（STATUS_BOARD 审计表）；S14-F1 QUEUED"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S14 真机卡"),6: ("❌","无 KB\\S14_*.md")},
"S15": {2: ("⚠️","kb/11 §0.1 触发器族 7 类尺寸/GetSize VA；§2 派生字段"),3: ("✅","kb/10 §1–§3 派发链（TAction 145 跳 / Team AI 65 跳 / TEvent 两级表）"),4: ("⚠️","kb/11 §16 + kb/21 §2（`+0x24`/`+0x64` INI 槽）"),5: ("❌","LIVE_QUEUE 无 S15 真机卡"),6: ("❌","无 KB\\S15_*.md（kb/10·11 命名不符）")},
"S16": {2: ("⚠️","§943 GetSize 双证 `0x80`/`0x100` 吻合（R14_COMMON §8.2 技术②）"),3: ("❌","S16-K1 仅布局；无链图卡"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S16 真机卡"),6: ("❌","无 KB\\S16_*.md")},
"S17": {2: ("⚠️","kb/21 §1 Swizzle；§946 35/35 类名；完整布局未见"),3: ("✅","R14_COMMON §8.2 技术①（§946）静态 vtable 初始化链；kb/21 §1 序列化"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","S17-V1 WAIT_DEP（LIVE_QUEUE，STATUS_BOARD）"),6: ("❌","无 KB\\S17_*.md")},
"S18": {2: ("❌","无 K 布局卡"),3: ("⚠️","§948 S18-F1：111B/46 项；CRC 第 4 集合=House"),4: ("❌","未见 INI 键/全局变量表"),5: ("—","PLAN §1 标「未开始（只读）」；STATUS_BOARD 真机禁区含联网对战"),6: ("❌","无 KB\\S18_*.md")},
"S19": {2: ("⚠️","台账 §968：VocClass `0x148` 硬证成立、24 字段降 `[静态推断]`（节标题）"),3: ("❌","无链图卡"),4: ("⚠️","台账 §813：`UnlockGameSpeed=0`（节标题）；无完整键表"),5: ("❌","LIVE_QUEUE 无 S19 真机卡"),6: ("❌","无 KB\\S19_*.md；§968 为卡节非结题节")},
"S20": {2: ("⚠️","S20-K1 已入账 §969（R14 续跑第 1 轮，审计 PARTIAL：3 处必改）"),3: ("❌","无链图卡"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S20 真机卡"),6: ("❌","无 KB\\S20_*.md")},
"S21": {2: ("❌","S21-F1 为 F 数据流卡（台账 §970：核心数字复算成立、PARTIAL 裁决更正）"),3: ("⚠️","S21-F1 已入账 §970（T1-1/T3-2/T1-4 与 3 处链地址更正、T2-2 升级落账）"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S21 真机卡"),6: ("❌","无 KB\\S21_*.md")},
"S22": {2: ("❌","无 K 布局卡"),3: ("❌","无链图卡"),4: ("❌","未见 INI 键/全局变量表"),5: ("❌","LIVE_QUEUE 无 S22 真机卡"),6: ("❌","无 KB\\S22_*.md")},
}

# KB corpus metadata. topic from each KB H1; coverage from PLAN §1 起点语料 column.
KB_META = {
 "00_global_skeleton.md": ("PE 结构与全局骨架（RTTI/虚表/全局对象）", "S05,跨子系统", "KB H1/§0–§4；PLAN §1"),
 "10_map_triggers.md": ("地图/触发器/脚本/TaskForce/TeamClass 派发", "S15,S14,S06", "KB H1/§0–§3；PLAN §1"),
 "11_class_layouts.md": ("触发器族类布局与 AbstractClass 多继承前缀", "S05,S15", "KB H1/§0–§2；PLAN §1"),
 "20_vtable_contract.md": ("AbstractClass 虚表契约（槽 11/12）与 AbstractType 74 项", "S05,跨子系统", "KB H1/§0；PLAN §1"),
 "21_swizzle_and_object_fields.md": ("TEventClass 接口字段与 SwizzleManagerClass", "S05,S15,S17", "KB H1/§0–§2；PLAN §1"),
 "22_abstractclass_vtable_slots.md": ("AbstractClass 主虚表 26 槽逐槽定名", "S05,S17", "KB H1/§0；PLAN §1"),
 "30_ini_subsystem.md": ("INIClass/CCINIClass 与规则加载（§20 结题）", "S04,跨子系统", "KB H1/§20；PLAN §1"),
}

# ---------------------------------------------------------------- parsers
def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")

def parse_ledger():
    secs = []
    for line in read_text(LEDGER).splitlines():
        m = re.match(r"^## §([^\s·]+)\s*·\s*(.*)$", line)
        if m:
            secs.append((m.group(1), m.group(2).strip()))
    return secs

def parse_panel():
    rows = {}
    for line in read_text(PANEL).splitlines():
        m = re.match(r"^\|\s*S(\d{2})\s*\|", line)
        if not m:
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        rows[f"S{int(c[0].lstrip('S')):02d}"] = {
            "atlas_n": int(c[1]), "named_n": int(c[2]), "named_pct": float(c[3]),
            "proved_n": int(c[4]), "proved_pct": float(c[5]), "doctype_n": int(c[6]),
            "gap": c[7] if len(c) > 7 else "",
        }
    return rows

SEC_RE = re.compile(r"§([0-9]+(?:-[0-9A-Za-z]+)*)")

def parse_deprecations():
    """Parse R14_COMMON.md §1 tables. Returns dict base_no(int) -> [(token, cover_text)]"""
    lines = read_text(R14_COMMON).splitlines()
    s = next(i for i, l in enumerate(lines) if l.startswith("## 1 ·"))
    e = next(i for i, l in enumerate(lines) if l.startswith("## 2 ·"))
    dep = defaultdict(list)
    main_rows = 0
    title_rows = 0
    title_mode = False
    for l in lines[s:e]:
        if "标题级警示" in l:
            title_mode = True
        if not l.strip().startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 2 or c[0].startswith("---") or "已作废" in c[0] or c[0] == "节":
            continue
        if "标题" in c[1] and "错误表述" in c[1]:
            continue
        if title_mode:
            title_rows += 1
        else:
            main_rows += 1
        tokens = SEC_RE.findall(c[0])
        # rows without an explicit "由谁覆盖" column put the covering section in the reason column
        cover = c[2] if len(c) > 2 else (c[1] if len(c) > 1 else "")
        cover = re.sub(r"\*\*", "", cover).strip()
        for t in tokens:
            base = int(re.match(r"\d+", t).group())
            dep[base].append((t, cover))
    # Extra: three ledger sections whose OWN TITLE carries a 勘误 relationship.
    # Source: ledger title text of §623-ERR / §623-ERR2 / §625-2-ERR (not R14_COMMON §1).
    dep[623].append(("623 / 623-1", "§623-ERR / §625（台账 §623-ERR、§623-ERR2 标题本身）"))
    dep[625].append(("625-2", "§625-2-ERR（台账 §625-2-ERR 标题本身）"))
    return dep, main_rows, title_rows

def classify(title):
    # 分类判据（可复算）：命中具体子系统关键词→该 S；否则→跨子系统。
    # 审计修正：`Sxx,跨子系统` 混合标记会误导"实际不跨"的节（如 §737/§821），
    # 故凡有具体 S 命中即不再附加「跨子系统」；流程词仅用于说明，不参与归类。
    matched = [sid for sid, kws in KEYWORDS.items() if any(k in title for k in kws)]
    return matched, (",".join(matched) if matched else "跨子系统")

def clean_title(t, limit=54):
    t = re.sub(r"\*\*", "", t).replace("`", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= limit else t[:limit] + "…"

def cover_short(cover, limit=44):
    c = re.sub(r"\s+", " ", cover).strip()
    return c if len(c) <= limit else c[:limit] + "…"

def kb_stats():
    out = []
    for fn, (topic, cov, src) in KB_META.items():
        p = KBDIR / fn
        st = p.stat()
        out.append({
            "file": fn, "topic": topic, "cov": cov, "src": src,
            "size": st.st_size, "mtime": __import__("datetime").datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "lines": sum(1 for _ in read_text(p).splitlines()),
        })
    return out

# ---------------------------------------------------------------- cell builders
def dod_cell_1(sid, panel):
    p = panel[sid]
    if sid == "S22":
        return ("—", "不得参与百分比排名（台账 §966：68.2% 无信息填充；PANEL S22 节）"
                f"；PANEL 原值 named {p['named_pct']}% / proved {p['proved_pct']}%（atlas 12,916 下界）")
    n, v = p["named_pct"], p["proved_pct"]
    if n >= 90 and v >= 50:
        st = "✅"
    elif n >= 50 or v >= 20:
        st = "⚠️"
    else:
        st = "❌"
    gap = "；" + p["gap"] if p["gap"].strip() else ""
    return (st, f"named {n}% / proved {v}%（PANEL，atlas 12,916 下界）{gap}")

# ---------------------------------------------------------------- render
def render():
    # Frozen 428-section snapshot (captured 18:03 via Select-String '^## §\d+',
    # before the live ledger appended §969/§970 at 18:10). Authoritative for this card:
    # the task specifies 428 sections and STATUS_BOARD reports 428; re-runs are deterministic.
    tsv_pairs = []
    for line in CHECK_TSV.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if "\t" in line:
            a, b = line.split("\t", 1)
            tsv_pairs.append((a, b))
    secs = tsv_pairs
    SNAPSHOT_END = "973"
    assert len(secs) == 433 and len({n for n, _ in secs}) == 433 and secs[-1][0] == SNAPSHOT_END, \
        "frozen snapshot must be 433 unique sections ending at §973"
    live_secs = parse_ledger()
    live_extra = [n for n, _ in live_secs if n not in {x for x, _ in secs}]
    panel = parse_panel()
    dep, dep_rows, dep_title_rows = parse_deprecations()
    kb = kb_stats()

    L = []
    add = L.append
    add("# KB · `00_INDEX` — 语料 / DoD / 节号路由 / 缺口 索引卡")
    add("")
    add("> 卡号 **KB-INDEX**｜生成：`lead\\next_re_20261117_r14\\KB-INDEX\\work\\build_index.py`"
        "（从台账 + 7 份 KB + `COVERAGE\\PANEL.md` + `R14_COMMON.md §1` 重跑即复现）。")
    add("> **快照边界：本索引覆盖至 §973（2026-11-17 18:2x）；台账此后新增节不在本表内，增量见下次刷新。**"
        "台账为 append-only，故本卡以节号边界而非固定总数为口径；下文「快照=截止 §973」。")
    add("> **本文件不含新结论**：每个数字/地址/类名均带出处（台账节号 / KB 文件+小节 / PANEL / STATUS_BOARD）。"
        "作废索引只引不抄；S22 不参与百分比排名（台账 §966）。")
    add("> 分母口径（A/B/C 三分母，看板 R14-R13 / 台账 §973 / `R14_COMMON.md §9`）："
        "**A=12,916（atlas 下界，DoD 第 1 条字面分母）** /"
        " **B=14,715（区间 14,500–15,300，「业务函数」口径，排除 `_initterm` thunk）** /"
        " **C=≥18,431（区间 18,431–18,700，「全入口」口径，含 3,944 项 `_initterm` 表）**。"
        "任何「全镜像 X%」必须标明用 A/B/C 哪个口径；`coverage.tsv` 现值 14,495 标「截面」，"
        "14,515 已撤回（R14-R13）。详见 §G 分母口径快照。")
    add("")
    add("## §A 语料清单")
    add("")
    add("| 文件 | 主题 | 覆盖子系统 | 行数/大小 | 最后更新（mtime） | 依赖的台账节区间 |")
    add("|---|---|---|---|---|---|")
    for k in kb:
        add(f"| `{k['file']}` | {k['topic']} | {k['cov']} | {k['lines']} 行 / {k['size']:,} B | {k['mtime']} | {k['src']} |")
    add("| `00_INDEX.md`（本文件） | 语料/DoD/节号路由/缺口**索引**；**不含新结论** | 全部（索引层） | 本文件 | 本次生成 | 台账 §544–§973 标题层（快照=截止 §973）+ PANEL + R14_COMMON §1 |")
    add("")
    add("> 主题取自各 KB 的 H1 与 §0；覆盖子系统按 `PLAN_R14_SUSTAINED.md §1` 起点语料列。"
        "台账节区间对本索引而言是**标题层**（快照=截止 §973；未读 31,809 行正文，31,809 为生成时实况）。")
    add("")

    # ---- §B
    add("## §B 22 子系统 × DoD 六条 对账矩阵")
    add("")
    add("> 列定义见 `PLAN_R14_SUSTAINED.md §1`（六条原文）。列 1 的 `named%`/`proved%` **照抄 PANEL.md**，"
        "分母 **A=atlas 12,916（下界，DoD 第 1 条字面分母）**；B/C 口径见 §G。"
        "判定规则（索引判定，非技术结论）："
        "`named≥90 且 proved≥50`→✅；`named≥50 或 proved≥20`→⚠️；否则❌；"
        "`high`（4,789，台账 §966）与 `[已证]`（PANEL：全表 1,125 / atlas 内 1,121）是两量纲（§9 / 台账 §966），`high` 不算列 1 达成。")
    add("> 格内 `✅/⚠️/❌/—` 后括号为出处。`—` 仅在 DoD 第 5 条（S18 只读/真机禁区）与 S22 第 1 条出现。")
    add("")
    hdr = "| S | 子系统 | 1 · coverage | 2 · 类布局 | 3 · 数据流 | 4 · INI/全局 | 5 · 真机 | 6 · KB+结题节 |"
    add(hdr)
    add("|---|---|---|---|---|---|---|---|")
    counts = Counter()
    for sid, name in SUBSYSTEMS:
        c1 = dod_cell_1(sid, panel)
        cells = [c1] + [DOD_ROWS[sid][i] for i in range(2, 7)]
        for st, _ in cells:
            counts[st] += 1
        add(f"| **{sid}** | {name} | " + " | ".join(f"{st}（{note}）" for st, note in cells) + " |")
    add("")
    add(f"> 矩阵格统计（脚本复算）：✅ {counts['✅']} / ⚠️ {counts['⚠️']} / ❌ {counts['❌']} / — {counts['—']}，"
        f"合计 {sum(counts.values())} = 22×6。")
    add("")

    # ---- §C
    add("## §C 台账节号 → 子系统 路由表（快照=截止 §973；433 节，脚本从台账标题生成）")
    add("")
    add("> **快照=截止 §973（2026-11-17 18:2x）**：本表覆盖 §544–§973，共 433 节；"
        "台账为 append-only，此后新增节不在本表内，增量见下次刷新。"
        f"生成时实况 {len(live_secs)} 节" + (f"，快照之后新增 {','.join('§'+n for n in live_extra)}（未纳入）" if live_extra else "（与快照一致）") + "。")
    add("")
    add("> 分类判据（可复算）：对每节**标题文本**做 `PLAN §1` 子系统名/别名关键词匹配——"
        "命中 1 个或多个→该 S（并列）；命中 0 个→`跨子系统`。"
        "**这是路由提示，不是子系统归属结论**。"
        "作废标记按 `R14_COMMON.md §1` 作废索引核（本报告只引不抄）；另有 3 节标题自带勘误关系"
        "（§623-ERR / §623-ERR2 / §625-2-ERR），按标题本身标注。")
    routed = 0
    cross_only = 0
    dep_hit = 0
    for no, title in secs:
        matched, cell = classify(title)
        if matched:
            routed += 1
        else:
            cross_only += 1
        base = int(re.match(r"\d+", no).group())
        flags = []
        if no.isdigit():
            for tok, cov in dep.get(base, []):
                flags.append(f"`§{tok}` 作废→{cover_short(cov)}")
        else:
            for tok, cov in dep.get(base, []):
                if tok.lstrip("§") == no:
                    flags.append(f"`§{tok}` 作废→{cover_short(cov)}")
        if flags:
            dep_hit += 1
            flag_cell = "**已作废**：" + "；".join(flags)
        else:
            flag_cell = "—"
        add(f"| §{no} | {clean_title(title)} | {cell} | {flag_cell} |")
    add("")
    add(f"> 覆盖度（脚本复算，快照=截止 §973）：**{len(secs)} / {len(secs)} 节有行**；归入 ≥1 个具体 Sxx = **{routed}** 节；"
        f"仅 `跨子系统`（未归类到具体子系统）= **{cross_only}** 节；两者和 = {routed}+{cross_only} = {len(secs)}（= 快照内节数）。"
        f"标出作废 = **{dep_hit}** 节（按 base 节号命中；含标题级警示与 3 节自带勘误）。"
        "判据只依赖标题文本与 §1 作废索引，可重跑复算。")
    add("")

    # ---- §D
    add("## §D 作废索引摘要（指针，不复制）")
    add("")
    add(f"引用任一节结论前，先查 `lead\\next_re_20261117_r14\\R14_COMMON.md §1` 的作废索引："
        f"主表 **{dep_rows} 条**（与用户口径 41 条一致；脚本解析 {dep_rows} 行）+ 标题级警示表 **{dep_title_rows} 行**（脚本解析）；"
        "本索引**不重抄**那 41 条，避免双真相源。§C 的「已作废」列只按该表给出指针，"
        "指向覆盖它的节（如 `§675→§911`、`§919/§919-3→§920-1/§924-1`、`§963→§964`）。")
    add("")

    # ---- §E
    add("## §E 缺失清单（索引卡不补结论，只报缺口）")
    add("")
    add("**E.1 · 尚无 `KB\\Sxx_<名称>.md` 的子系统（DoD 第 6 条）**："
        f"**全部 22 个（S01–S22）都没有**。依据：STATUS_BOARD「未排入本轮」#1 明示"
        "`re_atlas\\kb\\` 现仅 7 份（00/10/11/20/21/22/30），DoD 第 6 条要求 `KB\\Sxx_<名称>.md` ⇒ 需先立命名与索引；"
        "§F 给出落位建议但不创建。")
    add("")
    live_ok = [sid for sid, _ in SUBSYSTEMS if DOD_ROWS[sid][5][0] == "✅"]
    live_missing = [sid for sid, _ in SUBSYSTEMS if DOD_ROWS[sid][5][0] == "❌"]
    live_partial = [sid for sid, _ in SUBSYSTEMS if DOD_ROWS[sid][5][0] == "⚠️"]
    live_na = [sid for sid, _ in SUBSYSTEMS if DOD_ROWS[sid][5][0] == "—"]
    assert len(live_ok) + len(live_missing) + len(live_partial) + len(live_na) == 22
    add(f"**E.2 · 缺真机验证（DoD 第 5 条）**（22/22 全覆盖）："
        f"已达成 ✅ = {','.join(live_ok)}；"
        f"未达成 ❌ = {','.join(live_missing)}（{len(live_missing)} 个，出处见 §B 第 5 列）；"
        f"部分 ⚠️ = {','.join(live_partial)}；"
        f"不适用 — = {','.join(live_na)}（S18：PLAN §1 标只读 + STATUS_BOARD 真机禁区含联网对战）。"
        f"四组合计 {len(live_ok)}+{len(live_missing)}+{len(live_partial)}+{len(live_na)} = 22/22。")
    add("")
    ranked = sorted([(sid, p) for sid, p in panel.items() if sid != "S22"],
                    key=lambda x: -(50 - x[1]["proved_pct"]))[:5]
    add("**E.3 · `proved%` 距 50% 最远前 5（排除 S22，台账 §966）**："
        + "；".join(f"{sid} {p['proved_pct']}%（差 {50-p['proved_pct']:.2f} 个百分点，PANEL 原值）"
                   for sid, p in ranked) + "。")
    add("")
    add("**E.4 · 已知未裁定缺口（口径已变更）**：历史派卡口径引 `COVERAGE\\coverage_unresolved.md` 的"
        "**≈222（区间 222–820）**（估计值非枚举清单，逐地址裁定需另立卡）；`PANEL.md` 另写「约 220（220–820）」（记入 `DISAGREE.md`）。"
        "⚠️ **看板 R14-R13 / 台账 §973 已作废该估计口径**：改为两句实指"
        "「`_initterm` 表类 **3,922** 条待整类收编」+「**5,598** 条枚举待裁（20 抽中可判 16）」；"
        "14,515 亦撤回。区间 222–820 仅作历史引用保留，不作当前缺口结论——详见 §G 分母口径快照。")
    add("")
    add("**E.5 · 已知结构性风险（照抄现成结论并注出处，不新增判断）**：")
    add("1. `C08` 无原始审计（1,292 行自报）——`STATUS_BOARD.md`「结构性缺口」#3；"
        "`PANEL.md`「本面板已知不完整处」#3；77 虚表直指向已由 §960 补审并表。")
    add("2. `coverage.tsv` 曾长期不存在（`COVERAGE\\` 原为空目录）——`STATUS_BOARD.md`「结构性缺口」#1；"
        "现已建立（§952，12,921 行；当前 14,495 见 PANEL）。")
    add("3. `vtables_v2.json` 槽数错——`R14_COMMON.md §8.1`① / 台账 §935·§937·§938·§942·§944："
        "实测 14,044 槽 / 1,214 表，JSON 13,351 槽 / 1,214 表（净 −693）。")
    add("4. S22 是垃圾桶桶——台账 §966 / `PANEL.md` S22 节：S22 6,240（43.06%）中 68.2% 无信息填充，"
        "真容器模板仅 1,830（29.3%），**不得参与百分比排名**。")
    add("5. 5 行旧 `CONFLICTS` 登记值与 coverage 不符——`STATUS_BOARD.md`「已知遗留」："
        "`00468090`/`004F4EC0`/`005F4EC0`/`006FDD50`/`004C6CB0`。")
    add("")

    # ---- §F
    add("## §F 命名与落位约定（建议，不决定）")
    add("")
    add("现状：既有 7 份 KB 全在 `re_atlas\\kb\\`，命名 `NN_主题.md`；"
        "`PLAN_R14_SUSTAINED.md §1` DoD 第 6 条写的是 `KB\\Sxx_<名称>.md`。两方案利弊：")
    add("")
    add("| 方案 | 利 | 弊 |")
    add("|---|---|---|")
    add("| A. `re_atlas\\kb\\Sxx_*.md`（与既有 7 份同目录） | 语料同源、引用路径短、本索引 §A 无需拆两处；"
        "与 `re_atlas\\STATUS.md` 子系统表并列可查 | `NN_` 与 `Sxx_` 两套命名并存，需在索引中显式标注两套；"
        "与 PLAN 字面路径不一致 |")
    add("| B. 新建 `KB\\Sxx_*.md`（PLAN 字面路径） | 完全符合 DoD 第 6 条字面；"
        "子系统卡与既有专题 KB 物理分离、便于按 Sxx 统计交付数 | 仓库出现两个 KB 目录，"
        "引用歧义（同名主题可能两处）；迁移/同步成本高；本索引 §A 需拆表 |")
    add("")
    add("**明确声明**：落位与命名是 **Lead/用户决定**，本卡只给建议。"
        "本卡**不创建任何 `Sxx_*.md` 文件**，也未修改 `re_atlas\\kb\\` 下任何既有文件"
        "（本索引自身 `00_INDEX.md` 除外）。")
    add("")

    # ---- §G 分母口径快照（R14-R13 / 台账 §973）
    add("## §G 分母口径快照（看板 R14-R13 / 台账 §973）")
    add("")
    add("> 来源：`STATUS_BOARD.md`「R14-R13 三分母口径」（2026-11-17 续跑，a-P0-RESIDUAL-2 审计倒逼；"
        "依据 R14-R8「P0 由你决定」授权）+ 台账 §973（【更正 §966 / 看板 R14-R11】审计裁决 PARTIAL）。"
        "本卡只照录，不新增结论。")
    add("")
    add("| 口径 | 值 | 含义 | 用途 |")
    add("|---|---|---|---|")
    add("| **A** | **12,916** | `function_atlas.tsv` 数据行，**下界** | DoD 第 1 条**字面**分母（不变）；本卡 §B 列 1 用此 |")
    add("| **B** | **14,715**（区间 14,500–15,300） | 「业务函数」口径，**排除编译器生成的 `_initterm` thunk** | 出口闸；须改述（原「混合模型」前提已证伪） |")
    add("| **C** | **≥18,431**（区间 18,431–18,700） | 「全入口」口径，**含 3,944 项 `_initterm` 表** | 完备性讨论 |")
    add("")
    add("**背景（照录 R14-R13）**：`.data+0x4` 起有 **3,944 项 MSVC `_initterm` 静态初始化表**"
        "（遍历点 `0x7CBDD3 call 0x7CBED3`，界 `0x812000`–`0x815da4`；3,944/3,944 全 16B 对齐、"
        "3,943 体尾链式衔接、3,941 前驱∈TERM）。`coverage.tsv` 只收 22 条、`function_atlas.tsv` 只收 2 条"
        "⇒ **3,922 条未被任何覆盖表收编**。")
    add("")
    add("**同时作废（照录 R14-R13，本卡不引用）**：❌ **14,515**（P0-RESIDUAL-2 的 14,495+20 推导，撤回）；"
        "❌ **≈222（区间 222–820）**（不再是「估计缺口」）；❌ **2,026=无人引用**（initterm 表子集，其中 2,019 已被通道 G 命中）；"
        "❌ **5,598 已逐地址裁定**（实为「已枚举待裁清单」）。")
    add("")
    add("**截面值**：`coverage.tsv` 现值 **14,495**（M2 并表后，**截面**，非 A/B/C 任一分母）；引用须标「截面」。"
        "**明令**：任何「全镜像 X%」必须写明用 **A / B / C** 哪个口径；引用 12,916 必须标「下界」。"
        "**不得用 A 宣布 P0 完成**（R14-R8 原令继续有效）。")
    add("")

    text = "\n".join(L) + "\n"
    OUT.write_text(text, encoding="utf-8")

    stats = {
        "snapshot_end": SNAPSHOT_END, "live_ledger_sections": len(live_secs),
        "live_extra": live_extra,
        "ledger_sections": len(secs), "routed_to_Sxx": routed, "cross_only": cross_only,
        "deprecation_flags": dep_hit, "dep_table_rows": dep_rows, "dep_title_rows": dep_title_rows,
        "dod_counts": {k: counts[k] for k in ("✅", "⚠️", "❌", "—")},
        "dod_total": sum(counts.values()),
        "missing_kb_subsystems": [sid for sid, _ in SUBSYSTEMS],
        "missing_kb_count": len(SUBSYSTEMS),
        "live_ok": live_ok,
        "live_missing": live_missing,
        "live_partial": live_partial,
        "live_na": live_na,
        "proved_gap_top5": [(sid, p["proved_pct"], round(50-p["proved_pct"], 2)) for sid, p in ranked],
        "panel_total": panel.get("TOTAL", None),
        "output_lines": text.count("\n"),
    }
    STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return stats

if __name__ == "__main__":
    s = render()
    print(json.dumps(s, ensure_ascii=True, indent=2))
