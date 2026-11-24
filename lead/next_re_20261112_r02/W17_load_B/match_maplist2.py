#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W17 对账 v2：全 268 条列表项分类 + 全 277 文件分类 + 划分恒等式。

分类规则（由 attempt1/2 实测证据驱动）：
  - 列表项含全角（N-M）后缀且为正常 UTF-16 中文 ⇒ 内置本地化条目（游戏自带 MIX 图）。
  - 列表项 ASCII 或可按 GBK/UTF-8 逐字节零扩展恢复 ⇒ 散装文件条目（游戏把 ANSI
    文件名逐字节零扩展）。
  - 目的：判定 B（official=yes，[Basic].Name='[8] Sonic Highways'）是否可能出现在
    列表中；若内置块封闭且散装 official=yes 不被列出 ⇒ B 无列表条目 ⇒ [B 不可用]。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
GAME_DIR = ROOT / "ra2youli"
W17 = ROOT / "lead" / "next_re_20261112_r02" / "W17_load_B"
B_FILENAME = "[8]音速公路_SonicHighways.yrm"

SUFFIX_FW = re.compile(r"（\d+-\d+）$")
SUFFIX_ASC = re.compile(r"\((\d+)-(\d+)\)$")


def recover(s: str):
    """列表项字节零扩展恢复：全字符 ≤0xFF ⇒ 取低字节，分别试 GBK/UTF-8。"""
    if not s or any(ord(c) > 0xFF for c in s):
        return None, None
    b = bytes(ord(c) & 0xFF for c in s)
    g = u = None
    try:
        g = b.decode("gbk")
    except Exception:
        g = None
    try:
        u = b.decode("utf-8")
        if any(ord(c) == 0xFFFD for c in u):
            u = None
    except Exception:
        u = None
    return g, u


def parse_basic(raw: bytes):
    out = {}
    m = re.search(rb"\[Basic\]\s*\r?\n(.*?)(?=\r?\n\[|\Z)", raw, re.S)
    if not m:
        return None
    body = m.group(1) or b""
    for key in (b"Name", b"MaxPlayer", b"MinPlayer", b"MultiplayerOnly",
                b"Official", b"GameMode", b"NewINIFormat"):
        km = re.search(rb"^" + key + rb"\s*=\s*([^\r\n]*)", body, re.M)
        if km:
            v = km.group(1)
            g = None
            for enc in ("gbk", "utf-8", "latin-1"):
                try:
                    g = v.decode(enc)
                    if enc != "latin-1" and "\ufffd" in g:
                        continue
                    break
                except Exception:
                    continue
            out[key.decode()] = (g or "").strip()
    return out


def main():
    entries = json.loads((W17 / "out" / "maplist_names.json")
                         .read_text(encoding="utf-8"))
    for e in entries:
        g, u = recover(e["name"])
        e["gbk"], e["utf8"] = g, u
        e["proper_utf16"] = any(ord(c) > 0xFF for c in (e["name"] or ""))
        e["suffix_fw"] = bool(SUFFIX_FW.search(e["name"] or ""))
        e["suffix_asc"] = bool(SUFFIX_ASC.search(e["name"] or ""))

    files = {}
    for p in sorted(GAME_DIR.iterdir()):
        if p.suffix.lower() not in (".yrm", ".mpr", ".map"):
            continue
        files[p.name] = parse_basic(p.read_bytes())

    # 散装文件条目候选名集合：ASCII 原样 + GBK 恢复 + UTF-8 恢复
    loose_names = {}
    for fn, b in files.items():
        if not b:
            loose_names[fn] = []
            continue
        nm = (b.get("Name") or "").strip()
        cands = {nm}
        try:
            cands.add(nm.encode("gbk").decode("gbk"))
        except Exception:
            pass
        # 文件名本身（去扩展名）也是候选：有的图 [Basic].Name 缺失
        cands.add(Path(fn).stem)
        loose_names[fn] = [c for c in cands if c]

    entry_names = set()
    for e in entries:
        for k in ("name", "gbk", "utf8"):
            if e.get(k):
                entry_names.add(e[k].strip())

    matched_files = {}
    for fn, cands in loose_names.items():
        hit = [c for c in cands if c in entry_names]
        matched_files[fn] = hit

    n_loose_matched_entries = 0
    all_loose_cands = set()
    for v in loose_names.values():
        all_loose_cands.update(v)
    used_entries = set()
    for e in entries:
        cands = {e.get("name", "").strip(), (e.get("gbk") or "").strip(),
                 (e.get("utf8") or "").strip()} - {""}
        if any(c in all_loose_cands for c in cands):
            used_entries.add(e["index"])
    n_builtin = len(entries) - n_loose_matched_entries

    print("=== 划分恒等式 ===")
    print("entries=%d  散装可对上=%d  内置本地化(推断)=%d"
          % (len(entries), n_loose_matched_entries, n_builtin))
    print("files=%d  散装对上列表=%d  未上列表=%d"
          % (len(files),
             sum(1 for v in matched_files.values() if v),
             sum(1 for v in matched_files.values() if not v)))

    # 内置条目细分
    builtin = [e for e in entries if e["index"] not in used_entries]
    print("--- 内置推断条目 %d 条：后缀分布 ---" % len(builtin))
    from collections import Counter
    cnt = Counter()
    for e in builtin:
        sfx = "（fw）" if e["suffix_fw"] else ("(asc)" if e["suffix_asc"] else "无")
        cnt[sfx] += 1
    print(dict(cnt))
    fw8 = [e for e in builtin if e["suffix_fw"] and "2-8" in e["name"]]
    print("（2-8）内置条目：", [(e["index"], e["name"]) for e in fw8])
    non_suffix = [e for e in builtin
                  if not e["suffix_fw"] and not e["suffix_asc"]]
    print("--- 内置推断中无后缀条目 %d 条 ---" % len(non_suffix))
    for e in non_suffix[:40]:
        print("   [%3d] %r gbk=%r utf8=%r" % (e["index"], e["name"],
                                              e["gbk"], e["utf8"]))

    # 未上列表文件细分
    unlisted = [fn for fn, v in matched_files.items() if not v]
    cls = Counter()
    for fn in unlisted:
        b = files.get(fn) or {}
        off = (b.get("Official") or "").lower()
        mp = b.get("MultiplayerOnly")
        if not b:
            cls["no_basic"] += 1
        elif mp == "0":
            cls["mp_only=0(战役图)"] += 1
        elif off == "yes":
            cls["official=yes"] += 1
        else:
            cls["other"] += 1
    print("--- 未上列表文件 %d 个分类：%s ---" % (len(unlisted), dict(cls)))
    print("B 文件:", B_FILENAME, "在未上列表中 =", B_FILENAME in unlisted)

    # 8 人图专项
    unlisted_8p = [fn for fn in unlisted
                   if (files.get(fn) or {}).get("MaxPlayer") == "8"]
    print("--- 未上列表的 8 人图 %d 个 ---" % len(unlisted_8p))
    for fn in unlisted_8p:
        b = files.get(fn) or {}
        print("   %-44s name=%r off=%s" % (fn, b.get("Name"),
                                           b.get("Official")))

    (W17 / "maplist_reconcile2.json").write_text(
        json.dumps({"entries": [
            {k: e.get(k) for k in ("index", "name", "gbk", "utf8",
                                   "proper_utf16", "suffix_fw", "suffix_asc")}
            for e in entries],
            "loose_match": {k: v for k, v in matched_files.items()},
            "used_entry_indices": sorted(used_entries),
            "unlisted_files": unlisted},
            ensure_ascii=False, indent=1), encoding="utf-8")
    print("written maplist_reconcile2.json")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
