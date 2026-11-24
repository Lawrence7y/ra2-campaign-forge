#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W45 / B-half - offline analysis of the round-3 dual-track evidence.

Reads out/<tag>_result.json (A1,A2,B1,B2) and out/w45_dual_track.ndjson,
applies the PRE-DECLARED criteria from EQUIVALENCE_SPEC.md §3, writes
out/analysis.json.  Pure offline; no game, no writes outside this card.

IMPORTANT: no threshold is adjusted here.  Verdicts are
  等价 / 不等价 / 不可判, and "不可判" is a first-class result.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W45_b_line_equivalence"
OUT = CARD / "out"
TAGS = ("A1", "A2", "B1", "B2")
K_EXPECTED_BATTLE_DELTA = 1        # pre-declared in EQUIVALENCE_SPEC.md §2.5 / W2
RATE_THRESHOLD_PCT = 0.5            # pre-declared (RE-N04), never loosened
ESC_REQUIRED = ("GUI:AbortMission", "GUI:GameControls", "GUI:GameOptions",
                "GUI:LoadGame", "GUI:ResumeMission", "GUI:SaveGame")

R = {t: json.loads((OUT / (t + "_result.json")).read_text(encoding="utf-8"))
     for t in TAGS}


def get(tag, *keys, default=None):
    x = R[tag]
    for k in keys:
        if not isinstance(x, dict):
            return default
        x = x.get(k)
    return x if x is not None else default


def verdict_line(quantity, verdict, reason, **kw):
    return {"quantity": quantity, "verdict": verdict, "reason": reason, **kw}


def pct_diff(a, b):
    if a in (None, 0) or b is None:
        return None
    return round(abs(a - b) / a * 100.0, 5)


def analyse():
    lines = []

    # ---------------- 1. timer [0xA8ED84] ----------------
    rates = {t: get(t, "timer", "rate_cps") for t in TAGS}
    ge64 = {t: get(t, "timer", "intervals_ge64ms", default=0) for t in TAGS}
    ge2 = {t: get(t, "timer", "delta_frame_ge2", default=0) for t in TAGS}
    read_fail = {t: get(t, "timer", "read_fail", default=-1) for t in TAGS}
    walls = {t: get(t, "timer", "wall_s", default=0) for t in TAGS}
    med = {t: get(t, "timer", "interval_median_ms") for t in TAGS}
    p95 = {t: get(t, "timer", "interval_p95_ms") for t in TAGS}
    p99 = {t: get(t, "timer", "interval_p99_ms") for t in TAGS}
    a_mean = (rates["A1"] + rates["A2"]) / 2.0
    # N = same-arm noise band = A1 vs A2 directly (spec §2.4), NOT vs mean.
    N_rate_pct = pct_diff(rates["A2"], rates["A1"])
    D = {b: pct_diff(a_mean, rates[b]) for b in ("B1", "B2")}
    noise_unstable = (N_rate_pct is not None and N_rate_pct > RATE_THRESHOLD_PCT)
    ge64_noisy = len(set(ge64.values())) > 1
    ge2_noisy = len(set(ge2.values())) > 1
    hard_fail = (any(v > 0 for v in ge64.values())
                 or any(v > 0 for v in ge2.values())
                 or any(v != 0 for v in read_fail.values())
                 or any(v < 60 for v in walls.values()))
    if noise_unstable or ge64_noisy or ge2_noisy or hard_fail:
        v = "不可判"
        why = ("同臂噪声基线不成立：A1/A2 速率差 %.3f%% > %.1f%% 预设阈；"
               "≥64 ms 间隔数 A1/A2/B1/B2 = %s（噪声带本身含非零）；"
               "Δframe>=2 = %s。按规格 §3.1/§3.7 不得判等价，也不得把"
               "B 与 A 的差异归因于改造。"
               % (N_rate_pct, RATE_THRESHOLD_PCT,
                  [ge64[t] for t in TAGS], [ge2[t] for t in TAGS]))
    elif all(d is not None and d <= RATE_THRESHOLD_PCT for d in D.values()):
        v, why = "等价", "全部判据在阈值内"
    else:
        v, why = "不等价", "速率差超出预设 0.5% 阈值"
    lines.append(verdict_line("局内定时器 [0xA8ED84]", v, why,
                              rates_cps=rates, wall_s=walls,
                              read_fail=read_fail, intervals_ge64ms=ge64,
                              delta_frame_ge2=ge2,
                              interval_median_ms=med, interval_p95_ms=p95,
                              interval_p99_ms=p99,
                              A_mean_rate=a_mean, noise_band_pct=N_rate_pct,
                              D_B_vs_A_pct=D, threshold_pct=RATE_THRESHOLD_PCT,
                              secondary_observation=(
                                  "A1 存在单次 344 ms 长间隔，是 A 臂内的环境瞬态；"
                                  "A2/B1/B2 三者速率互相差异 <=0.04%，中位/p95/p99 "
                                  "全为 31/47/47 ms。此为补充说明，不覆盖主判定。")))

    # ---------------- 2/6. Esc control set & visibility ----------------
    req = {}
    full_sets = {}
    stable = {}
    for t in TAGS:
        polls = R[t].get("esc_polls") or []
        stable[t] = bool(R[t].get("esc_stable")) and len(polls) == 3
        # required 6 as (text, cls, visible, ctrl_id) tuples
        tuples = set()
        for p in polls:
            for item in p:
                if len(item) >= 4 and item[0] in ESC_REQUIRED:
                    tuples.add(tuple(item[:4]))
        req[t] = sorted(tuples)
        full_sets[t] = sorted(set(tuple(x[:4]) for x in polls[0])) if polls else []
    base_req = req["A1"]
    base_full = full_sets["A1"]
    req_equal = all(req[t] == base_req for t in TAGS)
    full_equal = all(full_sets[t] == base_full for t in TAGS)
    req_hits = {t: R[t].get("esc_required_hits") for t in TAGS}
    all_6 = all(sorted(req_hits[t] or []) == sorted(ESC_REQUIRED) for t in TAGS)
    esc_opened = {t: R[t].get("esc_menu_opened") for t in TAGS}
    if not all(esc_opened.values()):
        v, why = "不可判", "某臂 Esc 菜单未打开"
    elif all_6 and req_equal and all(stable.values()):
        v = "等价"
        why = ("四臂均命中 6/6 必需控件，(text,cls,visible,ctrl_id) 集合相同，"
               "3 次轮询稳定" + ("" if full_equal else
               "；全控件集合存在 OS 瞬态窗口差异（见 full_set_equal）"))
    elif all_6 and not req_equal:
        v, why = "不等价", "必需控件的 (cls,visible,ctrl_id) 在两臂不同"
    else:
        v, why = "不可判", "必需控件未全部命中或轮询不稳定"
    lines.append(verdict_line("局内 Esc 菜单控件集合 / 控件可见性", v, why,
                              esc_menu_opened=esc_opened,
                              required_hits=req_hits,
                              required_tuples_equal=req_equal,
                              full_control_set_equal=full_equal,
                              polls_stable=stable,
                              required_tuples_A1=base_req,
                              full_set_sizes={t: len(full_sets[t]) for t in TAGS},
                              note=("全集合含 MSCTFIME/CiceroUIWndFrame 等 OS 瞬态窗口；"
                                    "本卡以必需 6 控件集合 + visible 为主判据。")))

    # ---------------- 3. read-only RPM fields ----------------
    scen = {t: get(t, "counters_at_ingame", "scen_filename") for t in TAGS}
    bidx = {t: get(t, "counters_at_ingame", "scen_battle_idx") for t in TAGS}
    bcnt = {t: get(t, "counters_at_ingame", "battle_cnt") for t in TAGS}
    phase_same = len(set(scen.values())) == 1 and len(set(bidx.values())) == 1
    if not phase_same:
        v, why = "不可判", "两臂进入的不是同一官方场景（相位错）"
    else:
        a_cnt = {bcnt["A1"], bcnt["A2"]}
        b_cnt_set = {bcnt["B1"], bcnt["B2"]}
        a_stable = len(a_cnt) == 1
        delta_ok = all(b - list(a_cnt)[0] == K_EXPECTED_BATTLE_DELTA
                       for b in b_cnt_set) if a_stable else False
        if not a_stable:
            v, why = "不可判", "A 臂 battle_cnt 自身不稳"
        elif delta_ok:
            v = "等价"
            why = ("scen_filename / scen_battle_idx 严格相等；battle_cnt "
                   "B−A == k=%d（白名单 W2，k 由 BATTLEMD98.INI 的 "
                   "'15=RA2F1' 事先算出）" % K_EXPECTED_BATTLE_DELTA)
        else:
            v, why = "不等价", "battle_cnt 的 B−A != 事先声明的 k"
    lines.append(verdict_line("只读 RPM 字段（scen_filename/scen_battle_idx/battle_cnt）",
                              v, why, scen_filename=scen,
                              scen_battle_idx=bidx, battle_cnt=bcnt,
                              k_declared=K_EXPECTED_BATTLE_DELTA,
                              whitelist="W2"))

    # ---------------- 4. save file bytes ----------------
    saves = {t: R[t].get("save") for t in TAGS}
    ok_saves = {t: saves[t] for t in TAGS if saves[t]}
    shas = {t: (saves[t] or {}).get("sha256") for t in TAGS}
    sizes = {t: (saves[t] or {}).get("size") for t in TAGS}
    a_same = shas["A1"] == shas["A2"] if shas["A1"] and shas["A2"] else False
    if len(ok_saves) < 4:
        v, why = "不可判", "有臂未产出存档（%d/4）" % len(ok_saves)
    elif not a_same:
        v, why = ("不可判",
                  "同臂 A1/A2 存档字节已不同（sha %s / %s，size %s / %s）："
                  "噪声基线不成立，按规格 §3.4 只能写「无法判定」，"
                  "不得把 B 与 A 的差异归因于改造。"
                  % (str(shas["A1"])[:8], str(shas["A2"])[:8],
                     sizes["A1"], sizes["A2"]))
    elif all(shas[b] == shas["A1"] for b in ("B1", "B2")):
        v, why = "等价", "全字节 + sha256 + size 相同"
    else:
        v, why = "不等价", "B 与 A 存档字节不同且 A1==A2"
    lines.append(verdict_line("存档文件字节", v, why,
                              sha256=shas, size=sizes,
                              names={t: (saves[t] or {}).get("name") for t in TAGS},
                              copies={t: (saves[t] or {}).get("copy") for t in TAGS},
                              note=("存档文件名由引擎自动生成、各趟不同；本卡比较"
                                    "内容字节而非文件名。未事先声明非确定字段白名单。")))

    # ---------------- 5. verify exit code (install-state GATE only) ----------
    pre = {t: R[t].get("verify_pre_rc") for t in TAGS}
    post = {t: R[t].get("verify_post_rc") for t in TAGS}
    manifest = {t: (R[t].get("verify_pre_json") or {}).get("manifest_present")
                for t in TAGS}
    install = {t: R[t].get("install_rc") for t in TAGS}
    gate_ok = (all(pre[t] == 0 and post[t] == 0 for t in TAGS)
               and all(install[t] in (None, 0) for t in TAGS)
               and manifest["A1"] is False and manifest["A2"] is False
               and manifest["B1"] is True and manifest["B2"] is True)
    lines.append(verdict_line("verify 退出码（安装态门禁，非行为证据）",
                              "等价（门禁通过）" if gate_ok else "不等价（门禁失败）",
                              "verify exit 0 只证安装态；按规格 §3.5 不计入六项行为结论通过数",
                              verify_pre_rc=pre, verify_post_rc=post,
                              install_rc=install, manifest_present=manifest,
                              is_behavior_evidence=False))

    # ---------------- global ----------------
    behaviour = [l for l in lines[:4]] + [lines[4]]  # 1,2/6,3,4,5 excluded? keep all
    undecidable = [l["quantity"] for l in lines if l["verdict"] == "不可判"]
    inequivalent = [l["quantity"] for l in lines if "不等价" in l["verdict"]]
    if undecidable or inequivalent:
        overall = "无法判定"
    else:
        overall = "等价（限本镜像/本机/本配置/单机/官方场景/本时段）"
    return {
        "kind": "w45_equivalence_analysis",
        "source": "round-3 authoritative run (A1,A2,B1,B2; 75 s per arm, 6 ms cadence)",
        "spec": "EQUIVALENCE_SPEC.md §3 (thresholds pre-declared, not adjusted)",
        "k_declared": K_EXPECTED_BATTLE_DELTA,
        "per_comparable": lines,
        "undecidable_quantities": undecidable,
        "inequivalent_quantities": inequivalent,
        "overall_verdict": overall,
        "noise_baseline": {"A1_vs_A2_rate_pct": N_rate_pct,
                           "A1_vs_A2_save_identical": a_same,
                           "ge64_counts": ge64, "ge2_counts": ge2},
        "scope_limitations": [
            "渲染侧/逐帧渲染等价不可判（注入被禁，规格 §4.1）",
            "函数级/按 tick 对象状态/RNG/事件顺序对拍不可判（规格 §4.2）",
            "干净零售金标准未定谳，A 臂不是官方未修改原版（规格 §4.3）",
            "联机/跨进程存读档/全战役链/其它分辨率与汉化版本不在范围（规格 §4.4）",
            "臂 C（安装期禁用某特性）不可实现（规格 §2.2 / §4.6）",
            "本卡只走官方既有战役路径，不判定新增战役/地图内容的行为",
        ],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = analyse()
    (OUT / "analysis.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    print(json.dumps(d, ensure_ascii=True, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
