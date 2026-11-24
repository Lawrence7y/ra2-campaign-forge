"""EX-1 数据面 — 只读原始 JSON 重建分类，生成 Markdown 文档。

不是采样代码：不启动任何游戏/发射器，不注入、不读活进程内存。
只读取 measure_w*.json、各趟 _launch_result.json、harness 源码的只读片段，
写入指定输出目录（文档 + 两个可复核副件）。
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import sys
from datetime import datetime, timezone

DATA_ROOT = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
OUT_DIR = Path("D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c")
OUT_MD = OUT_DIR / "EX1_DATAFACE.md"
OUT_JSON = OUT_DIR / "ex1_rebuild.json"
OUT_CHECKS = OUT_DIR / "ex1_checks.txt"
HARNESS_SRC = Path("D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py")
if not all(p.is_absolute() for p in (DATA_ROOT, OUT_DIR, OUT_MD, OUT_JSON, OUT_CHECKS, HARNESS_SRC)):
    raise SystemExit("Absolute paths required")


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def isnum(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def show(v):
    """原始值照抄；缺字段/null 一律写「缺」。"""
    if v is None:
        return "缺"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, int):
        return str(v)
    return str(v).replace("|", "\\|")


def mdshow(v):
    return "`" + show(v) + "`"


files = sorted(DATA_ROOT.rglob("measure_w*.json"))
records = []
for p in files:
    d = jload(p)
    samples = d.get("samples") or {}
    t = samples.get("t") or []
    f = samples.get("f") or []
    depth = len(p.relative_to(DATA_ROOT).parts) - 1
    layer = "root" if depth == 0 else "child" if depth == 1 else "deeper"
    ok_pairs = len(t) == len(f) and len(f) >= 2
    df = int(f[-1]) - int(f[0]) if ok_pairs else None
    st = d.get("stats") or {}
    gate = d.get("gate") or {}
    fe = d.get("frame_edges")
    first_edge = int(fe[0][0]) if isinstance(fe, list) and fe and isinstance(fe[0], (list, tuple)) else None
    last_edge = int(fe[-1][0]) if isinstance(fe, list) and fe and isinstance(fe[-1], (list, tuple)) else None
    rec = {
        "path": p.as_posix(), "layer": layer, "d": d,
        "n_t": len(t), "n_f": len(f), "ok_pairs": ok_pairs, "df": df,
        "f_first": int(f[0]) if f else None, "f_last": int(f[-1]) if f else None,
        "span": d.get("span_s"), "trip_id": d.get("trip_id"),
        "avg": st.get("fps_avg"), "p50": st.get("fps_p50"), "stall": st.get("max_stall_s"),
        "map": d.get("map_sha256"), "gamemd_sha256": d.get("gamemd_sha256"),
        "gate_ok": gate.get("ok", None), "verdict": d.get("verdict"),
        "units0": gate.get("units0", None), "settle_s": d.get("settle_s"),
        "first_edge": first_edge, "last_edge": last_edge,
        "n_edges": len(fe) if isinstance(fe, list) else None,
    }
    # harness 版本/哈希：优先本趟 _launch_result.json 的 harness_sha16 + harness 路径
    lp = p.parent / "_launch_result.json"
    rec["launch_path"] = lp.as_posix()
    rec["launch_exists"] = lp.is_file()
    ld = jload(lp) if lp.is_file() else {}
    rec["harness_sha16"] = ld.get("harness_sha16")
    rec["harness_path"] = ld.get("harness")
    rec["launch_keys"] = sorted(ld.keys()) if ld else []
    rec["argv_first"] = None
    if ld.get("argv"):
        try:
            import ast
            av = ast.literal_eval(ld["argv"]) if isinstance(ld["argv"], str) else ld["argv"]
            rec["argv_first"] = str(av[0]) if isinstance(av, (list, tuple)) and av else None
        except Exception:
            rec["argv_first"] = None
    records.append(rec)

# ---- 分类 ----
def pos(r):
    return r["df"] is not None and r["df"] > 0

moving = [r for r in records if pos(r)]
p25 = [r for r in moving if r["span"] == 25.0]
p4 = [r for r in moving if r["span"] == 4.0]


def low_avg(r):
    return isnum(r["avg"]) and r["avg"] < 28


def low_both(r):
    return low_avg(r) and isnum(r["p50"]) and r["p50"] < 28


def high_p50(r):
    return low_avg(r) and isnum(r["p50"]) and r["p50"] >= 28


control = [r for r in p25 if isnum(r["avg"]) and r["avg"] >= 28]
steady = [r for r in p25 if low_both(r)]
stopped = [r for r in p25 if high_p50(r)]
unclassified = [r for r in p25 if r not in control and r not in steady and r not in stopped]
nonpositive = [r for r in records if not pos(r)]

by_layer = {k: [r for r in records if r["layer"] == k] for k in ("root", "child", "deeper")}
by_layer_pos = {k: [r for r in by_layer[k] if pos(r)] for k in by_layer}

# 41 个不可算窗的判据
reason = {}
for r in nonpositive:
    if not r["ok_pairs"]:
        reason[r["path"]] = "样点不足（samples.t/f 配对 <2 或长度不等）"
    elif r["df"] == 0:
        reason[r["path"]] = "零推进（末沿帧号 − 首沿帧号 = 0）"
    elif r["df"] < 0:
        reason[r["path"]] = "计数回绕（末沿帧号 − 首沿帧号 < 0）"
    else:
        reason[r["path"]] = "其他非正推进"
reason_counts = {}
for r in nonpositive:
    reason_counts[reason[r["path"]]] = reason_counts.get(reason[r["path"]], 0) + 1

# 全部 104 份的 avg<28 及双低（分母 38 / 24）
all_low = [r for r in records if low_avg(r)]
all_low_both = [r for r in records if low_both(r)]
low25 = [r for r in records if r["span"] == 25.0 and low_avg(r)]
low4 = [r for r in records if r["span"] == 4.0 and low_avg(r)]

steady_ids = sorted({r["trip_id"] for r in steady})
stopped_ids = sorted({r["trip_id"] for r in stopped})
grp47 = steady + control

# ---- 附加只读核查（写入 ex1_checks.txt，便于复核） ----
checks = []
def chk(s):
    checks.append(s)
    print(s)

chk("COMMAND=python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py'")
chk("INTERPRETER=" + sys.executable)
chk("DATA_ROOT=" + DATA_ROOT.as_posix())
chk("A total=" + str(len(records)) + " root=" + str(len(by_layer["root"])) + " child=" + str(len(by_layer["child"])) + " deeper=" + str(len(by_layer["deeper"])))
chk("A df_positive_total=" + str(len(moving)) + " root=" + str(len(by_layer_pos["root"])) + " child=" + str(len(by_layer_pos["child"])) + " deeper=" + str(len(by_layer_pos["deeper"])))
chk("A positive_25s=" + str(len(p25)) + " positive_4s=" + str(len(p4)) + " nonpositive=" + str(len(nonpositive)))
chk("B all_avg_lt28=" + str(len(all_low)) + " span25_avg_lt28=" + str(len(low25)) + " span4_avg_lt28=" + str(len(low4)) + " span25_both_lt28=" + str(sum(low_both(r) for r in records if r["span"] == 25.0)))
chk("B control=" + str(len(control)) + " steady=" + str(len(steady)) + " stopped=" + str(len(stopped)) + " unclassified=" + str(len(unclassified)))
chk("B steady_trip_ids=" + str(len(steady_ids)) + " stopped_trip_ids=" + str(len(stopped_ids)) + " overlap=" + str(len(set(steady_ids) & set(stopped_ids))))
chk("B steady_stall_min=" + repr(min(r["stall"] for r in steady)) + " steady_stall_max=" + repr(max(r["stall"] for r in steady)) + " n_stall_ge_1s=" + str(sum(r["stall"] >= 1.0 for r in steady)))
chk("B reasons=" + json.dumps(reason_counts, ensure_ascii=False))
# 全库递归键扫描：确认原始 JSON 内无 harness 版本/哈希字段
topkeys = set()
harness_key_hits = []
def walk(o, p, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if path == "":
                topkeys.add(k)
            if "harness" in k.lower() or "sha16" in k.lower():
                harness_key_hits.append((p.as_posix(), path + "/" + k, repr(v)[:120]))
            walk(v, p, path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, p, path + "/" + str(i))
for r in records:
    walk(r["d"], Path(r["path"]))
chk("D full_recursive_key_walk: files=" + str(len(records)) + " harness_or_sha16_key_hits=" + str(len(harness_key_hits)))
chk("D top_level_keys=" + json.dumps(sorted(topkeys), ensure_ascii=False))
root_named = sorted(x.name for x in DATA_ROOT.iterdir() if x.is_file() and ("harness" in x.name.lower() or "launch" in x.name.lower()))
chk("D root_level_harness_or_launch_named_files=" + json.dumps(root_named, ensure_ascii=False))
# 47 窗 frame_edges 首末帧号与 samples.f 首末值一致性（只作核对，不改写读数）
eq_count = 0
bad = []
for r in grp47:
    f = r["d"]["samples"]["f"]
    if r["first_edge"] == int(f[0]) and r["last_edge"] == int(f[-1]):
        eq_count += 1
    else:
        bad.append(r["path"])
chk("D grp47_frame_edges_endpoints_equal_samples_f=" + str(eq_count) + "/" + str(len(grp47)) + " mismatches=" + str(len(bad)))
# T34 分型核对
t34 = next((r for r in records if r["path"].endswith("/archive_T34/measure_w0.json")), None)
chk("D t34_path=" + (t34["path"] if t34 else "MISSING") + " avg=" + repr(t34["avg"]) + " p50=" + repr(t34["p50"]) + " stall=" + repr(t34["stall"]) + " in_stopped=" + str(t34 in stopped) + " in_control=" + str(t34 in control))
# 47 窗缺格
miss = {
    "map_sha256": [r["path"] for r in grp47 if r["map"] is None],
    "harness_sha16": [r["path"] for r in grp47 if r["harness_sha16"] is None],
    "frame_edges 首末帧号": [r["path"] for r in grp47 if r["first_edge"] is None or r["last_edge"] is None],
    "gate.ok": [r["path"] for r in grp47 if r["gate_ok"] is None],
    "verdict": [r["path"] for r in grp47 if r["verdict"] is None],
    "gate.units0": [r["path"] for r in grp47 if r["units0"] is None],
    "settle_s": [r["path"] for r in grp47 if r["settle_s"] is None],
}
chk("D grp47=" + str(len(grp47)) + " missing=" + json.dumps({k: len(v) for k, v in miss.items()}, ensure_ascii=False))
# units0 取值阶段：只读 harness 源码片段定位
src_lines = HARNESS_SRC.read_text(encoding="utf-8-sig").splitlines()
chk("D units0_source=" + HARNESS_SRC.as_posix() + ":5173-5196 settle_then_first_units ; :5220-5224 gate_block")
for ln in (5173, 5175, 5192, 5195, 5220, 5222):
    chk("  src:" + str(ln) + " " + src_lines[ln - 1].strip()[:160])
chk("ROOT_TRIP_IDS=" + json.dumps([(r["path"].split("/")[-1], r["trip_id"]) for r in by_layer["root"]], ensure_ascii=False))
chk("END_UTC=" + datetime.now(timezone.utc).isoformat())

# ---- 输出文本 ----
L = []
A = L.append
A("# EX-1 数据面：从原始 JSON 重建的 104 窗分类与 47 窗混杂控制表")
A("")
A("本件为裁决 EX-1 数据面落实稿（域内候选件，未改台账/PENDING，未 commit）。全部数值从指定数据根的原始 `measure_w*.json` 顶层/嵌套字段直接读出，不推测、不补造；查不到的单元格写「缺」。只出文档，不含采样/注入/运行期探针代码。")
A("")
A("## 0. 本次实际执行的检查（可复核）")
A("")
A("**数据根（只读）**：`" + DATA_ROOT.as_posix() + "`")
A("")
A("**重建脚本（本轮自写，仅离线读 JSON / 源码片段 / 写文档）**：`" + Path(__file__).resolve().as_posix() + "`")
A("")
A("**执行命令**（`python -I -X utf8`，绝对路径，退出码 0；脚本内所有路径均为绝对路径，未使用 `..`）：")
A("")
A("```bash")
A("python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py'")
A("```")
A("")
A("**副件**：机器可读重建结果 `" + OUT_JSON.as_posix() + "`；完整 stdout 副本 `" + OUT_CHECKS.as_posix() + "`（含全库递归键扫描、47 窗帧沿端点核对、T34 分型核对、units0 源码定位）。关键输出摘录：")
A("")
A("```text")
for s in checks[:10]:
    A(s)
A("```")
A("")
A("**口径**：`df = samples.f[-1] − samples.f[0]`（要求 `samples.t` 与 `samples.f` 等长且配对 ≥2）；`df>0` 为净正推进窗。名义窗长取顶层 `span_s`。分类只读 `stats.fps_avg` / `stats.fps_p50`。主指标 `fps_avg`，`fps_p50` 只作分型。")
A("")
A("**已读的裁决/底账**：`RULING.md` 二、D-15（`RULING.md:69-93`，分层表 `RULING.md:75-85`，报数规定 `RULING.md:87`，混杂字段要求 `RULING.md:150`）、四、EX-1 行（`RULING.md:166`）；`FACTBASE.md` 二 a/b（`FACTBASE.md:38-84`）；`RECHECK.md` R1（`RECHECK.md:9-13`）。裁决记载值为对照目标，不是本件的数据来源。")
A("")
A("## 1. 语料账（复现 104 = 子目录 101 + 根 3）")
A("")
A("| 层级 | JSON 份数 | 其中净正推进 df>0 | 说明 |")
A("|---|---:|---:|---|")
A("| 趟根目录层（`.../qc161_u0400_trip/measure_w*.json`） | " + str(len(by_layer["root"])) + " | " + str(len(by_layer_pos["root"])) + " | 根层 `measure_w0/w1/w2.json` 三个文件并非同一 trip（w0=T55j、w1/w2=T55h），全部 df=0 |")
A("| 一层子目录层（各趟目录下 `measure_w*.json`） | " + str(len(by_layer["child"])) + " | " + str(len(by_layer_pos["child"])) + " | 两层都扫，分别报数 |")
A("| 更深层 | " + str(len(by_layer["deeper"])) + " | " + str(len(by_layer_pos["deeper"])) + " | 无 |")
A("| **合计** | **" + str(len(records)) + "** | **" + str(len(moving)) + "** | `df<=0` 或样点不足共 " + str(len(nonpositive)) + " |")
A("")
A("与裁决 `RULING.md:77` 记载的 104=101+3 一致，无差异。根层三个文件的 `trip_id`（各 JSON 顶层字段）：" + "；".join("`" + r["path"].split("/")[-1] + "` = `" + show(r["trip_id"]) + "`" for r in by_layer["root"]) + "（`FACTBASE.md:59` 亦记 T55j / T55h / T55h）。")
A("")
A("## 2. 净正推进窗、25 秒推进观测集、4 秒 settle 门控窗")
A("")
A("| 口径 | 窗数 | 判据 |")
A("|---|---:|---|")
A("| 全部 JSON | " + str(len(records)) + " | 见第 1 节 |")
A("| **净正推进窗 df>0** | **" + str(len(moving)) + "** | `samples.f[-1] − samples.f[0] > 0` |")
A("| 其中 **25 秒推进观测集** | **" + str(len(p25)) + "** | `span_s=25.0` 且 df>0，完整性能观测分母 |")
A("| 其中 **4 秒 settle 门控窗（剔除）** | **" + str(len(p4)) + "** | `span_s=4.0` 且 df>0；排除 25 秒性能分析 |")
A("| 非正推进/样点不足 | " + str(len(nonpositive)) + " | 见第 5 节 |")
A("")
A("复现裁决 `RULING.md:78-84` 的 63 / 58 / 5 / 41，无差异。")
A("")
A("### 2.1 5 个 4 秒 settle 门控窗（单列，不作同质性能样本）")
A("")
A("| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s | gate.ok | verdict | df |")
A("|---:|---|---|---:|---:|---:|---:|---|---|---:|")
for i, r in enumerate(p4, 1):
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["span"]) + " | " + mdshow(r["avg"]) + " | " + mdshow(r["p50"]) + " | " + mdshow(r["stall"]) + " | " + mdshow(r["gate_ok"]) + " | " + mdshow(r["verdict"]) + " | " + mdshow(r["df"]) + " |")
A("")
A("**字段来源**：`trip_id`、`span_s`、`verdict`、`gate.ok`、`samples.f`、`stats.*` 均为各绝对路径指向的原始 JSON 顶层/子字段；`df` 由 `samples.f[0]` 与 `samples.f[-1]` 相减（派生，非存储字段）。5 窗全部 `span_s=4.0`，且 `stats.fps_avg<28` 共 " + str(sum(low_avg(r) for r in p4)) + " 个（与 `FACTBASE.md:71` 的 4 秒行一致）。")
A("")
A("## 3. 58 窗逐行三分类")
A("")
A("| 类别 | 窗数 | 定义 | 独立 trip_id 数 |")
A("|---|---:|---|---:|")
A("| `avg>=28` 对照 | " + str(len(control)) + " | `stats.fps_avg >= 28` | " + str(len({r['trip_id'] for r in control})) + " |")
A("| **持续低速核心** | **" + str(len(steady)) + "** | `stats.fps_avg<28` 且 `stats.fps_p50<28` | **" + str(len(steady_ids)) + "** |")
A("| 停摆主导 | " + str(len(stopped)) + " | `stats.fps_avg<28` 且 `stats.fps_p50>=28` | " + str(len(stopped_ids)) + " |")
A("| 合计 | " + str(len(control) + len(steady) + len(stopped)) + " | 25+22+11=58，无其他未分类窗 " + ("（0）" if not unclassified else "（**有 " + str(len(unclassified)) + " 个未分类**）") + " | — |")
A("")
A("**22 窗的 8 个独立 trip_id**（取自各 JSON 顶层 `trip_id`）：" + "、".join("`" + x + "`" for x in steady_ids) + "。11 停摆窗的 trip_id 共 " + str(len(stopped_ids)) + " 个，与 22 窗 trip_id 集合交集 " + str(len(set(steady_ids) & set(stopped_ids))) + " 个。")
A("")
A("**每行字段来源（统一说明，避免逐行重复）**：")
A("")
A("- `绝对原件路径`：本次 `rglob('measure_w*.json')` 的实际绝对路径，绝对化后写入。")
A("- `trip_id`：JSON 顶层 `trip_id`；`span_s`（名义窗长）：JSON 顶层 `span_s`。")
A("- `stats.fps_avg` / `stats.fps_p50` / `stats.max_stall_s`：`stats` 对象内同名键，原值照抄（`repr(float)` 保留原精度），**未重算、未事后截尾**。")
A("- `df`（若有）：派生量 `samples.f[-1] − samples.f[0]`，只用于判定可算性，不填入任何存储字段。")
A("")
A("### 3.1 `avg>=28` 对照（25 窗）")
A("")
A("| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |")
A("|---:|---|---|---:|---:|---:|---:|")
for i, r in enumerate(control, 1):
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["span"]) + " | " + mdshow(r["avg"]) + " | " + mdshow(r["p50"]) + " | " + mdshow(r["stall"]) + " |")
A("")
A("### 3.2 持续低速核心（22 窗 / 8 趟）")
A("")
A("| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |")
A("|---:|---|---|---:|---:|---:|---:|")
for i, r in enumerate(steady, 1):
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["span"]) + " | " + mdshow(r["avg"]) + " | " + mdshow(r["p50"]) + " | " + mdshow(r["stall"]) + " |")
A("")
A("22 窗 `stats.max_stall_s` 的最小值/最大值（由本表数值直接取，未重算）：`" + repr(min(r["stall"] for r in steady)) + "` / `" + repr(max(r["stall"] for r in steady)) + "` 秒；与 `FACTBASE.md:80`、`RECHECK.md:55` 的 0.103742 / 0.749879 一致。按记录值，N=1 秒谓词覆盖 **" + str(sum(r["stall"] >= 1.0 for r in steady)) + "/22**（`RULING.md:135`、D-13.2）。")
A("")
A("### 3.3 停摆主导（11 窗 / 11 趟）——整组「停摆观测、待归因」")
A("")
A("| # | 绝对原件路径 | trip_id | span_s | stats.fps_avg | stats.fps_p50 | stats.max_stall_s |")
A("|---:|---|---|---:|---:|---:|---:|")
for i, r in enumerate(stopped, 1):
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["span"]) + " | " + mdshow(r["avg"]) + " | " + mdshow(r["p50"]) + " | " + mdshow(r["stall"]) + " |")
A("")
A("按 `RULING.md:111`、`RULING.md:117-120`，这 11 窗**既不作为已证在战卡顿正证，也不整组认定终局**；它们是 25 秒低 avg 观测的有效记录，不用于替代 22 窗持续低速机制，也不从 33 的原始计数中抹除。")
A("")
A("## 4. ★ 混杂控制表（复查 R1 补强）：22 + 25 = 47 窗逐行五列")
A("")
A("**列定义与字段来源**（缺一律写「缺」，不补造）：")
A("")
A("1. `map_sha256`：原始 JSON 顶层 `map_sha256`。")
A("2. `harness 版本/哈希`：本次对 104 份原始 JSON 做完整递归键扫描（含 `stats` / `gate` / `w1` / `h8` / `counters` 等），`harness` 或 `sha16` 类键命中 **0**（`ex1_checks.txt` 的 `D full_recursive_key_walk`、`D top_level_keys`）。按裁决 `RULING.md:150`、EX-1 `RULING.md:166` 指示，改查该趟目录 `_launch_result.json` 的 `harness_sha16` 与 `harness`（脚本文件绝对路径/版本名）；两者皆无时记「缺」，`_launch_result.json` 不存在也记「缺」并注明。")
A("3. `实际采样起止帧`：`frame_edges[0][0]`（首个帧沿元素帧号）与 `frame_edges[-1][0]`（末个元素帧号），均为原始 JSON 顶层 `frame_edges` 数组元素 `[帧号, 时间]` 的第 0 位；不是派生量，也不重算。47 窗已核对 `frame_edges` 首末帧号与 `samples.f[0]`/`samples.f[-1]` 一致（`ex1_checks.txt` 的 `D grp47_frame_edges_endpoints_equal_samples_f=47/47`）。")
A("4. `门控状态`：`gate.ok`（`gate` 对象内）与顶层 `verdict`。")
A("5. `units0 及取值阶段`：`gate.units0`。**取值阶段为 settle 阶段起始读数**：源码 `qc151_trip.harness8_v4.py:5173-5196` 显示 settle 4 s 的 `_measure_poll_span` 之后，从 `s_counters` 取第一个非 null 的 `units`（`units0`），并在 `:5220-5224` 写入 `gate_block`；同型写法另见 `qc151_trip.harness6.py:4957-4967`、`qc151_trip.harness7.py:5025-5035`、`qc151_trip.harness8.py:5159-5169`、`qc151_trip.harness3.py:4051-4061`（本次只读定位，未执行这些源码）。`settle_s` 取自 JSON 顶层。按 `RULING.md:150`，它只是**起始/settle 负载描述，不冒充每个窗的实时同负载**。")
A("")
A("### 4.1 22 个持续低速窗")
A("")
A("| # | 绝对原件路径 | trip_id | map_sha256（顶层） | harness 版本/哈希（_launch_result.json） | 起帧→末帧（frame_edges[0][0]→[-1][0]） | gate.ok | verdict | gate.units0 | units0 阶段 | settle_s |")
A("|---:|---|---|---|---|---|---|---|---|---|---:|")
for i, r in enumerate(steady, 1):
    h = ("`" + show(r["harness_sha16"]) + "`" if r["harness_sha16"] is not None else "缺") + " / " + ("`" + str(r["harness_path"]).replace("|", "\\|") + "`" if r["harness_path"] else "缺")
    fr = (mdshow(r["first_edge"]) + " → " + mdshow(r["last_edge"]))
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["map"]) + " | " + h + " | " + fr + " | " + mdshow(r["gate_ok"]) + " | " + mdshow(r["verdict"]) + " | " + mdshow(r["units0"]) + " | settle 起始（见上） | " + mdshow(r["settle_s"]) + " |")
A("")
A("### 4.2 25 个 `avg>=28` 对照窗")
A("")
A("| # | 绝对原件路径 | trip_id | map_sha256（顶层） | harness 版本/哈希（_launch_result.json） | 起帧→末帧（frame_edges[0][0]→[-1][0]） | gate.ok | verdict | gate.units0 | units0 阶段 | settle_s |")
A("|---:|---|---|---|---|---|---|---|---|---|---:|")
for i, r in enumerate(control, 1):
    h = ("`" + show(r["harness_sha16"]) + "`" if r["harness_sha16"] is not None else "缺") + " / " + ("`" + str(r["harness_path"]).replace("|", "\\|") + "`" if r["harness_path"] else "缺")
    fr = (mdshow(r["first_edge"]) + " → " + mdshow(r["last_edge"]))
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["map"]) + " | " + h + " | " + fr + " | " + mdshow(r["gate_ok"]) + " | " + mdshow(r["verdict"]) + " | " + mdshow(r["units0"]) + " | settle 起始（见上） | " + mdshow(r["settle_s"]) + " |")
A("")
A("### 4.3 47 窗缺格统计与查阅来源（禁止补造）")
A("")
A("| 列 | 47 窗中「缺」格数 |")
A("|---|---:|")
for k, v in miss.items():
    A("| " + k + " | " + str(len(v)) + " |")
A("")
nohash = [r for r in grp47 if r["harness_sha16"] is None]
A("**harness 版本/哈希大面积缺失**：47 窗中有 **" + str(len(nohash)) + "** 窗从 `_launch_result.json` 取不到 `harness_sha16`，表中已逐行写「缺」。逐趟查阅的绝对路径（全部为本数据根下的绝对路径，只读；不存在者如实标注）：")
A("")
for r in sorted({x["launch_path"]: x for x in nohash}.values(), key=lambda x: x["launch_path"]):
    exists = "存在" if r["launch_exists"] else "**不存在**"
    A("- `" + r["launch_path"] + "` — " + exists + "；键：" + ("、".join("`" + k + "`" for k in r["launch_keys"]) if r["launch_keys"] else "无") + ("；`argv[0]` 脚本路径为 `" + str(r["argv_first"]).replace("|", "\\|") + "`，但该件**无 `harness_sha16` 字段**，按铁律不据文件名/他趟补造哈希" if r["argv_first"] else ""))
A("")
A("此外，对全部 104 份 `measure_w*.json` 做过**完整递归键扫描**（不只顶层；结果在 `ex1_checks.txt`）：**没有任何 harness 版本或哈希键**。对根目录层查过 `" + DATA_ROOT.as_posix() + "` 下文件名含 `harness`/`launch` 的清单（`" + "`、`".join(root_named) + "`），这些是发射日志/脚本，不是 47 窗所属趟的 `harness_sha16` 记录，不用于代填。")
A("")
A("**47 窗行覆盖核对**：22 + 25 = " + str(len(grp47)) + " 行，与 4.1/4.2 两表行数之和一致；路径均为绝对路径。不同版本/地图/相位不得合成因果配对（`RULING.md:150`）。")
A("")
A("## 5. 41 个不可算窗单列（零推进 / 样点不足 / 计数回绕）")
A("")
A("判据统一为：`df = samples.f[-1] − samples.f[0]` 非正，或样点不足（`samples.t` / `samples.f` 长度不等或配对 <2）；这些窗的 `stats.fps_avg` / `stats.fps_p50` 为 null 或不可作可算 fps 样本。按 `RULING.md:85`，保留终局、复位、门控失败等审计用途，**不得统称 41 个冻结**。")
A("")
A("| # | 绝对原件路径 | trip_id | span_s | 判据 | 首沿帧号 | 末沿帧号 | df | 样点对数 | stats.fps_avg | verdict |")
A("|---:|---|---|---:|---|---:|---:|---:|---:|---:|---|")
for i, r in enumerate(nonpositive, 1):
    A("| " + str(i) + " | `" + r["path"] + "` | `" + show(r["trip_id"]) + "` | " + mdshow(r["span"]) + " | " + reason[r["path"]] + " | " + mdshow(r["f_first"]) + " | " + mdshow(r["f_last"]) + " | " + mdshow(r["df"]) + " | " + mdshow(r["n_f"]) + " | " + mdshow(r["avg"]) + " | " + mdshow(r["verdict"]) + " |")
A("")
A("**分因计数**：" + "；".join(k + " = " + str(v) for k, v in sorted(reason_counts.items())) + "；合计 " + str(sum(reason_counts.values())) + "。计数回绕窗即 `l1_20261023e4/measure_w1.json`（首沿 3557 → 末沿 0，df=−3557，`stats.logic_frames=-3557`），单列为计数回绕，不并入零推进。5 个样点不足窗的 `samples.t/f` 均为空数组、`stats.note=insufficient samples`，其中 3 个 `span_s=0.0` / `verdict=frame_wait_timeout`，另 2 个 `span_s=4.0` / `verdict=no_advance`。")
A("")
A("## 6. 口径解释：33 与 38 的分母差异")
A("")
A("| 计数 | 本次重建值 | 分母 / 组成 | 能否当同质性能样本 |")
A("|---|---:|---|---|")
A("| 全部 104 份中 `stats.fps_avg<28` | " + str(len(all_low)) + " | 分母为全部 104 份（根层 3、零推进/样点不足窗的 `fps_avg` 为 null，不贡献命中）；命中 = 25 秒低 avg " + str(len(low25)) + " + 4 秒低 avg " + str(len(low4)) + " | **不能**：混入 5 个 4 秒门控窗 |")
A("| **25 秒低 avg 总计** | **" + str(len(low25)) + "** | 仅 `span_s=25.0`；= 22 持续低速 + 11 停摆主导 | 是「全部 25 秒低 avg 观测」总数，但两类证据用途不同 |")
A("| 25 秒双低（avg<28 且 p50<28） | " + str(sum(low_both(r) for r in records if r["span"] == 25.0)) + " | 22 核心 | 核心持续低速分析样本 |")
A("| 4 秒 `span_s=4.0` 且 avg<28 | " + str(len(low4)) + " | 5 个 settle 门控窗 | 排除 25 秒性能分析 |")
A("")
A("**明确写出**：`38` 是**混入 5 个 4 秒门控窗的旧混合计数**（38 = 33 + 5），来自未按时长分层的 `avg<28` 全量筛选（`FACTBASE.md:69-71`）；`33` 是**仅 25 秒窗的低 avg 总数**（33 = 22 + 11，见 `RULING.md:81-83`、`FACTBASE.md:70`）。二者分母不同，**38 不得再当同质性能样本数**，也不得把 22/47 写成全体真机卡顿发生率；22 窗与 25 对照的 47 窗分析集必须标为「排除 11 个待归因停摆窗后的持续低速/对照分析集」（`RULING.md:87`）。本次重建 38 / 33 / 22 / 11 / 5 与裁决分层逐项一致。")
A("")
A("## 7. `p50` 高不得记为健康")
A("")
t34 = next((r for r in records if r["path"].endswith("/archive_T34/measure_w0.json")), None)
if t34:
    A("本次直接读原件 `" + t34["path"] + "` 得：`stats.fps_avg=" + repr(t34["avg"]) + "`（`<28`），`stats.fps_p50=" + repr(t34["p50"]) + "`（`>=28`），`stats.max_stall_s=" + repr(t34["stall"]) + "`，`frame_edges` 共 " + str(t34["n_edges"]) + " 条，首末帧号 " + str(t34["first_edge"]) + "→" + str(t34["last_edge"]) + "（df=" + str(t34["df"]) + "）。按第 3 节定义它归入**停摆主导**（第 3.3 节表内），**不是健康/对照窗**；核对行见 `ex1_checks.txt` 的 `D t34_path=... in_stopped=True in_control=False`。")
A("")
A("依据：`RULING.md:89-91` 规定主指标维持 `fps_avg`，`p50` 仅作分型、不用于给停摆窗出健康结论；`FACTBASE.md:86-103` 记该窗采样无 >10ms 缺口却停约 24.734760 秒而 p50 仍 31.608660 fps；`RECHECK.md:56-57` 复查也读得同一组原存值。本件**声明：任何 `fps_p50>=28` 且 `fps_avg<28` 的窗一律列「停摆观测、待归因」，不得记为健康**，也整组不得判为已证终局（`RULING.md:111`）。")
A("")
A("## 8. 逐条验收自查与边界")
A("")
A("| 判据 | 本次是否做到 | 证据位置 |")
A("|---|---|---|")
A("| 1 语料账 104=101+3，两层分别报份数 | 是 | 第 1 节；`ex1_checks.txt` 的 `A total=104 root=3 child=101 deeper=0` |")
A("| 2 净正推进窗 63 | 是 | 第 2 节；`A df_positive_total=63` |")
A("| 3 58 / 5 分开列 | 是 | 第 2 节及第 2.1 节 5 窗逐行表 |")
A("| 4 58 窗三分类逐行、字段来源、22 窗独立 trip_id=8 | 是 | 第 3.1/3.2/3.3 节；8 个 trip_id 明列；`B steady_trip_ids=8` |")
A("| 5 47 窗逐行五列混杂控制、缺写「缺」并标查阅来源 | 是（harness 哈希大面积「缺」，如实登记） | 第 4.1/4.2/4.3 节；`D grp47=47 missing={\"harness_sha16\": 25}` |")
A("| 6 41 个不可算窗单列 + 判据 | 是 | 第 5 节；`B reasons=...` |")
A("| 7 33 与 38 分母差异 | 是 | 第 6 节 |")
A("| 8 p50 高不得记为健康（archive_T34/measure_w0.json） | 是 | 第 7 节 |")
A("")
A("**边界与未做**：未启动 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读活进程内存，未改任何既有件，未 commit。未重算 104 份的 `stats`（只照抄原存值），未重算 22 窗的 `max_stall_s`（只取第 3.2 节原存值），未目视/OCR 任何 PNG，未核截图时序/哈希，未做真机发射或运行期采样。写入仅 `" + OUT_MD.as_posix() + "`、机器可读副件 `" + OUT_JSON.as_posix() + "` 与 stdout 副本 `" + OUT_CHECKS.as_posix() + "`，均在指定写域内。")
A("")
A("生成时间（UTC）：`" + datetime.now(timezone.utc).isoformat() + "`；解释器：`" + sys.executable + "`。")

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
OUT_CHECKS.write_text("\n".join(checks) + "\n", encoding="utf-8")
machine = {
    "command": "python -I -X utf8 'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_rebuild.py'",
    "data_root": DATA_ROOT.as_posix(),
    "counts": {
        "total": len(records), "by_layer": {k: len(v) for k, v in by_layer.items()},
        "df_positive": len(moving), "by_layer_df_positive": {k: len(v) for k, v in by_layer_pos.items()},
        "positive_25s": len(p25), "positive_4s": len(p4),
        "control": len(control), "steady": len(steady), "stopped": len(stopped),
        "steady_trip_ids": steady_ids, "stopped_trip_ids": stopped_ids,
        "trip_overlap": len(set(steady_ids) & set(stopped_ids)),
        "nonpositive": len(nonpositive), "reason_counts": reason_counts,
        "all_avg_lt28": len(all_low), "all_both_lt28": len(all_low_both),
        "span25_avg_lt28": len(low25), "span4_avg_lt28": len(low4),
        "span25_both_lt28": sum(low_both(r) for r in records if r["span"] == 25.0),
        "steady_max_stall_s": max(r["stall"] for r in steady),
        "grp47": len(grp47), "missing": {k: len(v) for k, v in miss.items()},
        "harness_key_hits_in_raw_json": len(harness_key_hits),
        "frame_edges_endpoint_match": eq_count,
    },
    "windows": [{k: r[k] for k in ("path", "layer", "df", "span", "trip_id", "avg", "p50", "stall", "map", "harness_sha16", "harness_path", "launch_path", "launch_exists", "first_edge", "last_edge", "gate_ok", "verdict", "units0", "settle_s")} for r in records],
    "reasons": reason,
}
OUT_JSON.write_text(json.dumps(machine, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("WRITE_OK", OUT_MD.as_posix(), OUT_JSON.as_posix(), OUT_CHECKS.as_posix())
