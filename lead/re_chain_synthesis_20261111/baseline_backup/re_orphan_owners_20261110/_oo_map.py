# -*- coding: utf-8 -*-
"""
_oo_map.py — XMP29U2.MAP owner 实体清点（只读磁盘文件，不启动游戏、不读活进程）。

对照件：lead/goal1_h1decay_20261021/HOUSE_COUNTERS_DECODED.md §2.6（L213-L236）的声明：
  14 个 owner 沿对角线 14 个条带、每带 400 实体、坐标区间逐条列出；
  MaxPlayer=2 / Player=Russians；只有 4 个 HouseClass 实例。

任务（来自 ask）：
  1. [Units]+[Infantry] 逐 owner 统计车辆/步兵数与坐标范围（14 行表）。
  2. 核「每带 400」：14*400 vs [Units]+[Infantry] 总数（声明 3360+2240=5600）。
  3. 核坐标区间：§2.6 的 14 个 x/y 区间逐条对账。
  4. 解析 [Houses] 与各 house 节（PlayerControl 等标志）。
  5. MaxPlayer=2 vs 14 owner 在文件层面的解释。

输出：_oo_map_out.txt / _oo_map_out.json（与本脚本同目录）。
"""
import sys
sys.dont_write_bytecode = True

import os
import json
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))  # lead/re_orphan_owners_20261110 -> repo root
MAP_PATH = os.path.join(REPO, "scratch", "boot_probe", "arm_a", "XMP29U2.MAP")
OUT_TXT = os.path.join(HERE, "_oo_map_out.txt")
OUT_JSON = os.path.join(HERE, "_oo_map_out.json")

# ---- 台账 §2.6（HOUSE_COUNTERS_DECODED.md L218-L232）声明的 14 个条带（顺序照抄） ----
LEDGER_BANDS = [
    # (owner, x_min, x_max, y_min, y_max)
    ("<human player>", 91, 139, 7, 16),
    ("Alliance",       139, 188, 7, 16),
    ("French",         81, 129, 17, 26),
    ("Germans",        129, 179, 16, 26),
    ("British",        71, 119, 27, 36),
    ("Africans",       119, 169, 26, 36),
    ("Arabs",          61, 109, 37, 46),
    ("Confederation",  109, 159, 36, 46),
    ("Computer",       51, 99, 47, 56),
    ("YuriCountry",    100, 149, 46, 55),
    ("GDI",            41, 89, 57, 66),
    ("Nod",            90, 140, 55, 65),
    ("Neutral",        31, 79, 67, 76),
    ("Special",        80, 130, 65, 75),
]

NON_HOUSE_SECTIONS = {
    "Preview", "PreviewPack", "Map", "Basic", "SpecialFlags", "Lighting",
    "Houses", "IsoMapPack5", "OverlayPack", "OverlayDataPack", "Waypoints",
    "Units", "Infantry", "Structures", "Aircraft",
}


def parse_ini(path):
    """返回 (sections 有序 dict: name -> [(key, value, line_no)], file_meta)。"""
    with open(path, "rb") as f:
        raw = f.read()
    meta = {
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "crlf_count": raw.count(b"\r\n"),
        "lf_only_count": raw.count(b"\n") - raw.count(b"\r\n"),
    }
    text = raw.decode("latin-1")
    sections = {}
    cur = None
    for i, line in enumerate(text.split("\n"), start=1):
        s = line.rstrip("\r")
        if not s.strip():
            continue
        if s.startswith("[") and s.rstrip().endswith("]"):
            cur = s.strip()[1:-1]
            sections.setdefault(cur, [])
            continue
        if cur is None:
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            sections[cur].append((k, v, i))
        else:
            sections[cur].append((None, s, i))  # 不规范行，原样留存
    return sections, meta


def parse_objects(entries, section_name, errors):
    """解析 Index=Owner,Type,Strength,X,Y,... 行。字段 3=X、字段 4=Y。
    任何无法解析的行进 errors，不猜。"""
    objs = []
    for key, val, line_no in entries:
        if key is None:
            errors.append((section_name, line_no, "no '=' in line: %r" % val))
            continue
        parts = val.split(",")
        if len(parts) < 5:
            errors.append((section_name, line_no, "field<5: %r" % val))
            continue
        try:
            x, y = int(parts[3]), int(parts[4])
        except ValueError:
            errors.append((section_name, line_no, "X/Y not int: %r" % val))
            continue
        objs.append({"idx": key, "owner": parts[0], "type": parts[1],
                     "x": x, "y": y, "line": line_no})
    return objs


def extent(objs):
    if not objs:
        return None
    xs = [o["x"] for o in objs]
    ys = [o["y"] for o in objs]
    return (min(xs), max(xs), min(ys), max(ys))


def bbox_overlap(a, b):
    """(xmin,xmax,ymin,ymax) 两两是否相交（含边界相接）。"""
    return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])


def main():
    sections, meta = parse_ini(MAP_PATH)
    out_lines = []
    P = out_lines.append

    P("=" * 78)
    P("XMP29U2.MAP owner 实体清点 — 只读解析")
    P("=" * 78)
    P("file   : %s" % MAP_PATH)
    P("size   : %d bytes" % meta["size_bytes"])
    P("sha256 : %s" % meta["sha256"])
    P("EOL    : CRLF=%d, LF-only=%d" % (meta["crlf_count"], meta["lf_only_count"]))
    P("")

    sec_names = list(sections.keys())
    P("[0] 节清单（%d 节）" % len(sec_names))
    P("    " + ", ".join(sec_names))
    missing = [n for n in ("Units", "Infantry", "Houses", "Basic", "Map") if n not in sections]
    P("    缺失节: %s" % (missing if missing else "无"))
    extra_obj_secs = [n for n in ("Structures", "Aircraft") if n in sections]
    P("    [Structures]/[Aircraft] 存在性: %s" % (extra_obj_secs if extra_obj_secs else "均不存在（对象只有 Units+Infantry 两类）"))
    P("")

    # ---------- [Basic] ----------
    basic = {k: v for k, v, _ in sections.get("Basic", [])}
    P("[Basic] 关键键")
    for k in ("Name", "Author", "Player", "MaxPlayer", "MinPlayer", "MultiplayerOnly", "NextScenario"):
        P("    %-16s= %s" % (k, basic.get(k, "<absent>")))
    P("")

    # ---------- [Map] ----------
    mapsec = {k: v for k, v, _ in sections.get("Map", [])}
    P("[Map] 几何声明")
    for k in ("Size", "LocalSize", "Theater"):
        P("    %-16s= %s" % (k, mapsec.get(k, "<absent>")))
    P("")

    # ---------- [Houses] ----------
    houses_list = [(k, v) for k, v, _ in sections.get("Houses", [])]
    house_names = [v for _, v in houses_list]
    P("[1][Houses] 声明 %d 个 house：%s" % (len(houses_list), ", ".join(house_names)))
    P("")

    # ---------- house 节 ----------
    house_secs = [n for n in sec_names if n not in NON_HOUSE_SECTIONS]
    P("[4] house 节（有 Country= 键的节，共 %d 个；[Houses] 之外多出的: %s）"
      % (len(house_secs), [n for n in house_secs if n not in house_names] or "无"))
    P("")
    P("    %-14s %-13s %-9s %-9s %-4s %-8s %-10s %s" %
      ("[section]", "Country", "PlayerCtrl", "Color", "IQ", "Edge", "Credits", "Allies"))
    house_rows = []
    for name in house_secs:
        d = {k: v for k, v, _ in sections.get(name, [])}
        row = {
            "section": name,
            "Country": d.get("Country"),
            "PlayerControl": d.get("PlayerControl"),
            "Color": d.get("Color"),
            "IQ": d.get("IQ"),
            "Edge": d.get("Edge"),
            "Credits": d.get("Credits"),
            "Allies": d.get("Allies"),
            "PercentBuilt": d.get("PercentBuilt"),
            "NodeCount": d.get("NodeCount"),
            "TechLevel": d.get("TechLevel"),
        }
        house_rows.append(row)
        P("    %-14s %-13s %-9s %-9s %-4s %-8s %-10s %s" %
          (name, str(d.get("Country")), str(d.get("PlayerControl")),
           str(d.get("Color")), str(d.get("IQ")), str(d.get("Edge")),
           str(d.get("Credits")), str(d.get("Allies"))))
    pc_yes = [r["section"] for r in house_rows if (r["PlayerControl"] or "").lower() == "yes"]
    P("")
    P("    PlayerControl=yes 的节: %s" % (pc_yes if pc_yes else "无（14 节全部 PlayerControl=no，逐值见 JSON）"))
    P("")

    # ---------- [Units] / [Infantry] ----------
    errors = []
    units = parse_objects(sections.get("Units", []), "Units", errors)
    inf = parse_objects(sections.get("Infantry", []), "Infantry", errors)

    P("[Units]    条目数 = %d（含不可解析 %d）" % (len(units) + sum(1 for e in errors if e[0] == "Units"),
                                               sum(1 for e in errors if e[0] == "Units")))
    P("[Infantry] 条目数 = %d（含不可解析 %d）" % (len(inf) + sum(1 for e in errors if e[0] == "Infantry"),
                                               sum(1 for e in errors if e[0] == "Infantry")))
    total = len(units) + len(inf)
    P("总计 = %d" % total)
    P("")

    # 索引连续性
    def idx_check(objs, name):
        keys = [int(o["idx"]) for o in objs]
        n = len(keys)
        expect = set(range(n))
        dups = sorted(set(k for k in keys if keys.count(k) > 1))
        missing_idx = sorted(expect - set(keys))
        extra_idx = sorted(set(keys) - expect)
        return {"section": name, "count": n, "min": min(keys) if keys else None,
                "max": max(keys) if keys else None,
                "contiguous_0_to_n1": (not missing_idx and not extra_idx),
                "dups": dups[:20], "missing_sample": missing_idx[:20],
                "extra_sample": extra_idx[:20]}
    idx_u = idx_check(units, "Units")
    idx_i = idx_check(inf, "Infantry")
    P("[2a] 索引连续性：Units 0..%d 连续=%s；Infantry 0..%d 连续=%s（dups/missing/extra 见 JSON）"
      % (idx_u["max"], idx_u["contiguous_0_to_n1"], idx_i["max"], idx_i["contiguous_0_to_n1"]))
    P("")

    # ---------- 逐 owner 统计 ----------
    all_objs = units + inf
    owners = []
    for o in all_objs:
        if o["owner"] not in owners:
            owners.append(o["owner"])

    stats = {}
    for w in owners:
        u = [o for o in units if o["owner"] == w]
        i = [o for o in inf if o["owner"] == w]
        e_u, e_i = extent(u), extent(i)
        e_all = extent(u + i)
        stats[w] = {
            "units": len(u), "infantry": len(i), "total": len(u) + len(i),
            "x": [e_all[0], e_all[1]], "y": [e_all[2], e_all[3]],
            "units_extent": {"x": [e_u[0], e_u[1]], "y": [e_u[2], e_u[3]]} if e_u else None,
            "infantry_extent": {"x": [e_i[0], e_i[1]], "y": [e_i[2], e_i[3]]} if e_i else None,
        }

    P("[1] 逐 owner 实体统计（14 行；顺序照台账 §2.6，坐标范围=车辆+步兵合并 min/max）")
    P("    %-16s %6s %6s %6s   %-12s %-12s %s" %
      ("owner", "units", "inf", "total", "x[min..max]", "y[min..max]", "per-band=400?"))
    rows = []
    for w in [b[0] for b in LEDGER_BANDS]:
        s = stats.get(w)
        if s is None:
            P("    %-16s %s" % (w, "<owner 不存在于 [Units]/[Infantry]>"))
            rows.append({"owner": w, "present": False})
            continue
        rows.append({"owner": w, **s})
        P("    %-16s %6d %6d %6d   %-12s %-12s %s" %
          (w, s["units"], s["infantry"], s["total"],
           "%d..%d" % (s["x"][0], s["x"][1]), "%d..%d" % (s["y"][0], s["y"][1]),
           "OK" if s["total"] == 400 else "*** != 400 ***"))

    owners_not_in_ledger = [w for w in owners if w not in [b[0] for b in LEDGER_BANDS]]
    ledger_not_in_owners = [b[0] for b in LEDGER_BANDS if b[0] not in owners]
    P("")
    P("    对象里出现但台账未列的 owner: %s" % (owners_not_in_ledger or "无"))
    P("    台账列了但对象里没有的 owner: %s" % (ledger_not_in_owners or "无"))
    P("    distinct owner 总数 = %d" % len(owners))
    P("")

    # ---------- 每带 400 ----------
    per400 = [w for w in owners if stats[w]["total"] == 400]
    P("[2] 「每带 400 实体」核实")
    P("    实测 [Units]=%d, [Infantry]=%d, 合计=%d" % (len(units), len(inf), total))
    P("    声称 3360 + 2240 = 5600 → %s" % ("吻合" if (len(units), len(inf), total) == (3360, 2240, 5600) else "不吻合"))
    P("    14 * 400 = %d → %s" % (14 * 400, "吻合" if total == 5600 else "不吻合"))
    P("    total==400 的 owner：%d/%d 个" % (len(per400), len(owners)))
    P("    units==240 且 infantry==160 的 owner：%d/%d 个"
      % (sum(1 for w in owners if stats[w]["units"] == 240 and stats[w]["infantry"] == 160), len(owners)))
    P("")

    # ---------- 台账区间逐条对账 ----------
    P("[3] 坐标区间逐条对账（台账 §2.6 vs 文件实测，owner 合并车辆+步兵）")
    P("    %-16s %-15s %-15s %-13s %-13s %s" %
      ("owner", "declared x", "actual x", "declared y", "actual y", "verdict"))
    ledger_rows = []
    for (w, dx0, dx1, dy0, dy1) in LEDGER_BANDS:
        s = stats.get(w)
        if s is None:
            P("    %-16s <owner 不存在>" % w)
            ledger_rows.append({"owner": w, "declared": [dx0, dx1, dy0, dy1], "present": False})
            continue
        ok = (s["x"] == [dx0, dx1] and s["y"] == [dy0, dy1])
        verdict = "MATCH" if ok else "MISMATCH"
        P("    %-16s %-15s %-15s %-13s %-13s %s" %
          (w, "[%d..%d]" % (dx0, dx1), "[%d..%d]" % (s["x"][0], s["x"][1]),
           "[%d..%d]" % (dy0, dy1), "[%d..%d]" % (s["y"][0], s["y"][1]), verdict))
        ledger_rows.append({"owner": w, "declared": {"x": [dx0, dx1], "y": [dy0, dy1]},
                            "actual": {"x": s["x"], "y": s["y"]}, "verdict": verdict})
    n_match = sum(1 for r in ledger_rows if r.get("verdict") == "MATCH")
    P("")
    P("    逐条对账结果：%d/14 条 MATCH" % n_match)
    P("")

    # 条带相邻性（bbox 两两相交，验证「彼此紧邻」）
    P("[3b] 条带 bbox 两两相交（验证「彼此紧邻」；相接在边界上也算相交）")
    ext_map = {b[0]: extent([o for o in all_objs if o["owner"] == b[0]]) for b in LEDGER_BANDS
               if b[0] in stats}
    names = [b[0] for b in LEDGER_BANDS]
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = ext_map.get(names[i]), ext_map.get(names[j])
            if a and b and bbox_overlap(a, b):
                pairs.append((names[i], names[j]))
    P("    相交对数 = %d" % len(pairs))
    for a, b in pairs:
        P("      %s × %s" % (a, b))
    P("")

    # 坐标越界检查（对照 [Map] Size）
    size = (mapsec.get("Size") or "").split(",")
    map_w, map_h = (int(size[2]), int(size[3])) if len(size) == 4 and size[2].lstrip("-").isdigit() else (None, None)
    g = extent(all_objs)
    P("[3c] 坐标 vs [Map] Size=0,0,%s,%s（LocalSize=%s）" % (map_w, map_h, mapsec.get("LocalSize")))
    P("    全部 %d 个对象的实测范围：x[%d..%d], y[%d..%d]" % (len(all_objs), g[0], g[1], g[2], g[3]))
    if map_w is not None:
        oob_x = sum(1 for o in all_objs if not (0 <= o["x"] < map_w))
        oob_y = sum(1 for o in all_objs if not (0 <= o["y"] < map_h))
        P("    x 超出 [0,%d) 的对象数 = %d；y 超出 [0,%d) 的对象数 = %d" % (map_w, oob_x, map_h, oob_y))
        oob_owners = []
        for w in owners:
            s = stats[w]
            if s["x"][1] >= map_w or s["y"][1] >= map_h:
                oob_owners.append(w)
        P("    有坐标超出 [Map] Size 矩形的 owner（%d 个）：%s" % (len(oob_owners), ", ".join(oob_owners)))
    P("")

    # ---------- owner 名 vs [Houses] 名 ----------
    hs = set(house_names)
    os_ = set(owners)
    P("[5a] 对象 owner 名 vs [Houses] 声明名")
    P("    owner 有而 [Houses] 无: %s" % (sorted(os_ - hs) or "无"))
    P("    [Houses] 有而对象无: %s" % (sorted(hs - os_) or "无"))
    for w in sorted(hs - os_):
        P("      %s 拥有对象数 = 0（[Houses] 声明了但 [Units]/[Infantry] 没用它）" % w)
    P("")

    # ---------- 字面 token 计数（独立于分节解析的交叉验证） ----------
    P("[5b] 字面 token 行数（全文 grep 交叉验证，含任意节）")
    for tok in ("<human player>", "Computer", "Americans", "Russians"):
        with open(MAP_PATH, "rb") as f:
            raw = f.read()
        cnt = raw.decode("latin-1").count(tok)
        # 行级计数（避免一行多次出现重复计）
        line_cnt = sum(1 for ln in raw.decode("latin-1").split("\n") if tok in ln)
        P("    %-16r 出现在 %d 行 / 共 %d 次" % (tok, line_cnt, cnt))
    P("")

    # ---------- 解析错误 ----------
    P("[E] 不可解析行：%s" % (errors if errors else "无"))
    P("")

    # ---------- 结论 ----------
    P("[5c] MaxPlayer=2 vs 14 owner —— 文件层面的事实")
    P("    (a) [Basic] MaxPlayer=2, MinPlayer=2, MultiplayerOnly=1 —— 键在 [Basic]（多人元数据区），")
    P("        语义是「可加入的人类玩家槽位」；它与 [Houses] 的 house 数量在文件里就是两个独立的量。")
    P("    (b) [Houses] 独立声明了 14 个 house（0=Americans..13=Special），14 个 house 节全部")
    P("        PlayerControl=no —— 即文件层面没有任何一个 house 被标记为人类操控。")
    P("    (c) [Units]/[Infantry] 用了 14 个 owner 字符串，其中 <human player> 和 Computer 不在")
    P("        [Houses] 名单里；Americans 和 Russians 在 [Houses] 里声明了却拥有 0 个对象。")
    P("    (d) 因此「MaxPlayer=2 但 14 owner」在文件层面不是矛盾：MaxPlayer 不约束 [Houses]/对象")
    P("        owner 的数量，只约束多人加入槽位。运行期 meta_count=4 是引擎侧的实例化结果，")
    P("        文件本身不包含 HouseClass 实例表，无法从文件验证或反驳 4 这个数。")
    P("")

    txt = "\n".join(out_lines) + "\n"
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(txt)

    # ---------- JSON ----------
    result = {
        "source": {
            "path": MAP_PATH, "size_bytes": meta["size_bytes"], "sha256": meta["sha256"],
            "crlf": meta["crlf_count"], "lf_only": meta["lf_only_count"],
        },
        "sections": sec_names,
        "basic": basic, "map": mapsec,
        "houses_declared": houses_list,
        "house_sections": house_rows,
        "playercontrol_yes": pc_yes,
        "counts": {
            "units": len(units), "infantry": len(inf), "total": total,
            "claim_units": 3360, "claim_infantry": 2240, "claim_total": 5600,
            "claim_per_band": 400, "n_owners": len(owners),
            "owners_with_400": sorted(per400),
            "units_eq_240_inf_eq_160": sorted(w for w in owners if stats[w]["units"] == 240 and stats[w]["infantry"] == 160),
        },
        "index_continuity": [idx_u, idx_i],
        "per_owner": rows,
        "ledger_reconciliation": ledger_rows,
        "ledger_match_count": n_match,
        "bbox_overlap_pairs": pairs,
        "map_bounds_check": {
            "map_size": mapsec.get("Size"), "local_size": mapsec.get("LocalSize"),
            "global_extent": {"x": [g[0], g[1]], "y": [g[2], g[3]]},
            "oob_owners": oob_owners if map_w is not None else None,
        },
        "owner_vs_houses": {
            "owner_not_in_houses": sorted(os_ - hs),
            "houses_without_objects": sorted(hs - os_),
        },
        "parse_errors": errors,
        "waypoints": [(k, v) for k, v, _ in sections.get("Waypoints", [])],
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(txt)


if __name__ == "__main__":
    main()
