# M 轨就绪检查清单（2026-09-30）

> [META]
> 任务=轨道 M · 就绪门禁只读检查 · 执行方=MiMo（M 轨）· 日期 2026-09-30
> 检查时点：**2026-09-30 10:13–10:15（本地）** / 02:13–02:15 UTC
> 写作用域：本文件 + `out/re_work/m_ready_check/**`（日志）+ `docs/re/iface_mimo_re.md`（文末追加）
> 性质：**只读门禁**，不改产品代码、不改地图、不改 MANIFEST、不启动游戏

---

## 1. 门禁检查结果表

| # | 门禁 | 命令 | 结果 | 退出码 | 时点 | 备注 |
|---|---|---|---|---|---|---|
| G1 | except gate 自检 | `python tools/check_except_gate.py --selftest` | **PASS**（18/18） | 0 | 10:13 / 10:14 复跑 | 全部断言通过；报告落 `out/re_work/except_gate/selftest_except_gate.json` |
| G2 | H1 进图指纹 | `python tools/h1_map_fingerprint.py verify` | **PASS**（3/3） | 0 | 10:13 / 10:14 复跑 | 三档 max_stack=1、unique==total；指纹见下表 |
| G3 | 地图安装校验 | `python tools/bench_map_install.py --verify --game-dir ra2bench` | **PASS**（13/13） | 0 | **10:13 首跑 FAIL=3 → 10:14 复跑 PASS=13** | T15 在窗口内更新 MANIFEST，见 §2 |
| G4 | 工具语法编译 | `python -m py_compile tools/bench_replay.py tools/bench_cam_reset.py tools/check_except_gate.py` | **PASS** | 0 | 10:14 | 三脚本均无语法错误 |
| G5 | 真机包 A | `prompt_zcode_except_ab.txt` | **可交** | — | 文件 09:51 | 见 §3 |
| G6 | 真机包 B | H1 复测卡 | **缺口** | — | — | T16 未落独立复测卡，见 §4 |

### 1.1 H1 指纹明细（G2）

| 档位 | 文件 | objects | unique_cells | max_stack | hash12 | 指纹串 |
|---|---|---|---|---|---|---|
| U0050 | `[2]0LoadBench_U0050_H1.yrm` | 350 | 350 | 1 | `26c371932de7` | `H1FP1\|U0050\|26c371932de7` |
| U0200 | `[2]0LoadBench_U0200_H1.yrm` | 1400 | 1400 | 1 | `4bf2d6692bd5` | `H1FP1\|U0200\|4bf2d6692bd5` |
| U0800 | `[2]0LoadBench_U0800_H1.yrm` | 5600 | 5600 | 1 | `1189b6b550ff` | `H1FP1\|U0800\|1189b6b550ff` |

> 旧图（7× 堆叠、unique=50/200/800）已冻结于 `out/re_work/h1_map_fix/backup_pre_fix/`，含当时 MANIFEST。

---

## 2. T15 / MANIFEST 时点记录（G3 过程）

| 时点 | 事件 | 结果 |
|---|---|---|
| 2026-09-28 12:37:10 | MANIFEST 首次采集（H1 = **旧字节** 22359/79052/309630，sha `1447a962…/2fb6ab3a…/0dd6b270…`） | 基线 |
| 2026-09-30 09:55–09:57 | H1-MAPFIX 重生成三档图（cell 互斥 + 指纹），落 `pristine/H1/` | 新字节 22344/79411/309822 |
| **10:13:39** | M 轨首跑 `bench_map_install --verify` | **PASS=10 FAIL=3**（H1 三档 vs MANIFEST 不一致：镜像已是新字节，MANIFEST 仍旧哈希） |
| **10:14:41** | **T15 更新 MANIFEST.sha256**（H1 三行改写为新 sha `2013a100…/56bfc344…/e3acc130…`，字节数同步） | 对齐完成 |
| **10:14:48** | M 轨复跑 `bench_map_install --verify` | **PASS=13 FAIL=0** |

**结论**：G3 现状为全绿。首跑 FAIL 属「T15 改 MANIFEST 途中」的预期竞态，非产品缺陷。若下游复跑仍见 FAIL=3，请先核对 MANIFEST mtime 是否 ≥ 2026-09-30 10:14:41。

MANIFEST 现行 H1 条目：

```
2013a1007f73ad2c7870c47df5ace3a5527335f22c600ac563dbe1ae35e43269  22344  H1  ..._U0050_H1.yrm
56bfc344f83986364c0c2d74e0d9e6188ae9283b23340c286597d738bd546eee  79411  H1  ..._U0200_H1.yrm
e3acc1305f98698da293e5969cf6769c2ca7a84c758a18ff6b7ba020a28d9e39  309822  H1  ..._U0800_H1.yrm
```

---

## 3. 可交真机包文件列表

### 3.1 已就绪

| 产物 | 路径 | 大小 | 时点 | 状态 |
|---|---|---|---|---|
| **EXCEPT A/B 真机协议卡** | `out/re_work/dispatch_v30/prompt_zcode_except_ab.txt` | 6,279 B | 2026-09-30 09:51:04 | **可交 ZCode** |
| 上游取证定谳（只读引用） | `docs/re/except_zc11_forensics.md` | 24,181 B | 09-30 00:32 | 随卡引用 |
| A/B 协议细则（M 轨文档） | `docs/re/except_ab_protocol.md` | 17,207 B | 09-30 09:50 | 随卡引用 |
| H1 机制底座（指纹/误选签名） | `docs/re/h1_fanout_mechanism.md` | 20,724 B | 09-30 00:22 | 随卡引用 |
| H1 修复 + 指纹规格 | `docs/re/h1_map_fingerprint.md` | 15,675 B | 09-30 09:57 | 随卡引用 |
| except 门禁 harness | `docs/re/except_gate_harness.md` + `tools/check_except_gate.py` | — | 09-30 10:00 / 09:49 | 工具自检 PASS |
| H1 图三档（canonical） | `out/loadbench/pristine/H1/[2]0LoadBench_U{0050,0200,0800}_H1.yrm` | 22344/79411/309822 | 09-30 09:57 | 指纹 PASS，MANIFEST 对齐 |
| H1 图工作副本 | `out/loadbench/[2]0LoadBench_U{0050,0200,0800}_H1.yrm` | 同上 | 09-30 09:57 | 同内容 |

### 3.2 缺口（不可交）

| 产物 | 现状 | 缺口说明 |
|---|---|---|
| **H1 复测卡（ZCode 可执行）** | **未落独立卡片** | 见 §4 |

---

## 4. 遗留缺口

### 4.1 H1 复测卡（T16）— **未就绪**

仓库内与「H1 复测」相关的现有文件：

| 文件 | 时点 | 判定 |
|---|---|---|
| `out/loadbench/H1_REMEASURE_RUNBOOK.md` | 2026-09-28 12:39 | **陈旧**：字节数仍写旧图 22,359/79,052/309,630（7× 堆叠版）；安装步骤与还原纪律可参考，但负载口径（2 槽 fanout）已被 M1 修复推翻 |
| `docs/re/h1_map_fingerprint.md` §8/§9.5 | 2026-09-30 09:57 | 含「待实测」四项（真机读回指纹、国家对矩阵、Neutral 实例化、units_seen 标度），但是**规格卡**不是 ZCode 执行卡 |
| 独立 `H1 复测卡` / `prompt_zcode_h1_*` | **不存在** | T16 未写 |

**建议 T16 落卡时必须吸收**：
1. 新指纹口径 `H1FP1|<tier>|<hash12>`，进图先核指纹再计数（防再发三轮皆 U0200 误选）。
2. 新字节数 22,344 / 79,411 / 309,822 与 sha（§2）。
3. A2 delta 口径：`units_seen(H1) − units_seen(空图)` ∈ `[0.8T, 1.2T]`（不再用 2 槽 fanout 绝对值）。
4. 误选签名 U0050/U0200/U0800 ≈ 178/713/2852；`units_seen≈713` ⇒ 判「进错图」作废重跑。
5. 安装/还原一律走 `tools/bench_map_install.py`（LiteralPath 语义，不经 shell 通配）。

### 4.2 其它待实测（非本次门禁范围，供下游知悉）

| 项 | 来源 | 状态 |
|---|---|---|
| M2 负载挂 Neutral/Special | `h1_map_fingerprint.md` §6 | 只出规格未改图；Neutral 是否实例化 `[待实测]` |
| H1 性能 ROI 解冻 | `h1_map_fingerprint.md` §9.6 | **继续冻结**，待真机重测 |
| except A/B 真机执行 | `prompt_zcode_except_ab.txt` | 已成卡，待 ZCode 执行 |
| 张 E-8（Deform +0xA8 与 Verses[1] 重叠） | Verses-Deform ABI | R 轨今日已交 deep dive，待 M 侧收口 |

### 4.3 门禁执行的工具侧写（非人工越界）

以下为门禁脚本自身落盘，记录备查，**非** M 轨手工改写：

- `out/re_work/h1_map_fix/fingerprint_report.json`（`h1_map_fingerprint.py verify` 报告）
- `out/re_work/mimo_benchpris/script/install_log_20260930_*_verify.json`（`bench_map_install.py --verify` 日志）
- `out/re_work/except_gate/selftest_except_gate.json`（selftest 报告）
- `out/re_work/m_ready_check/*.txt`（本清单配套原始日志）

---

## 5. 检查日志索引

| 文件 | 内容 |
|---|---|
| `out/re_work/m_ready_check/check_except_gate_selftest.txt` | G1 全文（18 项 PASS） |
| `out/re_work/m_ready_check/h1_map_fingerprint_verify.txt` | G2 全文（3 档 PASS） |
| `out/re_work/m_ready_check/bench_map_install_verify.txt` | G3 复跑全文（PASS=13 FAIL=0） |
| `out/re_work/m_ready_check/py_compile.txt` | G4 退出码 |

---

## 6. 一句话

> 门禁四绿（selftest / 指纹 / 安装 / 编译），EXCEPT-AB 真机卡可交；**唯一硬缺口 = H1 复测卡（T16）**，且必须按新指纹+新字节重写，旧 `H1_REMEASURE_RUNBOOK.md` 不可直接下发。
