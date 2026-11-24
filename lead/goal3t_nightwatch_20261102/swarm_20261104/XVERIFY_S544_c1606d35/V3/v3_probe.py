# -*- coding: utf-8 -*-
"""V3 §544 真机分诊独立复算：v4e / v4f / v4g 三趟对比。"""
import json, os, re, hashlib, itertools, struct
from collections import Counter
from PIL import Image
import numpy as np

ROOT = "D:/Project/ra2-campaign-forge"
TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3"
TAGS = ["l3_1101v4e", "l3_1101v4f", "l3_1101v4g"]


def load_fields(t):
    p = os.path.join(TRIPS, t, "qc151_fields.json")
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    # key is unique? check
    keys = [e["key"] for e in d]
    dup = [k for k, c in Counter(keys).items() if c > 1]
    return p, d, dup


def fieldmap(d):
    return {e["key"]: e for e in d}


def jsonable(v):
    try:
        json.dumps(v)
        return True
    except Exception:
        return False


print("=" * 100)
print("SECTION 1: qc151_fields.json 导航链逐字段差异表")
print("=" * 100)
fmaps = {}
for t in TAGS:
    p, d, dup = load_fields(t)
    fmaps[t] = fieldmap(d)
    print(f"{t}: entries={len(d)} unique_keys={len(fmaps[t])} duplicate_keys={len(dup)}")
    if dup:
        print("  DUP KEYS (first 10):", dup[:10])

# Navigation-chain fields named by the ask + stage seconds
NAV_PATTERNS = [
    r"^verify_ok_nav_",
    r"^signature_got_nav_",
    r"^step_clicked_nav_",
    r"^clicked_nav_",
    r"^focus_nav_",
    r"^attempts_nav_",
    r"^wait_screen_nav_",
    r"^in_tactical_target$",
    r"^seconds_to_window$",
    r"^window_stabilize_seconds$",
    r"^stage_begin:",
    r"^stage_seconds:",
    r"^h7_nav_end_t$",
    r"^h7_nav_to_measure$",
]
allnav = []
for t in TAGS:
    for k in fmaps[t]:
        if any(re.search(p, k) for p in NAV_PATTERNS):
            allnav.append(k)
allnav = sorted(set(allnav))
print(f"\n导航链字段并集: {len(allnav)} 个")

diffs = []
for k in allnav:
    vals = []
    for t in TAGS:
        e = fmaps[t].get(k)
        vals.append(e["value"] if e else "<MISSING>")
    same = vals[0] == vals[1] == vals[2]
    if not same:
        diffs.append((k, vals))
    mark = "SAME" if same else "DIFF"
    # short repr
    vr = []
    for v in vals:
        s = repr(v)
        if len(s) > 90:
            s = s[:87] + "..."
        vr.append(s)
    print(f"  [{mark}] {k:42s} | e={vr[0]:38s} | f={vr[1]:38s} | g={vr[2]:38s}")

print(f"\n*** 差异字段数: {len(diffs)} / {len(allnav)} ***")
for k, vals in diffs:
    print("  DIFF", k, "=>", vals)

# Also: what keys exist only in some trips? (presence diff)
print("\n--- 全字段 key 存在性差异（v4e 有而 f/g 没有，或反之）---")
ke = set(fmaps[TAGS[0]])
kf = set(fmaps[TAGS[1]])
kg = set(fmaps[TAGS[2]])
print("v4e only (not in f):", len(ke - kf), sorted(ke - kf)[:25])
print("f only (not in e):", len(kf - ke), sorted(kf - ke)[:25])
print("f vs g key diff:", len(kf ^ kg), sorted(kf ^ kg)[:25])

# Value equality across ALL common keys (not just nav)
common = ke & kf & kg
valdiff_all = []
for k in sorted(common):
    a, b, c = (fmaps[t][k]["value"] for t in TAGS)
    if not (a == b == c):
        valdiff_all.append((k, a, b, c))
print(f"\n--- 全字段（{len(common)} 个共有 key）取值差异数: {len(valdiff_all)} ---")
for k, a, b, c in valdiff_all[:60]:
    print(f"  {k:45s} e={repr(a)[:50]} f={repr(b)[:50]} g={repr(c)[:50]}")

print()
print("=" * 100)
print("SECTION 2: except_post_*.txt 异常 & except_set_diff.json")
print("=" * 100)
exc_info = {}
for t in TAGS:
    dd = os.path.join(TRIPS, t)
    files = sorted(fn for fn in os.listdir(dd) if fn.startswith("except_post_") and fn.endswith(".txt"))
    print(f"\n=== {t} except files: {files}")
    for fn in files:
        p = os.path.join(dd, fn)
        raw = open(p, "rb").read()
        txt = raw.decode("utf-8", errors="replace")
        sha = hashlib.sha256(raw).hexdigest()
        print(f"  {fn}: bytes={len(raw)} sha256={sha}")
        # Address patterns: 8-hex-digit addresses, "007CFC9F", Exception at, code
        addrs = re.findall(r"\b0?[0-9A-Fa-f]{8}\b", txt)
        print("   8-hex tokens (first 30):", addrs[:30])
        print("   distinct 8-hex tokens:", sorted(set(addrs))[:40], "count", len(set(addrs)))
        # search key address
        for key in ["007CFC9F", "0x007CFC9F", "Exception", "exception", "Access", "Eip", "code="]:
            hits = [m.start() for m in re.finditer(re.escape(key), txt)]
            if hits:
                print(f"   has {key!r}: {len(hits)} hits, first ctx: {txt[max(0,hits[0]-90):hits[0]+120]!r}")
        exc_info[t] = {"file": fn, "sha256": sha, "txt": txt, "raw": raw, "addrs": addrs}

# Compare exception text byte-wise
print("\n--- except_post 文本逐字节比对 ---")
for a, b in itertools.combinations(TAGS, 2):
    ra, rb = exc_info[a]["raw"], exc_info[b]["raw"]
    print(f"  {a} vs {b}: bytes {len(ra)}/{len(rb)} sha_equal={ra==rb}")
    # line-level diff
    la = exc_info[a]["txt"].splitlines()
    lb = exc_info[b]["txt"].splitlines()
    same_lines = sum(1 for x, y in itertools.zip_longest(la, lb) if x == y)
    diff_lines = [(i, x, y) for i, (x, y) in enumerate(itertools.zip_longest(la, lb)) if x != y]
    print(f"    lines {len(la)}/{len(lb)} identical_line_count={same_lines} diff_line_count={len(diff_lines)}")
    for i, x, y in diff_lines[:12]:
        print(f"      L{i}: e-side={str(x)[:120]!r} other={str(y)[:120]!r}")

print("\n--- except_set_diff.json ---")
for t in TAGS:
    p = os.path.join(TRIPS, t, "except_set_diff.json")
    raw = open(p, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    print(f"  {t}: bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()}")
    print("   ", json.dumps(d, ensure_ascii=False, indent=2)[:1200])

print()
print("=" * 100)
print("SECTION 3: measure_w0.json gate / samples.f 分布 / v4e 起点")
print("=" * 100)
for t in TAGS:
    p = os.path.join(TRIPS, t, "measure_w0.json")
    d = json.load(open(p, encoding="utf-8"))
    s = d["samples"]
    t_arr, f_arr = s["t"], s["f"]
    cf = Counter(f_arr)
    print(f"\n=== {t}")
    print("  gate:", d["gate"], " w1:", d["w1"])
    print("  verdict:", d["verdict"], " error:", d["error"])
    print("  span_s:", d["span_s"], " settle_s:", d["settle_s"], " hz:", d["hz"])
    print("  stats.fps_avg:", d["stats"]["fps_avg"], " stats.note:", d["stats"]["note"])
    print("  stats.samples:", d["stats"]["samples"], " stats.logic_frames:", d["stats"]["logic_frames"])
    print("  samples len:", len(t_arr), "/", len(f_arr))
    print("  samples.f distinct:", sorted(cf.items())[:20], "... total distinct", len(cf))
    print("  samples.f min/max:", min(f_arr), max(f_arr), " all_zero:", all(x == 0 for x in f_arr))
    print("  samples.f first 10:", f_arr[:10])
    print("  samples.f last 10:", f_arr[-10:])
    # runs of identical f
    runs = []
    cur, st, n = f_arr[0], 0, 0
    for i, v in enumerate(f_arr):
        if v == cur:
            n += 1
        else:
            runs.append((cur, st, i - 1, n))
            cur, st, n = v, i, 1
    runs.append((cur, st, len(f_arr) - 1, n))
    print("  samples.f runs (value,start,end,len) first 8:", runs[:8])
    print("  samples.f runs count:", len(runs), " last 3:", runs[-3:])
    print("  samples.t first 5:", [round(x, 6) for x in t_arr[:5]])
    print("  samples.t last 5:", [round(x, 6) for x in t_arr[-5:]])
    print("  frame_edges len:", len(d["frame_edges"]), "first:", d["frame_edges"][:2], "last:", d["frame_edges"][-2:])
    print("  counters len:", len(d["counters"]))
    c0 = d["counters"][0]
    print("  counters[0] units:", c0.get("units"), "keys:", list(c0.keys()))
    # dt gaps
    dts = [t_arr[i + 1] - t_arr[i] for i in range(len(t_arr) - 1)]
    print("  samples.t dt min/max:", round(min(dts), 8), round(max(dts), 8),
          " dt>0.01 count:", sum(1 for x in dts if x > 0.01))

# all measure_w*.json in each trip
print("\n--- 每趟 measure_w*.json 文件清单与 gate ---")
for t in TAGS:
    dd = os.path.join(TRIPS, t)
    for fn in sorted(x for x in os.listdir(dd) if re.match(r"measure_w\d+\.json$", x)):
        d = json.load(open(os.path.join(dd, fn), encoding="utf-8"))
        print(f"  {t}/{fn}: verdict={d['verdict']} gate={d['gate']} fps_avg={d['stats']['fps_avg']}")

print()
print("=" * 100)
print("SECTION 4: 截图 sha256 与逐像素差")
print("=" * 100)
PNGS = ["frame_target_01.png", "fs_boot_probe.png", "frame_early_01.png",
        "navsig_burst_00_g.png", "navsig_nav_menu_pre_00_g.png",
        "navsig_nav_menu_post_00_g.png", "navsig_nav_setup_pre_00_g.png",
        "navsig_nav_start_pre_00_g.png"]
imgs = {}
for pname in PNGS:
    print(f"\n--- {pname}")
    row = {}
    for t in TAGS:
        p = os.path.join(TRIPS, t, pname)
        if not os.path.exists(p):
            print(f"  {t}: MISSING")
            row[t] = None
            continue
        raw = open(p, "rb").read()
        im = Image.open(p).convert("RGB")
        a = np.asarray(im, dtype=np.int16)
        sha = hashlib.sha256(raw).hexdigest()
        psha = hashlib.sha256(a.tobytes()).hexdigest()
        print(f"  {t}: bytes={len(raw)} sha256={sha} size={im.size} pixel_sha256={psha}")
        row[t] = (raw, a, sha, psha, im.size)
        imgs[(pname, t)] = a
    # pairwise pixel diff
    for x, y in itertools.combinations(TAGS, 2):
        if row[x] is None or row[y] is None:
            continue
        ax, ay = row[x][1], row[y][1]
        if ax.shape != ay.shape:
            print(f"  {x} vs {y}: SHAPE MISMATCH {ax.shape} vs {ay.shape}")
            continue
        diff = np.abs(ax - ay)
        npx = ax.shape[0] * ax.shape[1]
        changed = int(np.count_nonzero(np.any(diff > 0, axis=2)))
        maxd = int(diff.max())
        sumd = int(diff.sum())
        print(f"  {x} vs {y}: equal={np.array_equal(ax, ay)} changed_pixels={changed}/{npx} "
              f"({100.0*changed/npx:.4f}%) max_channel_diff={maxd} sum_abs_diff={sumd} "
              f"raw_sha_equal={row[x][2] == row[y][2]}")

print()
print("=" * 100)
print("SECTION 5: 全库搜索 units0=0 且 verdict=no_advance")
print("=" * 100)
# Walk all measure_w*.json under TRIPS (and check repo-wide other roots too)
hits = []
all_measure = []
for dirpath, dirnames, filenames in os.walk(TRIPS):
    for fn in filenames:
        if re.match(r"measure_w\d+\.json$", fn):
            p = os.path.join(dirpath, fn)
            all_measure.append(p)
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception as ex:
                print("  JSON ERROR", p, ex)
                continue
            u = d.get("gate", {}).get("units0")
            v = d.get("verdict")
            if u == 0 and v == "no_advance":
                hits.append((p, d))
print(f"TRIPS 下 measure_w*.json 总数: {len(all_measure)}")
print(f"units0==0 且 verdict=='no_advance' 命中: {len(hits)}")
for p, d in hits:
    print("  HIT", p)
    print("     trip_id:", d.get("trip_id"), " gate:", d.get("gate"), " span_s:", d.get("span_s"))
    print("     stats.note:", d.get("stats", {}).get("note"), " samples:", d.get("stats", {}).get("samples"))

# repo-wide: other roots with measure_w*.json
print("\n--- 全仓库其它目录下的 measure_w*.json ---")
other_roots = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if ".git" in dirpath or ".mimosa" in dirpath or ".zcode" in dirpath:
        continue
    if dirpath.startswith(TRIPS):
        continue
    for fn in filenames:
        if re.match(r"measure_w\d+\.json$", fn):
            other_roots.append(os.path.join(dirpath, fn))
print("其它目录 measure 文件数:", len(other_roots))
for p in other_roots[:40]:
    try:
        d = json.load(open(p, encoding="utf-8"))
        print(f"  {p}: units0={d.get('gate',{}).get('units0')} verdict={d.get('verdict')}")
    except Exception as ex:
        print("  ERR", p, ex)
# also check no_advance hits in other roots
other_hits = []
for p in other_roots:
    try:
        d = json.load(open(p, encoding="utf-8"))
        if d.get("gate", {}).get("units0") == 0 and d.get("verdict") == "no_advance":
            other_hits.append(p)
    except Exception:
        pass
print("其它目录命中 units0=0/no_advance:", len(other_hits), other_hits[:20])

# For every hit, find except_post file in same dir & look for 007CFC9F
print("\n--- 历史失败趟 except 地址 007CFC9F 普查 ---")
for p, d in hits + [(x, None) for x in other_hits]:
    dd = os.path.dirname(p)
    exfs = sorted(fn for fn in os.listdir(dd) if fn.startswith("except_post_") and fn.endswith(".txt"))
    for fn in exfs:
        raw = open(os.path.join(dd, fn), "rb").read()
        txt = raw.decode("utf-8", errors="replace")
        has = "007CFC9F" in txt.upper()
        addrs = sorted(set(re.findall(r"\b0?[0-9A-Fa-f]{8}\b", txt)))
        print(f"  {dd}/{fn}: 007CFC9F={has} distinct_8hex={len(addrs)} sample={addrs[:12]}")

# Also broader: all except_post files anywhere in repo, count 007CFC9F
print("\n--- 全库 except_post_*.txt 中 007CFC9F 出现统计 ---")
allexc = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if ".git" in dirpath:
        continue
    for fn in filenames:
        if fn.startswith("except_post_") and fn.endswith(".txt"):
            allexc.append(os.path.join(dirpath, fn))
with_addr, without = [], []
for p in allexc:
    txt = open(p, "rb").read().decode("utf-8", errors="replace").upper()
    (with_addr if "007CFC9F" in txt else without).append(p)
print("except_post 总数:", len(allexc), " 含 007CFC9F:", len(with_addr), " 不含:", len(without))
print("含地址样本(前15):")
for p in with_addr[:15]:
    print("  ", p)
print("不含地址样本(前15):")
for p in without[:15]:
    print("  ", p)

print()
print("=" * 100)
print("SECTION 6: _launch_result.json / qc151_run_log / MANIFEST 关键字段（回归排查）")
print("=" * 100)
for aux in ["_launch_result.json", "qc151_run_log.json", "qc151_fields_post.json",
            "carrier_post_state.json", "s4_module_table.txt", "T0_T1_diff.json",
            "carrier_mother_baseline.json"]:
    print(f"\n--- {aux}")
    for t in TAGS:
        p = os.path.join(TRIPS, t, aux)
        if not os.path.exists(p):
            print(f"  {t}: MISSING")
            continue
        raw = open(p, "rb").read()
        print(f"  {t}: bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()}")
        if aux.endswith(".json"):
            d = json.loads(raw.decode("utf-8", errors="replace"))
            s = json.dumps(d, ensure_ascii=False)
            print("     ", s[:700])
        else:
            print("     ", raw.decode("utf-8", errors="replace")[:400].replace("\n", " | "))

print("\nDONE")
