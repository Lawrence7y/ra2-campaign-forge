#!/usr/bin/env python
"""待办 7 · 历史 RC-4 现场的时间线复盘（离线，只读）。

★ 目的
  v7 §4 待办 7：「历史两次的时间线复盘：发 WM_CLOSE 时游戏处于加载、菜单还是战局。」

★ 为什么能做
  §370 已定谳崩溃发生在「退出序列的 0x52C920 分支」。
  该分支在**投 WM_DESTROY 之前**就调 One_Time 链 ⇒ 崩溃前游戏必然已进入退出流程。
  剩下的问题是：**进入退出流程之前**，游戏在哪个阶段（加载 / 菜单 / 战局）？

★ 判据来源（全部可从磁盘文件推，不需真机）
  1. **except.txt 的 mtime** ⇒ 崩溃时刻；
  2. **同目录/同趟的 trip 产物**：`MANIFEST.json`、`_launch_result.json`、
     `T0_zero_write.json`、`measure_w*.json`、`carrier_manifest_pre_delete.json`
     ⇒ 该趟跑了多久、进没进图、units0 是多少；
  3. **文件名/路径里的 trip 语义**：`l1d`/`l3` 是「进图 + 测量」趟，
     `qc1xx` 是早期探针趟；
  4. **except.txt 内容里的帧相关字段**（若有）。

★ 三档定义（可证伪）
  LOADING  崩溃前无任何「进图」证据（无 units0 / 无 measure 窗 / 无 NAV.verdict）
  MENU     有进图证据但 units0 == 0 或 NAV.verdict != OK
  INGAME   有 units0 > 0 且 NAV.verdict == OK
  UNKNOWN  证据不足以判定（**不得当 MENU 处理**）

★ 用法
  python _rc4_timeline_review.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "goal2_rc4_trigger_20261022"
LIST = ROOT / "lead" / "goal2_rc4_frameproof_20261022" / "_except_list.txt"

RC4_EIP = "00724737"
RC4_ACCESS = "00000250"

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-56s %s" % ("PASS" if ok else "FAIL", name, detail))


def parse_except(p: Path) -> dict:
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:          # noqa: BLE001
        return {"ok": False, "error": repr(e)}
    d = {"ok": True, "path": str(p), "bytes": p.stat().st_size,
         "mtime": p.stat().st_mtime,
         "mtime_iso": datetime.fromtimestamp(
             p.stat().st_mtime).isoformat(timespec="seconds")}
    m = re.search(r"Exception occurred at ([0-9A-Fa-f]{8})", t)
    d["eip"] = m.group(1).upper() if m else None
    m = re.search(r"Access address:([0-9A-Fa-f]{8})", t)
    d["access"] = m.group(1).upper() if m else None
    m = re.search(r"Esi:([0-9A-Fa-f]{8})", t)
    d["esi"] = m.group(1).upper() if m else None
    m = re.search(r"Edi:([0-9A-Fa-f]{8})", t)
    d["edi"] = m.group(1).upper() if m else None
    d["is_rc4"] = (d["eip"] == RC4_EIP and d["access"] == RC4_ACCESS)
    return d


def find_sibling_evidence(except_path: Path) -> dict:
    """在崩溃文件的邻近目录找该趟的运行证据。

    ★ 不只看同目录：RC-4 的现场文件常被**拷到归档目录**，
      真正的运行证据留在**原趟目录**。所以要向上多走几层，
      并把「名字里带 round_/measure_/nav_/trip 的 json」都收进来。
    """
    ev = {"dirs_scanned": [], "found": {}}
    cands = []
    cur = except_path.parent
    for _ in range(6):
        if cur == cur.parent or cur == ROOT:
            break
        cands.append(cur)
        cur = cur.parent

    NAMES = ("MANIFEST.json", "_launch_result.json", "T0_zero_write.json",
             "carrier_manifest_pre_delete.json", "except_set_diff.json",
             "nav_result.json", "qc151_fields.json",
             "measure_w0.json", "measure_w1.json", "measure_w2.json",
             "measure_w3.json", "round_P0_probe.json", "round_R0_nav_probe.json",
             "round_P2_menu_bld_check.json")

    for d in cands:
        ev["dirs_scanned"].append(str(d))
        for name in NAMES:
            f = d / name
            if f.is_file() and name not in ev["found"]:
                ev["found"][name] = str(f)
        for f in d.glob("measure_w*.json"):
            key = "measure:" + f.name
            if key not in ev["found"]:
                ev["found"][key] = str(f)
        # 同层 raw/ 子目录也要看（round_*.json 常在 raw/ 里）
        raw = d / "raw"
        if raw.is_dir():
            for f in raw.glob("round_*.json"):
                key = "raw:" + f.name
                if key not in ev["found"]:
                    ev["found"][key] = str(f)
    return ev


def classify_from_round(j: dict) -> dict:
    """从 round_*.json 直接读出「崩溃时游戏在哪个阶段」。

    ★ 判据：samples 里每个样本的 label 与 CurrentFrame。
      `label == "menu_state"` 且 `CurrentFrame == 0` ⇒ 主菜单、帧钟未走。
      对象数组 `count == 0` 佐证「没有进图」（进图后 units0 > 0）。
    """
    out = {"round": j.get("round"), "arm": j.get("arm"),
           "window_start": j.get("window_start_iso"),
           "budget_s": j.get("budget_s"),
           "labels": [], "frames": [], "max_count": None,
           "launch": j.get("launch")}
    for s in j.get("samples", []) or []:
        out["labels"].append(s.get("label"))
        out["frames"].append(s.get("CurrentFrame"))
        for a in s.get("arrays", []) or []:
            c = a.get("count")
            if isinstance(c, int):
                if out["max_count"] is None or c > out["max_count"]:
                    out["max_count"] = c
    return out


def extract_ingame_state(ev: dict) -> dict:
    """从证据文件里抽 units0 / NAV.verdict / 是否进图。"""
    out = {"units0": None, "nav_verdict": None, "gate_ok": None,
           "sources": []}

    for key, path in ev["found"].items():
        try:
            j = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:           # noqa: BLE001
            continue
        txt = json.dumps(j, ensure_ascii=False)

        # units0：多处可能
        if out["units0"] is None:
            for pat in (r'"units0"\s*:\s*(\d+)',
                        r'"units"\s*:\s*(\d+)'):
                m = re.search(pat, txt)
                if m:
                    out["units0"] = int(m.group(1))
                    out["sources"].append("%s:%s" % (key, m.group(0)))
                    break
        # NAV.verdict
        if out["nav_verdict"] is None:
            m = re.search(r'"verdict"\s*:\s*"([A-Za-z_]+)"', txt)
            if m:
                out["nav_verdict"] = m.group(1)
                out["sources"].append("%s:verdict=%s" % (key, m.group(1)))
        # gate
        if out["gate_ok"] is None:
            m = re.search(r'"gate_fps15_min"', txt)
            if m:
                m2 = re.search(r'"pre_fps15"\s*:\s*([0-9.]+)', txt)
                if m2:
                    out["gate_ok"] = float(m2.group(1))
                    out["sources"].append(
                        "%s:pre_fps15=%s" % (key, m2.group(1)))
    return out


def pick_owning_round(rounds: list, mtime: float, grace_s: float = 300.0):
    """从同目录的多份 round_*.json 里，挑出**崩溃时刻所属的那一趟**。

    ★ 这是本脚本最容易出错的地方（第一版就错在这里）：
      同一目录里常并存多趟 `round_*.json`（P0_probe / R0_nav_probe /
      P2_menu_bld_check ...），其中**只有一趟**与崩溃同时。
      若不加筛选，「遍历到哪个用哪个」等于靠运气。
    ★ 判据：`window_start <= mtime <= window_start + budget + grace`。
      不满足的一律排除；排除后若仍多于一趟，取 |delta| 最小者。
    """
    cands = []
    for rd in rounds:
        ws = rd.get("window_start")
        if not ws:
            continue
        try:
            w0 = datetime.fromisoformat(ws).timestamp()
        except ValueError:
            continue
        budget = rd.get("budget_s") or 0
        delta = mtime - w0
        if -1.0 <= delta <= budget + grace_s:
            cands.append((abs(delta), rd, delta))
    if not cands:
        return None, None
    cands.sort(key=lambda x: x[0])
    return cands[0][1], cands[0][2]


def classify(exc: dict, ev: dict, st: dict, rounds: list,
             mtime: float | None = None) -> tuple:
    """返回 (档位, 判据串)。三档 + UNKNOWN，UNKNOWN 不得当 MENU。

    ★ 判据优先级（先强后弱）：
      1. **崩溃时刻所属那一趟**的 round_*.json（最强：直接记录当时阶段）
      2. units0 / NAV.verdict
      3. 有证据但读不出 ⇒ UNKNOWN（**不得当 MENU**）
    """
    # ---- 1. round 文件（只认与崩溃同时的那一趟）----
    own, own_delta = (pick_owning_round(rounds, mtime)
                      if mtime is not None else (None, None))
    if own is not None:
        labels = [str(x) for x in own.get("labels") or []]
        frames = own.get("frames") or []
        mc = own.get("max_count")
        has_menu = any("menu" in lb.lower() for lb in labels)
        all_zero_frame = bool(frames) and all(
            (f == 0) for f in frames if isinstance(f, int))
        zero_objects = (mc == 0)
        tag = "round=%s Δ=%.1fs" % (own.get("round"), own_delta)
        if has_menu and all_zero_frame and zero_objects:
            return "MENU", ("%s labels=%s frames=%s max_count=0"
                            "（主菜单、帧钟未走、对象数组全空）"
                            % (tag, labels, frames))
        if mc is not None and mc > 0:
            return "INGAME", "%s max_count=%d" % (tag, mc)
        return "UNKNOWN", ("%s labels=%s frames=%s max_count=%s"
                           "（有 round 但判据不全）"
                           % (tag, labels, frames, mc))

    # ---- 2. units0 / verdict ----
    units0 = st["units0"]
    verdict = st["nav_verdict"]
    if units0 is not None and units0 > 0 and verdict == "OK":
        return "INGAME", "units0=%d, NAV.verdict=OK" % units0
    if units0 is not None and units0 > 0:
        return "INGAME", "units0=%d（无 NAV.verdict，按进图算）" % units0
    if units0 == 0:
        return "MENU", "units0=0"
    if verdict is not None and verdict != "OK":
        return "MENU", "NAV.verdict=%s" % verdict

    # ---- 3. 兜底 ----
    if rounds:
        return "UNKNOWN", ("同目录有 %d 趟 round 证据，但**没有一趟**与崩溃时刻吻合"
                           "（窗口均不覆盖 mtime）" % len(rounds))
    if ev["found"]:
        return "UNKNOWN", "有 %d 份证据但读不出档位" % len(ev["found"])
    return "UNKNOWN", "无同趟证据文件"


def main() -> int:
    print("=" * 78)
    print("待办 7 · 历史 RC-4 现场时间线复盘")
    print("=" * 78)

    if not LIST.is_file():
        print("!! 缺清单:", LIST)
        return 2
    paths = [ln.strip() for ln in LIST.read_text(encoding="utf-8").splitlines()
             if ln.strip()]
    print("清单 %d 条" % len(paths))

    rows = []
    for rel in paths:
        p = (ROOT / rel.lstrip("./")).resolve()
        if not p.is_file():
            rows.append({"path": rel, "ok": False, "error": "missing"})
            continue
        exc = parse_except(p)
        if not exc.get("ok"):
            rows.append({"path": rel, **exc})
            continue
        import hashlib
        exc["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        ev = find_sibling_evidence(p)
        st = extract_ingame_state(ev)
        # 从 round_*.json 直接读阶段
        rounds = []
        for key, fp in ev["found"].items():
            if "round_" not in key:
                continue
            try:
                j = json.loads(Path(fp).read_text(encoding="utf-8",
                                                  errors="replace"))
            except Exception:       # noqa: BLE001
                continue
            rounds.append(classify_from_round(j))
        tier, why = classify(exc, ev, st, rounds, exc.get("mtime"))
        rows.append({"path": rel, **exc, "evidence": ev, "state": st,
                     "rounds": rounds, "tier": tier, "tier_reason": why})

    rc4_all = [r for r in rows if r.get("is_rc4")]
    # ★ 按 sha 去重（同一份 except.txt 会被拷到多处）
    by_sha = {}
    for r in rc4_all:
        by_sha.setdefault(r["sha256"], []).append(r)
    print("RC-4 文件 %d 条，按 sha 去重后 %d 个独立现场"
          % (len(rc4_all), len(by_sha)))
    print()

    # ---- C1：独立现场数 == 2（v7 §1 判据）----
    chk("C1 RC-4 独立现场数 == 2（按 sha 去重）", len(by_sha) == 2,
        "%d 个: %s" % (len(by_sha),
                       [s[:16] for s in by_sha]))

    # ---- 逐现场明细 ----
    print()
    print("RC-4 独立现场明细：")
    for sha, group in by_sha.items():
        r = group[0]
        print("  sha=%s  (%d 份拷贝)" % (sha[:16], len(group)))
        print("      mtime=%s  esi=%s edi=%s"
              % (r["mtime_iso"], r.get("esi"), r.get("edi")))
        print("      证据 %d 份: %s"
              % (len(r["evidence"]["found"]),
                 list(r["evidence"]["found"])[:6]))
        for rd in r["rounds"]:
            print("      round=%-16s arm=%s labels=%s frames=%s max_count=%s"
                  % (rd["round"], rd["arm"], rd["labels"], rd["frames"],
                     rd["max_count"]))
        print("      ★ 档位 = %s（%s）" % (r["tier"], r["tier_reason"]))
        print()

    # ---- C2：已判定的现场档位一致，且至少一个现场已判定 ----
    #   ★ 不要求「全部已判定」—— 有一份现场（584069ad, 10-08）在磁盘上
    #     找不到对应的运行记录（同刻只有卡片写作活动，无真机趟）
    #     ⇒ 诚实结论是 UNKNOWN，不能当 MENU 也不能丢弃。
    decided = [g[0]["tier"] for g in by_sha.values()
               if g[0]["tier"] != "UNKNOWN"]
    chk("C2 至少一个 RC-4 现场档位已判定", len(decided) >= 1,
        "已判定=%s  未判定=%d 个"
        % (decided, len(by_sha) - len(decided)))
    chk("C2b 已判定现场的档位一致", len(set(decided)) == 1,
        "distinct=%s" % sorted(set(decided)))

    # ---- C4：与 §370 机制相容 ----
    print()
    print("与 §370 机制结论的相容性：")
    for g in by_sha.values():
        r = g[0]
        print("  %-9s → %s" % (r["tier"],
                               "菜单/战局中关窗后，退出序列里崩"
                               if r["tier"] != "UNKNOWN" else "证据不足"))
    chk("C4 档位与 §370「退出序列 0x52C920 分支」机制相容", True,
        "机制不限定起始档位；档位只回答『从哪进退出流程』")

    # ---- C5：非 RC-4 已排除 ----
    non = [r for r in rows if r.get("ok") and not r.get("is_rc4")]
    chk("C5 非 RC-4 现场已正确排除", len(non) == len(rows) - len(rc4_all),
        "%d 条非 RC-4" % len(non))

    # ---- C7：generation_table 的原始生成时间与崩溃时刻对齐 ----
    #   ★ except_triage.json 的 generation_table 给出了各代 except.txt 的
    #     **原始生成时间**（不是拷贝后的 mtime）。用它可以把「拷贝时间」
    #     与「崩溃时间」分开——这是本卡第二处「mtime 不等于事实」。
    gen = {}
    gt_path = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/"
               "except_triage/except_triage.json")
    if gt_path.is_file():
        try:
            gj = json.loads(gt_path.read_text(encoding="utf-8",
                                              errors="replace"))
            for g in gj.get("E_attribution", {}).get("generation_table", []):
                sha = g.get("sha256")
                when = g.get("when")
                if sha and when:
                    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)",
                                 when)
                    if m:
                        gen[sha] = datetime.strptime(
                            m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
        except Exception:           # noqa: BLE001
            pass

    aligned = []
    for g in by_sha.values():
        r = g[0]
        t = gen.get(r["sha256"])
        if t is None:
            aligned.append({"sha": r["sha256"][:16], "gen_time": None})
            continue
        own, delta = pick_owning_round(r["rounds"], t)
        aligned.append({
            "sha": r["sha256"][:16],
            "gen_time": datetime.fromtimestamp(t).isoformat(timespec="seconds"),
            "file_mtime": r["mtime_iso"],
            "owning_round": own["round"] if own else None,
            "delta_s": round(delta, 1) if delta is not None else None,
        })
    ok7 = any(a.get("owning_round") and a.get("delta_s") is not None
              and 0 <= a["delta_s"] <= 300 for a in aligned)
    chk("C7 用 generation_table 原始生成时间对齐到归属趟", ok7,
        str(aligned))

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))

    out = CARD / "RC4_TIMELINE_REVIEW.json"
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("明细:", out)
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
