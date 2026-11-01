# -*- coding: utf-8 -*-
"""_audit_batch6_recompute.py — XVERIFY_BATCH6 独立复算（A 线审计临时件，只读原始记录）。

对 c2ab_x/ 下 12 个 2026-10-28 趟目录逐趟复算：
  close_rows 轴（hwnd/singleton/frame/exitstate/wait/code）、终态字段、
  battle fps、post_windows（#32770 / 关窗后窗口）、菜单臂 menu_ready。
只读，不写任何文件（stdout 输出）。
"""
import json
import statistics
from pathlib import Path

BASE = Path(__file__).resolve().parent
TRIPS = [
    "20261028T084855_0001_P0_ORIG",
    "20261028T085311_0001_P0N_INJ_OFF",
    "20261028T085640_0001_P1_G1B0exp",
    "20261028T090813_0001_P2_G1B0def",
    "20261028T091330_0001_P3_G1B1",
    "20261028T092052_0001_P3m_MENU",
    "20261028T192013_0001_P0_ORIG",
    "20261028T192830_0001_P1_G1B0exp",
    "20261028T193722_0001_P3m_MENU",
    "20261028T204123_9001_P3e_EARLY_MENU",
    "20261028T204921_9001_P3e_EARLY_MENU",
    "20261028T205108_9001_P3e_EARLY_MENU",
]


def fmt_set(vals):
    """值集合摘要：原样，元素为 dict 时归并为 state 标记。"""
    out = set()
    for v in vals:
        out.add(v["state"] if isinstance(v, dict) else v)
    return sorted(out, key=lambda x: str(x))


def axis(rows, name):
    return [r.get(name) for r in rows]


def first_idx(vals, pred):
    for i, v in enumerate(vals):
        if pred(v):
            return i
    return None


def main():
    for trip in TRIPS:
        d = BASE / trip
        rec = json.loads((d / "_rec.json").read_text(encoding="utf-8"))
        tl = json.loads((d / "timeline.json").read_text(encoding="utf-8"))
        t_close = rec["close_delivery"]["t"]
        closed_at = rec.get("closed_at_s")
        print("=" * 100)
        print("TRIP", trip)
        print("  rec: trip_tag=%s verdict=%s phase=%s watch_s=%s closed_at_s=%s" % (
            rec.get("trip_tag"), rec.get("verdict"), rec.get("phase"),
            rec.get("watch_s"), closed_at))
        print("  rec: exited=%s exit_kind=%r exit_after_close_s=%s final_exitcode=%s" % (
            rec.get("exited"), rec.get("exit_kind"),
            rec.get("exit_after_close_s"), rec.get("final_exitcode")))
        print("  rec: killed_on_cleanup=%s except_before=%s except_at=%s except_changed=%s" % (
            rec.get("killed_on_cleanup"), rec.get("except_before"),
            rec.get("except_at"), rec.get("except_changed")))
        print("  rec: a8_verdict=%s a8_remaining=%s carrier_deleted=%s" % (
            rec.get("a8_verdict"), rec.get("a8_remaining"), rec.get("carrier_deleted")))
        cd = rec.get("close_delivery", {})
        print("  rec: close_delivery post_ok=%s err=%s win_pid=%s loader_pid=%s gamemd_pid=%s" % (
            cd.get("post_ok"), cd.get("post_err"), cd.get("win_pid"),
            rec.get("loader_pid"), rec.get("gamemd_pid")))
        for k in ("menu_ready", "menu_ready_s", "in_battle", "window_at_s", "hold_tl_n",
                  "protocol", "play_s", "pre_close_5s_n", "close_rows_n"):
            if k in rec:
                print("  rec: %s=%s" % (k, rec[k]))
        sbc = rec.get("scene_before_close")
        if sbc:
            print("  scene_before_close: t_abs=%.3f frame=%s hwnd=%s sing=%s exitstate=%s" % (
                sbc.get("t", -1), sbc.get("frame"), sbc.get("hwnd"),
                sbc.get("singleton"), sbc.get("exitstate")))

        # ---- post_windows 面 ----
        pw = rec.get("post_windows", [])
        n_pw = len(pw)
        vis_counts = [len(e.get("visible", [])) for e in pw]
        has_32770 = any(any("#32770" in (w.get("class") or "") for w in e.get("visible", []))
                        for e in pw)
        first_empty = first_idx(vis_counts, lambda c: c == 0)
        reappear = [i for i, c in enumerate(vis_counts) if c > 0 and first_empty is not None and i > first_empty]
        titles = sorted({w.get("title") for e in pw for w in e.get("visible", [])})
        shown = vis_counts[:12] + (["..."] if n_pw > 12 else [])
        print("  post_windows: n=%d vis_counts=%s first_empty_idx=%s reappear_idx=%s #32770=%s titles=%s" % (
            n_pw, shown, first_empty, reappear, has_32770, titles))

        # ---- close_rows 轴复算 ----
        rows = tl["close_rows"]
        n = len(rows)
        t0c = rows[0]["t"]
        t_last = rows[-1]["t"]
        rel = [r["t"] - t_close for r in rows]  # 关窗后秒
        wait_vals = fmt_set(axis(rows, "wait"))
        code_vals = [r["code"] for r in rows if r["code"] is not None]
        es_vals = fmt_set(axis(rows, "exitstate"))
        hwnd_vals = fmt_set(axis(rows, "hwnd"))
        sing_vals = fmt_set(axis(rows, "singleton"))
        tick_vals = fmt_set(axis(rows, "tick"))
        print("  close_rows: n=%d rel_span=[%.2f..%.2f] wait_set=%s code_nonnull=%s tick_set=%s" % (
            n, rel[0], rel[-1], wait_vals, code_vals, tick_vals))
        print("  close_rows: exitstate_set=%s hwnd_set=%s singleton_set=%s" % (
            es_vals, hwnd_vals, sing_vals))

        hwnd0 = [r.get("hwnd") for r in rows]
        i_h0 = first_idx(hwnd0, lambda v: isinstance(v, dict) or v == 0)
        sing0 = [r.get("singleton") for r in rows]
        i_s0 = first_idx(sing0, lambda v: isinstance(v, dict) or v == 0)
        n_hwnd_nonzero = sum(1 for v in hwnd0 if not isinstance(v, dict) and v not in (0, None))
        n_sing_nonzero = sum(1 for v in sing0 if not isinstance(v, dict) and v not in (0, None))
        print("  hwnd/sing: first=%s/%s n_nonzero=%d/%d first_zero_rel=%s/%s" % (
            hwnd0[0], sing0[0], n_hwnd_nonzero, n_sing_nonzero,
            None if i_h0 is None else round(rel[i_h0], 2),
            None if i_s0 is None else round(rel[i_s0], 2)))

        es = [r.get("exitstate") for r in rows]
        i_es1 = first_idx(es, lambda v: isinstance(v, int) and v == 1)
        if i_es1 is not None:
            es_after = set(v for v in es[i_es1:] if not isinstance(v, dict))
            es_back0 = [v for v in es[i_es1:] if v == 0]
            print("  LATCH: first exitstate=1 @row%d rel=%.2fs (abs=%.2f) rows_after=%d vals_after=%s back_to_0=%d" % (
                i_es1, rel[i_es1], closed_at + rel[i_es1], n - i_es1,
                sorted(es_after), len(es_back0)))
            # wait 轴在 latch 后
            waits_after = fmt_set([r["wait"] for r in rows[i_es1:]])
            print("  LATCH: wait_set_after_latch=%s" % waits_after)

        fr = [r.get("frame") for r in rows]
        fr_ok = [(i, v) for i, v in enumerate(fr) if not isinstance(v, dict)]
        i_f0 = first_idx(fr, lambda v: isinstance(v, dict) or v == 0)
        n_fr_nonzero = sum(1 for v in fr if not isinstance(v, dict) and v not in (0, None))
        # 末个 frame>0 行、首个 frame==0 行、其后是否回正
        last_pos = max((i for i, v in enumerate(fr) if not isinstance(v, dict) and v and v > 0), default=None)
        n_pos_after_f0 = sum(1 for i, v in enumerate(fr) if i is not None and i_f0 is not None
                             and i > i_f0 and not isinstance(v, dict) and isinstance(v, int) and v > 0)
        print("  frame: first=%s last=%s n_nonzero=%d first_zero_rel=%s last_pos_row=%s last_pos_rel=%s pos_after_f0=%d" % (
            fr[0], fr[-1], n_fr_nonzero,
            None if i_f0 is None else round(rel[i_f0], 2),
            last_pos, None if last_pos is None else round(rel[last_pos], 2), n_pos_after_f0))

        # ---- battle_tl / hold_tl fps ----
        if "battle_tl" in tl:
            b = tl["battle_tl"]
            fo = [(r["t"], r.get("frame")) for r in b
                  if not isinstance(r.get("frame"), dict) and isinstance(r.get("frame"), int)]
            if len(fo) >= 2:
                (ta, fa), (tb, fb) = fo[0], fo[-1]
                total = (fb - fa) / (tb - ta) if tb > ta else None
                rates = [(fo[i + 1][1] - fo[i][1]) / (fo[i + 1][0] - fo[i][0])
                         for i in range(len(fo) - 1) if fo[i + 1][0] > fo[i][0]]
                print("  battle_tl: n=%d frame %d→%d span=%.1fs fps_total=%.3f fps_med=%.3f fps_min=%.3f fps_max=%.3f" % (
                    len(b), fa, fb, tb - ta, total or -1,
                    statistics.median(rates), min(rates), max(rates)))
            else:
                print("  battle_tl: n=%d (frame 可读样本不足)" % len(b))
        if "pre5" in tl and tl["pre5"]:
            last_pre = tl["pre5"][-1]["sent"]
            print("  pre5 last: frame=%s exitstate=%s hwnd=%s" % (
                last_pre.get("frame"), last_pre.get("exitstate"), last_pre.get("hwnd")))
        if "hold_tl" in tl:
            h = tl["hold_tl"]
            fo = [(r["t"], r.get("frame")) for r in h
                  if not isinstance(r.get("frame"), dict) and isinstance(r.get("frame"), int)]
            print("  hold_tl: n=%d frame_seq=%s" % (len(h), [v for _, v in fo]))

    print("=" * 100)
    print("DONE")


if __name__ == "__main__":
    main()
