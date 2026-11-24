# EX-4｜D-13 离线机制缺口与对照线索卡（2026-11-04）

**本件身份**：裁决 EX-4 落实稿（域内候选件）。只出文档，不写采样代码，不启动/读取活进程，不改台账、不改 PENDING、不 commit。
对应 `RULING.md:169`（EX-4 行）、`RULING.md:124-158`（三、D-13 全文）、`RECHECK.md:25-30`（复查第 5/6 项：暂停选择成立、当前未越权）。

**一句话状态**：**当前 E3 不执行**；22 个 25 秒持续低速窗/8 趟的现象成立，**机制未闭合**。本卡只登记未知，不把未知填成闭合答案。

---

## 0. 本件执行边界与本次实际执行的检查

### 0.1 边界自证

- **零真机**：本轮未启动 `gamemd.exe` / `ra2loader.exe` / YURI，未 taskkill，未读取任何运行中进程内存（`RULING.md:9, 169`）。
- **零改动既有件**：`gamemd.exe`、真机 json/png、三路核验件、`RULING.md`、`FACTBASE.md`、`RECHECK.md`、台账 `GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md` 全部只读；本件是**新建文件**，未覆写任何既有件（`RULING.md:9, 170`）。
- **只出文档，不写采样代码**：本件是纯 Markdown。**本 EX-4 任务未落盘任何 `.py` 文件**，未产生运行期探针/注入/采样/候选实现代码。本轮唯一的 Python 是下面两条 `python -I -X utf8 -c '...'` **内联只读 JSON 字段核对命令**（不写文件、不导入 harness、不导入任何核验脚本），用途只是复核阈值覆盖与字段身份；它们不是采样代码，也不构成 E3 候选实现（`RULING.md:128, 169, 172`）。写域同目录 `impl_f4bcf30c/ex1_rebuild.py` 的 mtime 为 **2026-11-04 21:17**，是**先于本任务已存在**的 EX-1 离线重建脚本（本轮 `ls -la` 核对：`impl_f4bcf30c/` 仅 `EX1_DATAFACE.md`、`ex1_checks.txt`、`ex1_rebuild.json`、`ex1_rebuild.py` 四件且 mtime 均为 21:17），**不是本 EX-4 产物、本轮未读取或运行它**；EX-1 本身亦声明「只出文档，不含采样/注入/运行期探针代码」（`X1:3`）。
- **写域**：本件写在裁决指定的 EX-4 绝对路径（`RULING.md:169`）；**本任务唯一写入的文件就是本件**，未向 `impl_f4bcf30c/` 或其他目录写入任何内容。所有路径均为绝对路径，未用 `..`。

### 0.2 本次实际执行的检查（可复核）

**检查 A｜0/22 阈值覆盖 + v4c 字段身份**（本轮执行，退出码 0）：

```bash
python -I -X utf8 -c '
import json
from pathlib import Path
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
low = []
for p in sorted(root.rglob("measure_w*.json")):
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    s = d.get("stats") or {}
    sp = d.get("span_s")
    f = (d.get("samples") or {}).get("f") or []
    df = (f[-1] - f[0]) if len(f) >= 2 else 0
    a, p50 = s.get("fps_avg"), s.get("fps_p50")
    if sp == 25.0 and df > 0 and a is not None and p50 is not None and a < 28 and p50 < 28:
        low.append((p.as_posix(), d.get("trip_id"), a, p50, s.get("max_stall_s")))
stalls = [x[4] for x in low if x[4] is not None]
print("low_both_25s windows =", len(low), "trips =", len({x[1] for x in low}))
print("max_stall_s min =", min(stalls), "max =", max(stalls))
print("windows with max_stall_s >= 1.0 =", sum(1 for v in stalls if v >= 1.0), "/", len(stalls))
print("--- v4c field identity ---")
v4c = root / "l3_1101v4c"
for w in range(3):
    p = v4c / ("measure_w%d.json" % w)
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    edges = d["frame_edges"]
    live = (edges[-1][0] - edges[0][0]) / (edges[-1][1] - edges[0][1])
    s = d["stats"]
    print(json.dumps({"path": p.as_posix(), "stored_fps_avg": s["fps_avg"], "derived_live_fps": live, "has_stored_live_fps": ("live_fps" in d or "live_fps" in s)}, ensure_ascii=False))
'
```

实际 stdout：

```text
low_both_25s windows = 22 trips = 8
max_stall_s min = 0.103742 max = 0.749879
windows with max_stall_s >= 1.0 = 0 / 22
--- v4c field identity ---
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w0.json", "stored_fps_avg": 18.520948494813613, "derived_live_fps": 18.539626790502314, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w1.json", "stored_fps_avg": 28.40179635682234, "derived_live_fps": 28.416096013424877, "has_stored_live_fps": false}
{"path": "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4c/measure_w2.json", "stored_fps_avg": 30.681571141892938, "derived_live_fps": 30.70530239738328, "has_stored_live_fps": false}
```

**检查 B｜v4c 三窗身份字段 + 104 份 JSON 全键扫描**（本轮执行，退出码 0）：完整实际命令：

```bash
python -I -X utf8 -c '
import json
from pathlib import Path
root = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
print("--- v4c three windows: identity + phase fields ---")
v4c = root / "l3_1101v4c"
for w in range(3):
    p = v4c / ("measure_w%d.json" % w)
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    e = d["frame_edges"]
    print(json.dumps({"file": p.name, "trip_id": d.get("trip_id"), "span_s": d.get("span_s"), "settle_s": d.get("settle_s"), "map_sha256": d.get("map_sha256"), "gamemd_sha256": d.get("gamemd_sha256"), "gate.ok": (d.get("gate") or {}).get("ok"), "gate.units0": (d.get("gate") or {}).get("units0"), "verdict": d.get("verdict"), "frame_first": e[0][0], "frame_last": e[-1][0], "fps_avg": d["stats"]["fps_avg"]}, ensure_ascii=False))
lr = v4c / "_launch_result.json"
print("launch_result_exists =", lr.exists())
if lr.exists():
    L = json.loads(lr.read_text(encoding="utf-8-sig"))
    print(json.dumps({"launch_keys": sorted(L.keys()), "harness_sha16": L.get("harness_sha16"), "argv0": (L.get("argv") or [None])[0]}, ensure_ascii=False))
print("--- runtime stack / function keys across all 104 JSON ---")
keys = set()
n = 0
for p in sorted(root.rglob("measure_w*.json")):
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    n += 1
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            for k, v in o.items():
                keys.add(k)
                if isinstance(v, (dict, list)): stack.append(v)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, (dict, list)): stack.append(v)
hits = sorted(k for k in keys if any(t in k.lower() for t in ("stack", "frame_walk", "call", "func", "symbol", "dmp", "dump", "thread", "profile", "hotspot", "hot_spot", "stage", "phase")))
print("files_walked =", n, "all_key_count =", len(keys), "runtime_attribution_like_keys =", hits)
'
```

实际 stdout：

```text
--- v4c three windows: identity + phase fields ---
{"file": "measure_w0.json", "trip_id": "QC161-U0800-L3-V4-20261101C", "span_s": 25.0, "settle_s": 4.0, "map_sha256": "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36", "gamemd_sha256": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", "gate.ok": true, "gate.units0": 1229, "verdict": "ok", "frame_first": 869, "frame_last": 1332, "fps_avg": 18.520948494813613}
{"file": "measure_w1.json", "trip_id": "QC161-U0800-L3-V4-20261101C", "span_s": 25.0, "settle_s": 0.0, "map_sha256": "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36", "gamemd_sha256": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", "gate.ok": true, "gate.units0": 1229, "verdict": "ok", "frame_first": 1333, "frame_last": 2043, "fps_avg": 28.40179635682234}
{"file": "measure_w2.json", "trip_id": "QC161-U0800-L3-V4-20261101C", "span_s": 25.0, "settle_s": 0.0, "map_sha256": "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36", "gamemd_sha256": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", "gate.ok": true, "gate.units0": 1229, "verdict": "ok", "frame_first": 2044, "frame_last": 2811, "fps_avg": 30.681571141892938}
launch_result_exists = True
{"launch_keys": ["argv", "carriers_deleted", "duration_s", "harness", "harness_sha16", "leftover_procs", "out_dir", "rc", "trip_id"], "harness_sha16": "38244d2907e7f7fa", "argv0": "D:\\Project\\ra2-campaign-forge\\lead\\goal1_harness8_20261031\\qc151_trip.harness8_v4.py"}
--- runtime stack / function keys across all 104 JSON ---
files_walked = 104 all_key_count = 63 runtime_attribution_like_keys = []
```

**本轮未运行 / 未验证**（如实登记，不冒充通过）：1734 段分布与 `87.7%` 未重算（`FACTBASE.md:129`、`RECHECK.md:82`）；21/32 计分屏未独立读图（`RULING.md:197`）；全库派生 `live_fps` 未重算（`FACTBASE.md:84`）；静态反汇编/字节断言未复跑（`XVERIFY_S543_0f4bd824/VERDICT.md:130`）；截图 sha/mtime/时序未核；ρ/φ/镜像逐字节比对未跑；**没有任何运行期函数占用、调用链、墙钟热点或阶段链条的实测**，本件也不补这类实验。

### 0.3 引用约定（本件代号 → 绝对文件路径）

沿用 `RULING.md:19-39` 的代号；`B1`、`X1`、`X1C` 是本件新增代号。所有行号均为本次会话读到的实际工作树行号。

| 代号 | 绝对路径 |
|---|---|
| R | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RULING.md` |
| RC | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/RECHECK.md` |
| FB | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/FACTBASE.md` |
| N | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/factbase_probe_output.txt` |
| M | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S544_TRI_MODEL_VERDICT_20261104.md` |
| H | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/VERDICT.md` |
| Q2 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V2/REPORT.md` |
| S | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/S543_FREEZE_WAS_SCORESCREEN_20261104.md` |
| P | `D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md` |
| E0 | `D:/Project/ra2-campaign-forge/lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md` |
| E1 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md` |
| E2 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/E3_TRIGGER_N_20261103.md` |
| E3 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/E3_TRIGGER_N_CORRECTION_20261103.md` |
| B1 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/BATCH1_VERDICT.md` |
| X1 | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/EX1_DATAFACE.md` |
| X1C | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/impl_f4bcf30c/ex1_checks.txt` |
| V543G | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/VERDICT.md` |
| V543b | `D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/VERDICT.md` |

数据根（只读）：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`（`FB:35`、`N:3`）。EX-1 的 47 窗混杂控制表在同写域姊妹件 `X1:166-263`，本件引用其结论，不复制、不改写该表。

---

## 1. 状态声明：**当前 E3 不执行**

**D-13 选原选项「暂停」，执行含义是关闭当前版本 E3 用于目标①的实施申请**（`R:128`；裁定为「高」确信度，`R:140`、`R:204`；复查确认「暂停选择成立」，`RC:29`）。

### 1.1 明确关闭的具体项（逐项，全部不批准）

| # | 被关闭项 | 裁决原文依据 |
|---|---|---|
| 1 | **N=1 秒 MiniDump**（备选 A 的长停采样） | `R:128`「不执行A的N=1秒MiniDump」；`R:5`「不批准A的N=1秒长停采样」；`P:92-93` 为该项原申请 |
| 2 | **逐线程 Suspend/StackWalk**（备选 C） | `R:128`「不执行C的逐线程Suspend/StackWalk」；`R:5`「也不切换C」；`P:94-95` 为该项原申请 |
| 3 | **编写 E3 采样候选代码**（含离线单测形态） | `R:128`「当前也不批准编写E3采样候选代码」；`R:169`「只出文档，不写E3采样候选代码」；`P:98-100` 原问「是否只批编写候选件+离线单测」，本次同样不批 |
| 4 | **真机发射 / 活进程采集** | `R:128`「或真机发射」；`R:158`「不得执行活进程采集来补齐」；`R:169`「不启动/读取活进程」 |
| 5 | 变相关闭项：**降低 N、增加频率、把「改绑 22 窗」当成新实现授权** | `R:128`「不通过降低N、增加频率或把『改绑22窗』当成新实现授权」；`R:181`「不能仅改对象名称而保留无覆盖触发」 |

补充的授权边界（不要把关闭范围写歪）：

- **原有目标② E3 方案**保留其独立服务对象和条件；本裁决**不批准执行、也不替目标②另作结案**（`R:128`）。E3 原服务对象与触发条件为「②挂死未退 / `latch_detected`」（`E0:5-6, 16-17`、`E1:24, 35-40`），迁移到①不是原方案的直接执行（`R:134`）。
- 裁定覆盖**只到「本版 E3 不适用于当前目标①问题的实施路径」**；**不声称采栈技术对持续低速永远无效**（`R:130`），也不否定一切未来采栈技术（`RC:29`）。
- 本次关闭**不等于目标①已解决**：现象证据成立、机制仍未闭合（`R:130`，详见 §6）。
- 将来任何侵入性采集仍须**用户明示**；资料齐备和 Lead 验收均不构成授权（`RC:30`、`P:99-100`）。

---

## 2. 阈值覆盖：`0/22` 与 `87.7%` 的旧分母

### 2.1 N=1 秒对 22 窗覆盖 **0/22**

- 22 个 25 秒持续低速窗（`/8 趟`）的 `stats.max_stall_s` 记录值范围 **0.103742 – 0.749879 秒**，最大值为 **0.749879 秒**（`N:14`；`FB:80, 122`；`R:135`；`X1:146`）。
- 因此按记录值，**≥1 秒（N=1 秒）谓词在这组已观测历史窗中的覆盖是 0/22**（`R:135`、`R:199`、`FB:122`）。本轮检查 A 独立重算并确认：`low_both_25s windows = 22 trips = 8`、`max_stall_s max = 0.749879`、`windows with max_stall_s >= 1.0 = 0 / 22`（本件 §0.2 检查 A 实际 stdout）。
- 复查阶段已回到原始样点确认 0.749879 秒（`l3_20261031hb/measure_w1.json` 的 `stored_max_stall_s` 与重建值一致，`RC:55, 62`）。
- **边界**：这是阈值比较的逻辑结果，只针对这 22 个**已观测历史窗**；**不证明未来任何持续低速都无长停**，也不预测未来趟次（`FB:122`、`R:199`）。「误触率 0」（`E3:61-64`、`P:87-88`）即使成立，也不等于能观测当前要解释的持续低速（`R:135`）；「长停与短停可能同栈」是零证据推测，不能替代覆盖论证（`E2:116`、`E3:69-75`、`R:186`）。

### 2.2 `87.7%` 的原分母是**旧 1734 个 >0.1 秒事件**，不是 22 窗重算比例

- 原始出处：`E2:17, 36-47`。`87.7%` = **1521/1734**，分母 1734 是「**全量 1734 个 >0.1s 平台/停滞事件**」的旧数据分布（`E2:36` 标题原文：「全量 1734 个 >0.1s 平台」）；同一分布还给出 `N=1.0s` 只可捕获 50/1734 段 = 2.88%（`E2:16, 60`）。
- 裁决明确：`1521/1734` 是**旧数据中 >0.1 秒平台的事件分布，不是本次 22 窗重新统计出的比例，也不是独立趟比例**（`R:136`）；须**保留为旧事件统计，不外推为 22 窗比例，不作为当前否决的唯一依据**（`R:182`）。
- 因此该数字**只能作旧方案能力边界线索**：说明「帧号停推超 N 秒 + MiniDump」这一旧触发对短停主体的覆盖本就有缺口（`E3:90-95` 亦保留「乙案只能采 ≥1.0s 长停，不能采短停主体」为能力边界）。它**不能拿来证明 22 窗机制**。**否决 N=1 秒的直接依据是 0/22，而非误用 87.7%**（`R:136`）。
- **本轮未重算 1734 段/87.7%**（`FB:129`、`RC:82` 均登记为未运行），本件只照录其原分母与用途限制，不把材料记载冒充本轮通过。

### 2.3 否决现方案的其余已登记理由（不扩展为新技术结论）

对象错配（`R:134`）、触发无对象（本节 2.1）、介入代价与增量价值未闭合（甲案可能自造死锁、乙案可能引入数百 ms–秒停顿、dump 解析路径未验证，均为**方案自述、未在本次实测**；`E0:21-31`、`E1:81-91, 100-101`、`R:137`）、技术表述限缩（不把 dump 总耗时单独推成「任何实现物理上都不可能捕到 0.1 秒事件」；`R:138`）。`≤50ms/次` 只是 C 案的目标，**不是已达到的时延保证**（`R:137`）。

---

## 3. 三个机制缺口（逐条：现有证据 / 缺 / 查阅范围）

> 总纲：现有离线件**没有函数占用或时间对齐的运行期证据**（`R:156`）。三个缺口一律**未闭合**。

### 缺口 1｜持续低速时游戏阶段是否连续可确认 → **未闭合 / 缺**

- **问题**：22 个持续低速窗的**每一时刻**是否都处于同一可确认的战术/游戏阶段（在战、加载、结算、终局），以及阶段转换时点，是否有连续证据。
- **现有证据（只是边界，不是肯定答案）**：
  - 裁决明示「对现有切面的计数分层及其用途选择有直接支持；**这不等于确认 22 窗每一时刻的战术阶段或运行期瓶颈已知**」（`R:93`）；「**各窗战术阶段的连续确认程度**」列入尚未查明疑虑（`R:202`）。
  - 截图证据覆盖有限且对象不同：`S:190-191` 的「32 个冻结窗中有计分屏证据 21 个、11 个无证据」针对的是**整窗零推进冻结窗**，不是 22 个持续低速窗；`S:218-230` 明列 11 个无图/纯战斗画面窗「本件分不清，不作结论」；`R:102` 更明确「**截图在窗末，不能单靠该图把整个 25 秒每一时刻都标成终局**」。
  - 11 个停摆主导窗整组为「**停摆观测、待归因**」，既不作为已证在战卡顿正证、也不整组认定终局（`R:111, 146`）；其中 `l3_20261023q/w2` 单列未知阶段（`R:118`）。这些**不用于替代持续低速机制**（`R:146`）。
  - 本轮对 104 份原始 JSON 做完整递归键遍历：63 个键中**无 `stage`/`phase`/阶段类字段**（§0.2 检查 B，`runtime_attribution_like_keys = []`；与 `X1C:13` 的顶层键清单一致）。
- **缺**：22 窗逐窗的阶段标签、窗内阶段连续确认材料、截图与窗内时刻的时间对齐、阶段转换时点 —— 一律写「**缺**」。
- **查阅后仍是「缺」的文件**：`R:93, 102, 111-122, 146, 202`（裁决及证据强度边界）、`S:188-191, 215-230`（计分屏覆盖与 11 窗挂账）、`X1:166-263`（47 窗混杂表：仅 map/harness/起止帧/门控/units0 五列，**无阶段列**）、`X1C:12-17`（全库键扫描）、104 份原始 `measure_w*.json`（本轮检查 B）。上述文件均未提供 22 窗阶段连续确认证据，故不补造。

### 缺口 2｜哪些函数/调用链占据了墙钟时间 → **未闭合 / 缺（缺少运行期耗时定位）**

- **问题**：持续低速期间墙钟时间落在哪些函数、调用链或等待点上。这是目标①现象真正要解释的量（`RC:29`：持续低速本身不给出一个特殊的「停滞瞬间」，必须解释的是**持续低速期间墙钟时间落在哪里**）。
- **现有证据（静态 ≠ 运行期）**：
  - 裁决：**已有静态反汇编只列「静态事实/候选路径」，不能把可达路径写成历史运行期命中**（`R:155`）；静态字节结论与运行期因果归因分开，§540/§541 字节结论不得继续冒充运行期定位证据（`R:97`）。
  - `B1:106-108` 的「真机判别表」自述「全部出自 P01 §5 / P02 §2.7 / P04 §4 / P05 §1.13 的**静态判据，本批一条都未真机执行**」；`B1:104`「全部真机判别式……零真机铁律，一条都未执行」。
  - E3 原方案的目的恰是「把静态自旋环定性**升级为运行期定位**（线程卡在哪一帧）」（`E0:9-11`），而该方案**本阶段不执行**（本件 §1）；`E0:1` 自标「**未获授权、未执行**」。
  - 「22 窗内的实际运行期热点」「静态路径的历史运行期命中」列入尚未查明疑虑（`R:202`）；`R:196` 明示本会话读到的源码事实「**不证明游戏慢在何处**」。
  - 本轮 104 份原始 JSON 全键扫描：**无 stack / call / func / symbol / dump / thread / profile / hotspot / stage / phase 类键**（§0.2 检查 B：`runtime_attribution_like_keys = []`；`X1C:12-13` 亦记 104 份无 harness/sha16 键、顶层键清单）。原始测量语料里**没有**任何函数级或调用链级运行期记录。
- **缺**：函数/调用链级墙钟占用、线程栈快照、采样热点、与 22 窗时间对齐的运行期定位 —— 一律写「**缺**」。按 `R:156` 的固定用语：**「缺少运行期耗时定位，现有离线件不能闭合」**。
- **查阅后仍是「缺」的文件**：`R:97, 155-156, 196, 202`、`E0:1, 9-11, 20-31`、`B1:103-108`、`FB:129`（未运行完整实时速度机制）、`V543G:119-120`（§540/§541 指令结构不受窗体解释影响，但**不是运行期命中**）、`V543b:130, 187`（字节断言本路未核）、`X1C:12-17`、104 份原始 JSON（本轮检查 B）。上述均无运行期耗时证据，故不补造。

### 缺口 3｜固定版本/地图/采样相位后，哪项变量具有因果区分力 → **未闭合 / 缺**

- **问题**：在**固定**版本、地图、采样相位之后，是否存在某个变量（负载、时段、协议旗标、宿主状态等）对快/慢具有**因果**区分力。
- **现有证据指向的是「不可分辨」，不是「某变量有区分力」**：
  - `Q2:286-288`：缺 `sf=800 × harness8_v3` 与 `sf=400 × harness8_v4` 的交叉格，「版本 vs 协议 vs 时段」三者在本库内**结构性不可分辨，需要新趟才能分开——本件不新跑**。
  - `Q2:130-139`：同版本·同图·负载±40 配对 n=16、中位 1.06x、>3x 对数 0；跨版本 n=25、中位 1.91x、>3x 对数 6；「时代效应」与工具链版本/协议效应**不可分**，不能作为结论使用。
  - `Q2:199-212`：全局 −0.57 的「负载越重越慢」信号**固定版本后基本散架**（6 个版本里 2 个变正号、1 个零方差）；「带内的快慢差异在版本内部靠 `units0` 解释不了」，去趟均值后组内 ρ_P(c_units, live) = −0.06。
  - `M:63-67`：「地图/相位也混杂」；「**时代效应**」概念整体撤回，只能说「跨趟存在大幅速度差，与工具链版本/地图/采样相位**共线，不可分立**」。
  - 裁决：**不同版本/地图/相位不得合成因果配对**（`R:150`）；「`units0` 是起始/settle 负载描述，**不冒充每个窗的实时同负载**」（`R:150`；`X1:174`）。
  - EX-1 的 47 窗混杂表本身显示**版本轴还有缺格**：47 窗中 **25 窗** `harness_sha16` 为「缺」（`X1:238, 245-263`；`X1C:17` `missing={"harness_sha16": 25, ...}`），无法据此构造固定版本后的配对。
- **缺**：固定三轴后具因果区分力的变量及其可识别配对 —— 写「**缺**」。现有材料只证明「三轴共线、无法分离」，**不得**改写为「只是版本效应」，也不得把 `units0`、`gap_s`、时段、协议旗标中任一项升格为原因。
- **查阅后仍是「缺」的文件**：`Q2:81-100, 112-117, 124-139, 143-168, 199-212, 269-289`、`M:60-67`、`H:34`、`R:150, 184`、`FB:114`、`X1:233-263`、`X1C:17`。上述均给不出固定三轴后的因果变量，故不补造。

---

## 4. `l3_1101v4c` 线索（同版本同地图，趟内由慢转快）

### 4.1 字段身份（**强制标注，复查 R2 补强**）

| 窗 | **主指标 `stats.fps_avg`（原始存储字段）** | **派生 `live_fps`（首末帧沿差商，仅作诊断）** |
|---|---:|---:|
| w0 | **18.52**（18.520948494813613） | **18.54**（18.539626790502314） |
| w1 | **28.40**（28.40179635682234） | **28.42**（28.416096013424877） |
| w2 | **30.68**（30.681571141892938） | **30.71**（30.70530239738328） |

- 裁决订正：原稿 `18.54→28.42→30.71` 是**派生 `live_fps`**（首末帧沿差商），**不是源码字段**；三窗**主指标 `fps_avg` 实为 `18.52→28.40→30.68`**（`R:151-154`；`RC:15-21`）。
- 派生公式与「原件无该字段」：派生值 = `(frame_edges[-1][0] − frame_edges[0][0]) / (frame_edges[-1][1] − frame_edges[0][1])`，即首末帧沿的帧号差/时间差（`RC:64-80` 检查 B 的实际命令）；三窗 `has_stored_live_fps: false`（`RC:19, 77-79`）。本轮 §0.2 检查 A 独立重算，六个数与 `fps_avg`/派生值逐位一致，且 `has_stored_live_fps` 三窗皆 false。
- 两组数**都支持「趟内由慢转快」**，但引用时必须注明字段；**不得把派生值填进 avg 栏**（`R:154`、`RC:21`）。主指标维持 `fps_avg`（`R:89`）。
- 原汇总/核验件沿用派生序列且未标口径的位置：`M:147`（`18.54 / 28.42 / 30.71`）、`H:34, 52, 80`（`18.5396/28.4161/30.7053`、`18.54→28.42→30.71`）、`Q2:59, 116, 248`。本件照裁决订正后引用，不改写这些只读原件。

### 4.2 现有证据**能比较什么**（只记录，不解释原因）

本轮 §0.2 检查 B 从原始件直接读到的可比较项：

| 比较项 | w0 | w1 | w2 | 字段来源 |
|---|---|---|---|---|
| `trip_id` | 同一 `QC161-U0800-L3-V4-20261101C` | 同 | 同 | `measure_w*.json` 顶层 |
| `map_sha256` | 同一 `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36` | 同 | 同 | `measure_w*.json` 顶层 |
| `gamemd_sha256` | 同一 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | 同 | 同 | `measure_w*.json` 顶层 |
| `harness_sha16` | 同一 `38244d2907e7f7fa`（`qc151_trip.harness8_v4.py`） | 同 | 同 | **趟目录 `_launch_result.json`**，原始 measure JSON 内无版本字段（`Q2:84-86`、`X1:171-172`） |
| `span_s` | 25.0 | 25.0 | 25.0 | 顶层；25 秒是**名义时长**（`R:89`） |
| `settle_s` | 4.0 | 0.0 | 0.0 | 顶层 |
| 起帧→末帧 | 869 → 1332 | 1333 → 2043 | 2044 → 2811 | `frame_edges[0][0]` → `frame_edges[-1][0]`；三窗帧号连续（`X1:195, 218-219`） |
| `gate.ok` / `verdict` | `true` / `ok` | `true` / `ok` | `true` / `ok` | `X1:195, 218-219` |
| `gate.units0` | 1229 | 1229 | 1229 | **settle 阶段起始读数**，三窗共用同一值；**不是三窗实时同负载的证据**（`R:150`、`X1:174`） |

因此现有证据只能比较：**同一趟、同一地图哈希、同一引擎哈希、同一 harness 哈希记录、连续三个名义 25 秒窗**之内，主指标 `fps_avg` 与派生 `live_fps` **都单调上升**（由慢转快）；同一版本同一地图内部存在快/慢两态，构成「不只是版本效应」的**自身反例**（`Q2:115-117`、`H:34, 52`、`R:151`）。同 BOOT 下 v4d/v4e 三窗分别 31.18/31.27/31.27 与 31.29/31.24/31.27（`M:145-149`），可作**描述性对照**，但不同 trip、不同 `units0`（1225 / 1189），不是同负载因果配对（`Q2:59-61, 70-73`）。

**不得归因**：本卡**不**把 w0→w2 的速度变化归因于寻路、会话/进局相位、宿主争用或兵力变化。上述四项在此均**无运行期证据**，写「缺」。`H:80` 提出「应查进局后帧 800→925 的 settle 相位、单位生成时序与寻路/脚本负载」，是**未来核查建议，不是既有结论**；`R:151` 明确要求「只记录现有证据能比较什么，**不归因成寻路、会话、宿主或兵力变化**」。同理，w0 `settle_s=4.0` 与 w1/w2 `settle_s=0.0` 的差异、以及首帧 869→2044 的相位变化，只是**记录到的字段差异**，不得升格为原因。

---

## 5. 混杂限制：版本、地图、采样相位**结构性不可分辨**

**不是「只是版本效应」。** 三者与协议/时段共线，现有库内拿不出可分离的交叉格：

- **版本 × 协议**：`Q2:112-113`「版本与协议在带内是同一次改动」：`harness8_v4` 与 `--h7-measure-start-frame 800` 一起出现，v3/h8 配 `sf=400`；`Q2:154-156`「**每次换 harness 版本都同时改协议旗标 ⇒ 版本效应与协议效应本身也不可分**」。
- **地图**：`Q2:147-149` `map_sha256` 全库多个取值，带内 8 趟同为 `f3bb0a4e`，但 §544 举的 881-unit 慢窗 `l1c_20261021` 在 `0add791d11ae`（L1 图），快慢对照**跨图**；`Q2:278` 明列 1225 vs 881 是「**跨图 + 跨档 + 跨版本**」三重异质对照；`M:63-64`「地图/相位也混杂」。
- **采样相位 / 时段**：`Q2:154-155` `--h7-measure-start-frame` 为 default/400/800/1200；`Q2:157-168` 采样饥饿 `gap_s` 指纹与时段一起变，ρ_P(live, gap_s) = −0.434；`H:34` 记 `h7_measure_start_frame` 分布 `{400:4, 800:5, 1200:1}`，快趟 f0=869/920/925、慢趟 f0=387/434/454/957/1095/1158，「**采样相位随版本变**」；`Q2:72-73`「fast 组是在战斗更晚相位被测的」。
- **结论口径**：`Q2:286-288`「版本 vs 协议 vs 时段三者在本库内**结构性不可分辨**，需要新趟才能分开」；`Q2:272-274`、`M:66-67`「与工具链版本/地图/采样相位**共线，不可分立**」；`Q2:277`「同负载在 `units0` 精确口径下一对跨日期对照都没有」。
- **裁决归述纠偏**：`R:184` 明确 `M:188`、台账把 qfmodel 归为「只是版本效应」是**失真归述**；`FB:114` 指出 Q2 原文「时代与版本/协议效应无法分离，不能作为结论」「三者结构性不可分辨」，**只采「现有数据不能分离这些效应」，不作单因归因**；`H:34` 亦判「**只是版本效应**」被自身反例推翻。
- **数据面自身的缺格**：EX-1 的 47 窗混杂控制表中 **25 窗 `harness_sha16` 为「缺」**（`X1:238, 245-263`、`X1C:17`）；`Q2:90` 另记 archive_T*/t55k/l1a 共 22 窗无 `_launch_result.json`、harness 身份未证实（`Q2:289`）。版本轴本身不完整，更不能被当作已控制的单因。

因此：跨日期的「9.2 vs 31.2」之类快慢差**只能描述为共线差异**，不能拆成版本、地图、相位或其中任一项的因果效应；`R:150` 禁止把不同版本/地图/相位合成因果配对。

---

## 6. 机制状态：**机制未闭合**

### 6.1 裁决固定的缺口表述（照录，`R:146`）

> **目标①：22个25秒持续低速窗/8趟的现象成立；运行期耗时落点和因果链未定位。11个停摆主导窗另列阶段/终局待归因，不用于替代持续低速机制。当前E3→①方案关闭，不以正常退出或p50较高宣告机制已解。**

### 6.2 本件的状态判定

- **机制未闭合**。现有离线件没有函数占用或时间对齐的运行期证据（`R:156`）；§3 三个缺口逐条为「缺/未闭合」；§4 的 v4c 只是趟内趋势线索；§5 的三轴不可分辨使跨趟因果比较无效。按 `R:156`：「**填写『缺少运行期耗时定位，现有离线件不能闭合』，到此交付**」，**不靠再算窗口比例、重复投票或扩大引擎停摆叙事继续循环**。
- 现象证据成立 ≠ 机制已解：`R:130`「目标①的现象证据成立，**机制仍未闭合**……不能写成『目标①已解决』」；`R:93` 计数分层的高确信度「不等于确认 22 窗每一时刻的战术阶段或运行期瓶颈已知」；`R:204`「具体性能机制仍未知」。
- **不以正常退出宣告机制已解**：`E1:35-40` 记目标①所引趟正常退出（`rc=0`、`duration_s=259.7`、`leftover_procs=[]`）；`R:105` 明确「正常退出……**本身不能区分『曾慢/曾停』与『正常结算』**」；`R:134` 把它列为 E3 对象错配的原文支持。
- **不以 p50 较高宣告机制已解**：主指标维持 `fps_avg`，p50/live **仅作分型，不替换主指标、不用于给停摆窗出健康结论**（`R:89`）；`R:73` 「不以 p50 较高为由把 11 个停摆窗洗成健康」。`FB:101` 与 `RC:57` 的 T34 实例：原存 `fps_avg=0.360002`、`fps_p50=31.608660`、零 >10ms 采样缺口却停约 24.734760 秒 —— p50 高与长停并存（本轮未重跑 T34，此处为已读材料的记载）。
- **11 个停摆主导窗**整组仍为「停摆观测、待归因」，**不用于替代持续低速机制**（`R:111, 146`）；它们不从原始 33 低 avg 计数中抹除（`R:111`）。
- 本件不以「已出卡」冒称 D-13 在台账/PENDING 已落账：登记状态按 `R:170` 为「已裁、待来源会话落实」，本件是域内候选件。

---

## 7. 未来重开条件（**书面要求，本轮不执行**）

任何未来 E3→①重开只能是**新方案事项**，**不沿用本次关闭申请自动实施**（`R:158`、`R:155`）。须先书面提供以下五项，缺一不构成重开依据（`R:158`；`R:169` 本轮禁止启动/读取活进程）：

| # | 书面要求 | 依据与现状 |
|---|---|---|
| 1 | **与持续低速对象一致的判据**：阶段判据 + 持续低速判据，须对准 22 窗/8 趟这类「全程低速」对象，而不是 latch 后未退出的挂死对象或 ≥1 秒长停瞬间 | `R:158`「与持续低速对象一致的阶段/持续低速判据」；`R:134`（原对象错配）；`RC:29`（持续低速不给出特殊停滞瞬间，须解释墙钟时间落在哪里）；`R:150`（阶段/门控/units0 阶段须逐窗登记，缺写「缺」） |
| 2 | **覆盖论证**：证明触发条件对该对象确有覆盖，而非改绑对象名称或调 N 了事 | `R:158`；`R:135, 199`（现有 0/22 是覆盖不足的直接证据）；`R:128, 181`（禁止仅降 N/加频率/改绑 22 窗）；`E3:69-75` 的「可能同栈」不得替代覆盖论证（`R:186`） |
| 3 | **端到端延迟与扰动预算**：实际触发延迟、冻结时点、保存耗时须分开给出并验证；不得把 C 案 `≤50ms/次` 当已达成保证 | `R:158`「端到端延迟及扰动预算」；`R:138`（三种时延是不同量，本次未测）；`R:137`（甲案可能自造死锁、乙案数百 ms–秒停顿，均为方案自述未实测）；`E0:21-31, 44-48`、`E1:97-103` |
| 4 | **可验证的离线解析链**：dump/栈产物到可读结论的解析路径须先验证 | `R:158`；`R:137`「dump 解析路径未验证」；`E1:84, 150`「本机 procdump/cdb 全无、需自研解析器，可能采到 dump 却读不出栈」；`E0:29-30` |
| 5 | **与目标②读数隔离办法**：受采样影响的退出读数不得混入②正常退出验证；并给出明确执行范围 | `R:158`「与②读数隔离办法和明确执行范围」；`R:137`「更不能把受采样影响的退出读数混入②正常退出验证」；`E0:59`、`E1:113-114`「dump 停顿须与退出时点读数分列」；`R:128`（②方案保留独立服务对象，本裁决不替其结案） |

**授权与执行边界（同样只作书面登记）**：以上只是将来方案的书面要求；**在当前零真机约束下不得执行活进程采集来补齐**（`R:158`）。E3 属侵入性操作，须**用户明示**；资料齐备和 Lead 验收**均不构成授权**（`RC:30`、`P:99-100`）。本轮**不写采样代码、不启动游戏、不读活进程内存**（`R:169`、`P:100`）。

---

## 8. 交付边界与未闭合登记

- 本件只承担 EX-4；**不替代** EX-1 数据面（`X1`）、EX-2 追加勘误、EX-3 十一窗证据表、EX-5 主流程验收（`R:166-170`）。本件不修改台账/PENDING，不登记结案（`R:13, 170`）。
- 本件所有数字来源分三类，均已在正文标明：① 本轮 §0.2 两条只读核对命令的**实际 stdout**；② 裁决/底账/复查/核验件的**已读原文行号**；③ 题目与裁决给定的底账。**没有**根据其他窗、其他趟或推理补造任何字段值；原件查不到的写「缺」并列明查阅范围（§3）。
- **未闭合清单**（不得视为已解决）：22 窗运行期热点/函数与调用链墙钟占用；22 窗阶段连续确认；11 停摆窗终局转换边界及 `q/w2` 原因；无充分图像的零推进窗实际状态；静态路径的历史运行期命中；固定三轴后具因果区分力的变量；更合适采样的覆盖、扰动与解析能力（`R:202`）。
- **机制未闭合**是本件的交付终点，不是待补的空白（`R:156, 204`）。
