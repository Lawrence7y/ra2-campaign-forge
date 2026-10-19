#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_map_gen.py — ZC-GAP-P21 A3 行为验收专用场景图生成（GAPP21）

目的：构造一个最小可判的「敌方裂缝 + RevealArea2 开图」场景：
  - FogOfWar=yes（黑幕/裂缝机制的前提；bench 基准图默认 no，本图必须显式开）
  - 玩家 Americans 基地（ConYard/Power/WarFactory + 步兵）位于敌方裂缝半径内
  - 敌方 Germans（与玩家交战）预置两个裂缝候选：
      GAGAP     —— 官方 YR 合金（Allied）裂缝产生器（主候选，可见建筑 gaspOT 图）
      CAFARM02  —— 隐形农场（隐藏 gap 农场，mod 战役用法；备选）
  - 一条触发器（ElapsedTime=15s）一次性释放 25 个 RevealAroundWaypoint（TA 17，
    反汇编实证 0x6E0FE0 内含双 call 0x5678E0 = MapClass::RevealArea2 ⇒ 命中 P-2.1 补丁点），
    5×5 网格 waypoint 间距 4 格 ⇒ 覆盖基地周围约 ±8 格（即使单点半径只有 4 格也全覆盖）。

补丁判据（不依赖半径精确值）：
  开图前 读 CellClass+0x134（GapsCoveringThisCell）⇒ 若干格 >0（裂缝在）
  开图后 未打补丁：被开图格 +0x134 归 0（废缝）；已打补丁：仍 >0（缝仍在）

产物：
  out/re_work/zcode_live/gap_p21/map/[2]0GAPP21.yrm   （工作副本 + ini 文本）
  out/re_work/zcode_live/gap_p21/map/gapp21.ini       （同内容明文，供静态核查）
安装：--install 复制到 ra2bench/[2]0GAPP21.yrm；--uninstall 删除（MANIFEST 不管辖本图）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ra2forge.maplib import MissionMap, STANDARD_HOUSES, STANDARD_HOUSE_COLORS  # noqa: E402
from ra2forge import triggers as tg  # noqa: E402

OUT = ROOT / "out" / "re_work" / "zcode_live" / "gap_p21" / "map"
GAME = ROOT / "ra2bench"
MAP_NAME = "[2]0GAPP21.yrm"

SIZE = 100
PLAYER = "Americans"
GAP_OWNER = "Germans"
BASE = (50, 40)          # 玩家基地中心 (row, col)
ENEMY_BASE = (70, 70)    # 敌方老家（防止敌方瞬间战败）
TRIGGER_AT_S = 90    # 注入测试：开局后 90s 开图（A3-injected）
WP_BASE = 50             # waypoint id 起点
GAP_RING_R = 9           # 裂缝候选环绕半径（间距 ≈4 格，避免建筑重叠）
GAP_TYPES = ("GAGAP", "CAFARM02")   # 主候选（官方合金裂缝产生器）+ 备选（隐形 gap 农场）


def build_map() -> MissionMap:
    m = MissionMap("GAPP21 GAP TEST", width=SIZE, height=SIZE, theater="TEMPERATE")
    m.basic.update({
        "GameMode": "standard",
        "MaxPlayer": "2",
        "MinPlayer": "2",
        "MultiplayerOnly": "1",
        "FreeRadar": "yes",
    })
    m.player_house = PLAYER

    # 房屋配置：玩家 + 裂缝宿主交战，其余按默认（互相敌对，与判据无关）
    m.house_configs = []
    for idx, h in enumerate(STANDARD_HOUSES):
        m.house_configs.append({
            "name": h,
            "player": h == PLAYER,
            "techlevel": 10,
            "credits": 10000,
            "iq": 5,
            "edge": "West" if idx % 2 == 0 else "East",
            "color": STANDARD_HOUSE_COLORS.get(h, "Grey"),
            "allies": h,          # 只与自身结盟 ⇒ 其余全部交战（含裂缝宿主）
        })

    # 玩家基地（全部位于敌方裂缝半径内）
    r0, c0 = BASE
    m.add_structure(PLAYER, "GACNST", r0, c0)            # 建造厂
    m.add_structure(PLAYER, "GAPOWR", r0 - 4, c0)        # 发电厂
    m.add_structure(PLAYER, "GAWEAP", r0 + 4, c0)        # 战车工厂
    for i in range(6):
        m.add_infantry(PLAYER, "E1", r0 - 3 + i, c0 + 4 + (i % 3))

    # 敌方/各家：裂缝候选环绕基地（每家在环上占一点，装 GAGAP + CAFARM02 两个候选）
    #   ★理由：遭遇战 UI 的国家下拉决定实际参战方，本图不预设谁是 AI ⇒ 每家在环上
    #     都有裂缝候选，凡参战且与玩家交战的房屋必有其裂缝覆盖玩家基地。
    #   ★自家裂缝被引擎跳过（CreateGap 只对敌对房屋盖印）⇒ 玩家自己的候选天然惰性。
    import math
    for i, h in enumerate(STANDARD_HOUSES):
        ang = 2 * math.pi * i / len(STANDARD_HOUSES)
        r = BASE[0] + int(round(GAP_RING_R * math.sin(ang)))
        c = BASE[1] + int(round(GAP_RING_R * math.cos(ang)))
        if h == PLAYER or (r, c) == BASE:
            continue
        for t in GAP_TYPES:
            m.add_structure(h, t, r, c)
    # 参照系：Germans 自带老家（无论是否参战都留一个完整基地）
    m.add_structure(GAP_OWNER, "GAPOWR", ENEMY_BASE[0], ENEMY_BASE[1])
    m.add_structure(GAP_OWNER, "GACNST", ENEMY_BASE[0] + 3, ENEMY_BASE[1] + 3)

    # 5×5 waypoint 网格（间距 4 格，覆盖 ±8 格）+ 中心 waypoint
    wp_ids = []
    wid = WP_BASE
    # ★起点 waypoint 0/1（RA2 起始位；缺了会被当成无起始位配置，槽位数异常甚至加载崩溃）
    m.add_waypoint(0, *BASE)
    m.add_waypoint(1, *ENEMY_BASE)
    for dr in (-8, -4, 0, 4, 8):
        for dc in (-8, -4, 0, 4, 8):
            m.add_waypoint(wid, BASE[0] + dr, BASE[1] + dc)
            wp_ids.append(wid)
            wid += 1

    # 触发器：TRIGGER_AT_S 时一次性释放全部 25 个 RevealAroundWaypoint（TA17 → RevealArea2）
    #   ★TA17 的 waypoint 走 P7 字母字段（A=0..Z=25，26+ 两字母：W=26+26*f+s，A=0）。
    #     实测战役图：50↔AY、52↔BA、121↔DR、469↔RB 全合。maplib 的 act_reveal_waypoint
    #     恒写 P7='A'（=waypoint 0）⇒ 只会在 waypoint 0 放一个小圈，必须改写字条。
    def wp_letter(w: int) -> str:
        if w < 26:
            return chr(ord("A") + w)
        r = w - 26
        return chr(ord("A") + r // 26) + chr(ord("A") + r % 26)

    actions = [(17, (0, w, 0, 0, 0, 0, wp_letter(w))) for w in wp_ids]
    m.add_trigger(tg.make_trigger(
        tid="0000B021", tag_id="0000B022", house=PLAYER,
        name="GAPP21 reveal", events=[tg.ev_elapsed_time(TRIGGER_AT_S)],
        actions=actions, tag_name="GAPP21Reveal", repeating=1))
    # ★[CellTags]：把 tag 绑到「必然存在的格」上（战役图同法）——否则 TagClass 不实例化，
    #   ElapsedTime 事件永不求值（实测：无 CellTags 时触发器完全不触发，mapped 无增长）。
    #   键编码 = y*1000+x（同 [Waypoints]；战役图 CellTags 30105..30108 印证）。
    # [CellTags] 键 = y*1000+x（与 [Waypoints] 同编码；实测战役图 30105..30108 为同一行 4 格）
    m.cell_tags = [(51 + dr) * 1000 + (90 + dc)
                   for dr in (-8, -4, 0, 4, 8) for dc in (-8, -4, 0, 4, 8)]
    return m


def patch_basic_ignore_aitriggers(text: str) -> str:
    """IgnoreGlobalAITriggers=yes -> no（maplib 硬编码 yes；bench 图为 no）。
    疑似该键会连普通触发器一起静默（实测 TA11 文本消息在 yes 下完全不触发）。"""
    out = []
    in_basic = False
    done = False
    for ln in text.splitlines():
        if ln.startswith("[") and ln.endswith("]"):
            in_basic = ln.strip() == "[Basic]"
        elif in_basic and ln.startswith("IgnoreGlobalAITriggers="):
            out.append("IgnoreGlobalAITriggers=no")
            done = True
            continue
        out.append(ln)
    if not done:
        raise SystemExit("[FAIL] 未找到 IgnoreGlobalAITriggers= 行")
    return "\n".join(out) + "\n"


def patch_fog_of_war(text: str) -> str:
    """[SpecialFlags] FogOfWar=no → yes（maplib 硬编码 no，本图必须开黑幕）。"""
    lines = text.splitlines()
    out, in_sf, done = [], False, False
    for ln in lines:
        if ln.startswith("[") and ln.endswith("]"):
            in_sf = ln.strip() == "[SpecialFlags]"
        elif in_sf and ln.startswith("FogOfWar="):
            out.append("FogOfWar=yes")
            done = True
            continue
        out.append(ln)
    if not done:
        raise SystemExit("[FAIL] 未找到 FogOfWar= 行（[SpecialFlags] 段缺失？）")
    return "\n".join(out) + "\n"


def patch_multiplayer_basic(text: str) -> str:
    """强制多人/遭遇战字段（maplib 的 to_ini_text 忽略 m.basic 的这些键，恒写
    MultiplayerOnly=0/FreeRadar=no ⇒ 图会被当成战役任务图而非遭遇战图）。
    口径照抄 tools/empty_map_gen.py::patch_multiplayer_basic。"""
    lines = text.splitlines()
    out: list[str] = []
    in_basic = False
    seen: set[str] = set()
    extras = {
        "GameMode": "standard",
        "MaxPlayer": "2",
        "MinPlayer": "2",
        "MultiplayerOnly": "1",
        "FreeRadar": "yes",
        "HomeCell": "0",
        "AltHomeCell": "0",
    }
    for line in lines:
        if line.startswith("["):
            if in_basic:
                for k, v in extras.items():
                    if k not in seen:
                        out.append(f"{k}={v}")
                in_basic = False
            if line.strip() == "[Basic]":
                in_basic = True
                seen.clear()
        elif in_basic and "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in extras:
                seen.add(k)
                out.append(f"{k}={extras[k]}")
                continue
        out.append(line)
    if in_basic:
        for k, v in extras.items():
            if k not in seen:
                out.append(f"{k}={v}")
    return "\n".join(out) + "\n"


def add_header(text: str, player_cell: tuple[int, int], enemy_cell: tuple[int, int]) -> str:
    """补 [Header] 段（官方/bench 图均有；缺它时游戏地图浏览器读不到 Name/MP 设置，
    退化成 "No Name" + 8 槽位，导致选图与开局异常）。坐标 = 文件格（平行四边形）坐标。
    ★行文口径与官方图一致：CRLF、[Header] 与 [Preview] 之间无空行（实测 LF/空行会让
      浏览器把 Name 显示成 "No Name"）。"""
    header = (
        "[Header]\r\n"
        f"Width={SIZE}\r\n"
        f"Height={SIZE}\r\n"
        f"StartX={player_cell[0]}\r\n"
        f"StartY={player_cell[1]}\r\n"
        f"Waypoint1={player_cell[0]},{player_cell[1]}\r\n"
        f"Waypoint2={enemy_cell[0]},{enemy_cell[1]}\r\n"
        + "".join(f"Waypoint{i}=0,0\r\n" for i in range(3, 9))
        + "NumberStartingPoints=2\r\n"
    )
    if text.startswith("[Header]"):
        return text
    return header + text


def split_sections(text: str) -> "list[tuple[str, list[str]]]":
    """切分为 [(section_name, lines)] 保序列表。"""
    secs: list[tuple[str, list[str]]] = []
    cur = None
    for ln in text.splitlines():
        if ln.startswith("[") and ln.endswith("]") and len(ln) > 2:
            cur = (ln.strip()[1:-1], [])
            secs.append(cur)
        elif cur is not None:
            cur[1].append(ln)
    return secs


def graft_onto_skeleton(mine_text: str, skeleton_text: str,
                        player_cell: tuple[int, int], enemy_cell: tuple[int, int]) -> str:
    """把本人场景的 [Basic]/[Waypoints]/[Structures]/[Infantry]/[Triggers]/[Tags]/[Events]/[Actions]
    移植到一份已知可在浏览器正确显示/加载的骨架图上（保留其 [Header]/[Preview]/[PreviewPack]/
    [Map]/[Houses]+房屋段/[IsoMapPack5]/[OverlayPack]/[OverlayDataPack]/[Digest]/[Lighting]）。
    原因：maplib 从零生成的图在本构建的浏览器里 Name 显示为 "No Name"（疑因缺 [Digest]/
    或 [Header] 细节），而 bench 基准图可正常显示与加载 ⇒ 用骨架保底。
    [SpecialFlags] 取骨架但强制 FogOfWar=yes（黑幕/裂缝机制前提）。"""
    MINE_KEEP = {"Basic", "Waypoints", "Structures", "Infantry",
                 "Triggers", "Tags", "Events", "Actions", "CellTags"}
    mine = {name: lines for name, lines in split_sections(mine_text)}
    out: list[str] = []
    inserted = False
    for name, lines in split_sections(skeleton_text):
        if name in MINE_KEEP:
            if not inserted:
                # 在骨架原 [Waypoints] 位置一次性插入我的全部场景段（保序）
                for k in ("Basic", "Waypoints", "Structures", "Infantry",
                          "Triggers", "Tags", "Events", "Actions", "CellTags"):
                    if k not in mine:
                        continue
                    out.append(f"[{k}]")
                    out.extend(l for l in mine[k] if l.strip() != "")
                    out.append("")
                inserted = True
            continue
        if name == "Header":
            # 起点改到本人基地/敌基地（文件格坐标）
            out.append("[Header]")
            out.append(f"Width={SIZE}")
            out.append(f"Height={SIZE}")
            out.append(f"StartX={player_cell[0]}")
            out.append(f"StartY={player_cell[1]}")
            out.append(f"Waypoint1={player_cell[0]},{player_cell[1]}")
            out.append(f"Waypoint2={enemy_cell[0]},{enemy_cell[1]}")
            out.extend(f"Waypoint{i}=0,0" for i in range(3, 9))
            out.append("NumberStartingPoints=2")
            out.append("")
            continue
        if name == "SpecialFlags":
            out.append("[SpecialFlags]")
            for l in lines:
                if l.strip().startswith("FogOfWar="):
                    out.append("FogOfWar=yes")
                elif l.strip():
                    out.append(l)
            out.append("")
            continue
        out.append(f"[{name}]")
        out.extend(l for l in lines if l.strip() != "")
        out.append("")
    if not inserted:
        raise SystemExit("[FAIL] 骨架图缺少 [Waypoints] 锚点段")
    return "\r\n".join(out) + "\r\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true", help="复制到 ra2bench/")
    ap.add_argument("--uninstall", action="store_true", help="删除 ra2bench 中的本图")
    args = ap.parse_args()

    m = build_map()
    mine = patch_fog_of_war(m.to_ini_text())
    mine = patch_multiplayer_basic(mine)
    mine = patch_basic_ignore_aitriggers(mine)
    mine = add_header(mine, m.grid.to_cell(*BASE), m.grid.to_cell(*ENEMY_BASE))
    # 插入 [CellTags]（tag → 格绑定，保证 TagClass 实例化）
    if getattr(m, "cell_tags", None):
        celltag_lines = ["[CellTags]"] + [f"{idx}=0000B022" for idx in m.cell_tags]
        i = mine.rfind("[Actions]")
        if i >= 0:
            j = mine.find("\n[", i + 1)
            if j < 0:
                j = len(mine)
            mine = mine[:j] + "\r\n\r\n" + "\r\n".join(celltag_lines) + mine[j:]
    mine = mine.replace("\r\n", "\n").replace("\n", "\r\n")
    # 骨架：取当前 U0800 备份（已知可正常显示/加载的 bench 图）
    skeleton_path = OUT / "U0800.slotbak.yrm"
    if skeleton_path.is_file():
        skel = skeleton_path.read_bytes().decode("gbk", errors="replace")
        text = graft_onto_skeleton(mine, skel,
                                   m.grid.to_cell(*BASE), m.grid.to_cell(*ENEMY_BASE))
        mode = "grafted"
    else:
        text = mine
        mode = "standalone"
    raw = text.encode("gbk", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / MAP_NAME).write_bytes(raw)
    (OUT / "gapp21.ini").write_text(text, encoding="utf-8")

    sec = {}
    cur = None
    for ln in text.splitlines():
        if ln.startswith("[") and ln.endswith("]"):
            cur = ln[1:-1]
            sec.setdefault(cur, 0)
        elif "=" in ln and cur:
            sec[cur] += 1
    report = {
        "map": MAP_NAME, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "size": [SIZE, SIZE], "fog_of_war": "yes",
        "player": PLAYER, "gap_owner": GAP_OWNER,
        "sections": sec,
        "trigger_at_s": TRIGGER_AT_S,
        "waypoints": [WP_BASE, WP_BASE + 24],
    }
    (OUT / "gen_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

    if args.install:
        dst = GAME / MAP_NAME
        shutil.copy2(OUT / MAP_NAME, dst)
        print(f"[install] {dst}  sha={hashlib.sha256(dst.read_bytes()).hexdigest()[:16]}...")
    if args.uninstall:
        dst = GAME / MAP_NAME
        if dst.is_file():
            dst.unlink()
            print(f"[uninstall] removed {dst}")
        else:
            print(f"[uninstall] not present: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
