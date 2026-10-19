# 空图对照件 EMPTY 规格与用法（ZC-H1RM 段 0.4）

> 任务卡 ZC-H1RM 段 0.4 · 执行方 MiMo（M 轨 T21）· 工作区 `D:\Project\ra2-campaign-forge`
> 生成/校验工具：`tools/empty_map_gen.py`（ROOT 经 `tools/_ra2_paths.py` 便携解析）
> 证据等级：`[实证]` = 文件字节/字段/可复算脚本输出。

---

## 0. 一句话

EMPTY = **与 H1 同尺寸同 waypoints 的 100×100 TEMPERATE skirmish 空图**，无任何预置对象、**无 H1FP1 指纹**（缺指纹是预期，不是失败），供 A2 delta 做 units_seen 零点对照。**禁止由 H1 图删段冒充**。

---

## 1. 规格（生成即满足）

| 项 | 值 | 校验键 |
|---|---|---|
| 文件名 | `[2]0LoadBench_EMPTY.yrm` | — |
| 显示名 `Name` | `[2] 0LoadBench EMPTY`（**无** `fp:` 短标） | `no_name_fp_tag` |
| 尺寸 | 100×100（与 H1 一致） | `size_100x100` |
| 剧场 | TEMPERATE | — |
| 预置对象 | `[Units]/[Infantry]/[Structures]/[Aircraft]` 共 **0** 行 | `no_preplaced_objects` |
| Waypoints | 仅 `0`、`1`（与 H1 相同坐标） | `waypoints_present` |
| 指纹 | **无** `H1Fingerprint` / **无** `H1Tier` | `no_h1fingerprint` / `no_h1tier` |
| 多人字段 | `MultiplayerOnly=1` `MaxPlayer=2` `MinPlayer=2` | `multiplayer_fields` |
| 房屋配置 | 与 H1 对齐（14 house tech10/credits10000/iq5） | 生成器内置 |
| 来源 | `MissionMap` **从零生成**，非 H1 删段 | 生成器断言 |

## 2. 哈希（当前冻结件）

| 产物 | 字节 | sha256 |
|---|---|---|
| `out/loadbench/[2]0LoadBench_EMPTY.yrm` | 3669 | `26d83424cfc45c81bc733dc243c3520046963d4d4f329e82172c1f8e29651725` |
| `out/loadbench/pristine/EMPTY/[2]0LoadBench_EMPTY.yrm` | 3669 | 同上（字节级镜像） |

MANIFEST 行（`out/loadbench/pristine/MANIFEST.sha256`，UTF-8 **无 BOM**）：

```
26d83424cfc45c81bc733dc243c3520046963d4d4f329e82172c1f8e29651725  3669  EMPTY  out\loadbench\[2]0LoadBench_EMPTY.yrm  out\loadbench\pristine\EMPTY\[2]0LoadBench_EMPTY.yrm
```

## 3. 用法

```powershell
# 生成 + 自检 + 注册 MANIFEST（幂等）
python tools/empty_map_gen.py

# 只校验现有空图（不写盘）——CI/门禁用
python tools/empty_map_gen.py verify

# 生成但不碰 MANIFEST
python tools/empty_map_gen.py --no-manifest
```

退出码：`0` = 全部 check PASS，`1` = 任一 FAIL。

## 4. 在 ZC-H1RM 中的用法（段 0.4 / 段 2）

- **段 0.4**：装图前确认空图在位且 `verify` 全绿；记录图名 + sha256 进 RESULT。
- **段 2（A2 delta）**：对每档 `tier`，`delta = units_seen(H1_tier) − units_seen(EMPTY, 同 player/enemy/UnitCount)`。
  - 缺空图对照 ⇒ 该格 `delta=null`，档判 `NO_EMPTY_CTRL`（FAIL-证据）——**不得**用 H1 删段件或任意图顶替。
- **指纹口径**：EMPTY **期望无 H1FP1**。进图读不到 `H1Fingerprint` 对 EMPTY 是**正常**（与 H1 的 S1-c「装载物版本错」判定不同场景，勿混用）。

## 5. 自检清单（2026-09-30 实跑）

| 门禁 | 结果 |
|---|---|
| `python tools/empty_map_gen.py`（build 自证） | `[OK]` 7/7 checks PASS |
| `python tools/empty_map_gen.py verify` | `[PASS]` |
| `python tools/bench_map_install.py --verify` | `PASS=14 FAIL=0`（含 EMPTY 镜像行） |
| MANIFEST 编码 | UTF-8 **无 BOM**；含 EMPTY 行 + 新 H1 三行 |

产物留证：`out/re_work/empty_map/build_report.json`。
