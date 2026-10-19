# H1 地图 cell 互斥修复 + 进图指纹规格（H1-MAPFIX）

> 任务卡 H1-MAPFIX · 执行方 MiMo（M 轨）· 工作区 `D:\Project\ra2-campaign-forge`
> 上游机制拆解：`docs/re/h1_fanout_mechanism.md`（H1-FANOUT）
> 证据等级：`[实证]` = 文件字节/字段/可复算脚本输出；`[推演]` = 由已证事实推出；`[待实测]` = 需真机。
> 写作用域：`tools/bench_maps/build_bench_maps.py`、`tools/h1_map_fingerprint.py`、`out/loadbench/**H1**` 与 `pristine/H1`（经脚本生成+旧件备份）、`out/re_work/h1_map_fix/**`、本文件。
> 禁止：`ra2render/**`、`ra2youli/**`、`ra2bench/**` 手改、`gamemd.exe`、台账、`out/reverse/**`、`ARCHITECTURE_ATLAS*`。禁止真机。

---

## 0. 结论摘要

1. **M1 cell 互斥已修复** `[实证]`：三档 H1 图从「唯一 cell=50/200/800、每格 7× 堆叠」改为「唯一 cell=350/1400/5600、max_stack=1」，写盘前 `assert unique==total` 已装入生成器。
2. **M5 进图指纹已落地** `[实证]`：`[Basic]` 写入 `H1Tier` + `H1Fingerprint=H1FP1|<tier>|<hash12>`，`Name` 带 `fp:<hash12>` 短标；`tools/h1_map_fingerprint.py` 可读回重算并校验，三档全部 PASS。
3. **旧图已备份** `[实证]`：`out/re_work/h1_map_fix/backup_pre_fix/`（含 MANIFEST.sha256，冻结 7× 堆叠原始字节）。
4. **M2（负载挂 Neutral/Special）本次只出规格不改图**：改动会改变 units_seen 语义（从「2 槽 fanout」变为「常驻负载」），需与验收口径（A2 delta）一起换版，避免半改状态。
5. **H1 前提的性能 ROI 仍冻结**：cell 互斥只修几何层，owner→HouseClass 实例化规则（美蘇预置行 0 条进 Array）与 U0200 误选嫌疑尚需真机复测（A3/指纹）。

---

## 1. 问题回顾（H1-FANOUT §1.1 / §4.1 M1+M5）

| 缺陷 | 旧行为 | 后果 |
|---|---|---|
| 同奇偶 house 共用 slots | 7 偶数序 house 叠左带、7 奇数序叠右带 | 唯一 cell = total/7（50/200/800），可落地上限 ≈2×per_house |
| 无进图指纹 | 图名 `U50/U200/U800`（无零填充、无 hash）；`[Basic]` 无 tier 键 | 遥测无法证明「真的进了本档图」；三轮皆 U0200 签名 713 无法当庭拆穿 |

---

## 2. diff（生成器改动摘要）

### 2.1 `tools/bench_maps/build_bench_maps.py`

| 段 | 旧 | 新 |
|---|---|---|
| slot 分配 | `left_slots`/`right_slots` 两组，按 `hi%2` **复用** | `allocate_disjoint_slots()`：每 house 从本侧 pool **切私有连续块**，14 组互不相交 |
| 写盘门禁 | 无 | `assert unique_cells == total_objects`（写前两次：内存对象计 + 最终文本再计） |
| 指纹 | 无 | 哈希 `[Units]/[Infantry]/[Structures]/[Aircraft]` 规范行 → `H1FP1\|tier\|hash12` 写入 `[Basic]`；`Name` 追加 `fp:hash12` |
| 备份 | 无（直接覆盖） | 写前 `backup_if_needed()` 复制旧字节到 `out/re_work/h1_map_fix/backup_pre_fix/`（不覆盖已有备份） |
| 输出位置 | 仅 `out/loadbench/` | `out/loadbench/` + `out/loadbench/pristine/H1/`（两份同内容） |
| 档位名 | `Name=... U50/U200/U800`（无零填充） | `Name=... U0050/U0200/U0800`（与文件名/误选签名口径对齐） |

新增函数（要点）：

```python
def allocate_disjoint_slots(size, n_houses, per_house) -> list[list[tuple[int,int]]]:
    # even-index houses -> West pool, odd-index -> East pool
    # each house takes per_house consecutive row-major cells from its side
    # caller asserts global uniqueness
```

### 2.2 新增 `tools/h1_map_fingerprint.py`

- `load_hash(text)`：对预置对象行做规范哈希（见 §3）。
- `verify_map(path, expect_tier)`：读回 `[Basic]` 指纹、重算哈希、核 tier、核 cell 互斥（`unique==total && max_stack<=1`）。
- `compute_map(path)`：只算不校验，输出 `H1FP1|tier|hash`。
- CLI：`verify` / `compute`，报告落 `out/re_work/h1_map_fix/fingerprint_report.json`。

### 2.3 未改（明确）

- `ra2forge/maplib.py`（布局库，非本轨写域）。
- `IgnoreGlobalAITriggers` 写入仍为 `to_ini_text` 硬编码 `yes`（与 H1-FANOUT 实测一致；是否改 `no` 属 M3/触发器路，见 §6）。
- 14-house fanout 策略本身（M2 见 §6 规格）。

---

## 3. 指纹格式（H1FP1）

### 3.1 字面格式

```
H1FP1|<tier>|<load_hash12>
```

| 字段 | 含义 | 约束 |
|---|---|---|
| `H1FP1` | 方案 ID + 版本 | 固定；升版改字节规则时递增为 H1FP2 |
| `<tier>` | `U0050` / `U0200` / `U0800` | 4 位零填充，与文件名 `[2]0LoadBench_<tier>_H1.yrm` 一致 |
| `<load_hash12>` | sha256 前 12 hex | 小写；覆盖**预置负载正文**，不含指纹字段本身 |

### 3.2 哈希载荷（canonical）

对图 INI 的 `[Units]` `[Infantry]` `[Structures]` `[Aircraft]` 四段：

1. 每行 `id=Body` 去掉 `id`，保留 `Body`（逗号字段原样）；
2. 规范串 = `Section|Body`（`Section` 为段名）；
3. 全部规范串 **按字典序排序** 后以 `\n` 连接，UTF-8 编码；
4. `sha256(payload).hexdigest()[:12]`。

性质：

- **不随行号 id 重排变化**（只看 Body）。
- **不含** `Name` / `H1Tier` / `H1Fingerprint` / 段头 ⇒ 无循环依赖（写入指纹后重算应不变，生成器内 `assert final_h == load_h`）。
- 负载行任一字段（owner/type/health/X/Y/facing/mission…）变化 ⇒ hash 变。

### 3.3 嵌入位置

| 位置 | 例 | 用途 |
|---|---|---|
| `[Basic] H1Fingerprint=` | `H1FP1\|U0050\|26c371932de7` | 机器读回校验（主通道） |
| `[Basic] H1Tier=` | `U0050` | 快速过滤/断言档位 |
| `[Basic] Name=` | `[2] 0LoadBench U0050 H1 fp:26c371932de7` | UI/截图/遥测可见短标 |

当前三档实测指纹 `[实证]`（`python tools/h1_map_fingerprint.py verify`）：

| 档位 | total objects | unique cells | max_stack | fingerprint |
|---|---|---|---|---|
| U0050 | 350 | **350** | **1** | `H1FP1\|U0050\|26c371932de7` |
| U0200 | 1400 | **1400** | **1** | `H1FP1\|U0200\|4bf2d6692bd5` |
| U0800 | 5600 | **5600** | **1** | `H1FP1\|U0800\|1189b6b550ff` |

旧图（备份）同一算法的 hash 为 `4b8c8af9210b` / `734cbc26717c` / `57e0157ed7cd` —— 与新图不同（cell 布局变了），可用于「装的是旧图还是新图」判别。

### 3.4 读回校验（脚本可复算）

```powershell
python tools\h1_map_fingerprint.py verify                  # 默认 pristine/H1
python tools\h1_map_fingerprint.py verify out\loadbench    # 指定路径
python tools\h1_map_fingerprint.py compute out\re_work\h1_map_fix\backup_pre_fix
```

`verify` 硬门禁（任一失败即 FAIL）：

1. `H1Fingerprint` 存在且 scheme=`H1FP1`；
2. 声明 hash == 由对象行重算 hash；
3. `H1Tier` == 指纹内 tier == 文件名 tier（若文件名含 U####）；
4. `unique_cells_xy == total_objects`；
5. `max_cell_stack <= 1`。

报告：`out/re_work/h1_map_fix/fingerprint_report.json`。

---

## 4. cell 互斥修复前后对照 `[实证]`

可复算：`out/re_work/h1_map_fix/cell_exclusion_proof.json`（生成器 `build_report.json` 亦含同断言）。

| 档位 | objects | unique before | max_stack before | unique after | max_stack after | unique==total |
|---|---|---|---|---|---|---|
| U0050 | 350 | 50 | 7 | **350** | **1** | yes |
| U0200 | 1400 | 200 | 7 | **1400** | **1** | yes |
| U0800 | 5600 | 800 | 7 | **5600** | **1** | yes |

几何策略（新）：

- 100×100 图；中线两侧各留 4 列过道 + 边距 6；
- 偶数序 house 取西侧 pool、奇数序取东侧 pool 的**私有连续块**（row-major）；
- 2 个玩家槽仍分居东西，对冲视觉保留；14 house 条目在图内互不重叠。

**注意（口径）**：`unique==total` 证明的是**图内**互斥。引擎侧 1 cell/台的 `Put` 规则（步兵 subcell 仍可 3 台同格）不由本门禁保证；本次每对象仍独占 cell，故引擎可落地上限回到 `min(active_house_rows, free_cells)`，设计上 ≈2×per_house（激活 2 槽）或 14×per_house（全 house 激活）。

---

## 5. 复测协议建议（真机 / 对拍，P0）

> 本节是给遥测与 A/B 对拍的**建议口径**，不涉及本次真机执行。

### 5.1 A3 误选签名门禁（升级为「指纹门禁」）

| 步骤 | 动作 | 判据 |
|---|---|---|
| S1 | 开局后回读当前场景 `Name` / `H1Fingerprint`（UI 或存档/scenario 读回） | 必须等于**目标档**指纹；否则直接判「进错图」，**不计入 units_seen** |
| S2 | 若读不到 `H1Fingerprint`（旧图/装载失败） | 判「装载物版本错」，用旧图 hash 表（§3.3）或文件 sha256 对照 |
| S3 | S1 通过后再比 units_seen | 落入 §5.2 delta 带才计数 |
| S4 | 误选签名保留为兜底 | `segD_run.py` 的 178/713/2852 仍作副证；与指纹冲突时以指纹为准 |

旧事故（三轮皆 ≈713）在 S1 即被拦：U0050 轮读回 `H1Fingerprint` 若为 `...|U0200|...`，立即出局。

### 5.2 A2 delta 口径

```
delta = units_seen(H1_tier) - units_seen(空图对照)
期望   delta ∈ [target*0.8, target*1.2]
```

- 空图对照 = 无 `[Units]/[Infantry]` 的同尺寸 skirmish 图（仍保留 waypoints）；
- **先过 S1 指纹**，再算 delta；
- 目标值 `target` 取**设计 2 槽量**（50/200/800）；若走 M2（§6）则取 `per_house` 全量。

### 5.3 A5 国家对矩阵（锁开局兵力）

| 对照 | 玩家 | 敌 | UnitCount | Credits | 用途 |
|---|---|---|---|---|---|
| N1 | Americans | Russians | 0 | 0 | 基线（去 GenerateStartingUnits 噪声） |
| N2 | Americans | Random | 0 | 0 | 敌国效应 |
| N3 | Russians | Random | 0 | 0 | 玩家国效应 |
| N4 | Random | Random | 0 | 0 | 旧 713 事故组 |
| N5 | Americans | Russians | 10 | 10000 | 复现 ra2bench 现状 |

每格 3 轮；先指纹后计数。N1–N4 的 delta 互比 = 国家主效应；N5−N1 = 开局兵力档效应。

### 5.4 回归断言（离线，已可跑）

```powershell
python tools\bench_maps\build_bench_maps.py     # 重建 + 写前 assert
python tools\h1_map_fingerprint.py verify      # 读回校验
```

两条都 exit 0 才算地图侧闭环。**在此闭环 + S1 真机复测完成前，H1 前提的性能 ROI 保持冻结**（ZC-9B 红线延续）。

---

## 6. M2 规格：负载挂 Neutral/Special（本次不改图）

### 6.1 动机

H1-FANOUT §2.2：美蘇预置行 **0 条** 进 `mobile_count`（Neutral/Special 亦 0）。即使 cell 互斥修复，玩家 House 的 owner 匹配仍可能整层丢弃。把**全部目标负载**写到 **必然创建** 的 `Neutral`（或 `Neutral+Special`）上，与选国彻底解耦。

### 6.2 目标语义

| 项 | 现行 14-house fanout | M2 Neutral 承载 |
|---|---|---|
| 图内条目 | 14 × per_house | `target`（=2×per_house）全部 owner=`Neutral` |
| 激活 2 槽时 units_seen ≈ | 2×per_house + SU（若 owner 命中） | **target + SU**（与选国无关） |
| 与档位标度 | 依赖 owner 实例化 | 条目数即负载（若 Neutral 实例化） |
| 风险 | owner 匹配失败 | Neutral 被 Passive 吞掉（U-MB-1） |

### 6.3 改动点（供下波次实施）

1. `build_bench_maps.py`：`houses_for_rows = ["Neutral"]` 或 `["Neutral", "Special"]`；`per_house` 改为 `total_units`（或 `total_units` 分给 1–2 个 house）。
2. cell 分配仍走 `allocate_disjoint_slots`（单 house 时 n_houses=1，整图一份）。
3. 指纹**继续写**（tier+hash 不变）；`H1Tier` 不变。建议 fingerprint scheme 升为 `H1FP1|U0050|hash|N` 或新键 `H1LoadHouse=Neutral`，避免新旧图混淆。
4. 验收改走 A2 delta 带 `[target*0.8, target*1.2]`（§5.2），**不再**用「2 槽 fanout」绝对值。
5. 先做 **U0050 单档试点** + 指纹 + delta，通过后再滚 U0200/U0800。

### 6.4 开放风险

- Neutral/Special 在遭遇战是否创建 HouseClass、是否消费 `[Units]` 行：`[待实测]`（U-MB-1）。
- `MultiplayPassive` 规则可能阻止落兵：需用指纹进图后看 `mobile_count` 是否 ≈ target。
- 若 Neutral 也不实例化，则只剩 M4（owner=`Multi1..Multi8`）/ M3（触发器 TeamType）两条路（H1-FANOUT §4.1）。

---

## 7. 产物清单

| 路径 | 说明 |
|---|---|
| `tools/bench_maps/build_bench_maps.py` | 生成器（M1 互斥 + M5 指纹 + 备份） |
| `tools/h1_map_fingerprint.py` | 指纹计算/读回校验 CLI |
| `out/loadbench/pristine/H1/[2]0LoadBench_U{0050,0200,0800}_H1.yrm` | 修复后 3 档（canonical） |
| `out/loadbench/[2]0LoadBench_U{0050,0200,0800}_H1.yrm` | 同内容工作副本 |
| `out/re_work/h1_map_fix/backup_pre_fix/*` | 旧图字节 + MANIFEST.sha256 + SOURCE.txt |
| `out/re_work/h1_map_fix/build_report.json` | 生成器自检（含 assert 结果） |
| `out/re_work/h1_map_fix/fingerprint_report.json` | 读回校验报告 |
| `out/re_work/h1_map_fix/cell_exclusion_proof.json` | 前后 cell 证明 |
| `docs/re/h1_map_fingerprint.md` | 本文件 |

复算：

```powershell
python tools\bench_maps\build_bench_maps.py
python tools\h1_map_fingerprint.py verify
```

---

## 8. §九草稿（供下游台账/收口直接粘贴）

> ### 九、H1 地图 cell 互斥修复与进图指纹（H1-MAPFIX）
>
> **9.1 现象**：H1-FANOUT 查明生成器同奇偶 house 共用 slots ⇒ 三档全部 7× 同格堆叠（唯一 cell=50/200/800）；且图无进图指纹，随机轮 units_seen 713–723 与 U0200 误选签名同带，无法证明进了本档图。
>
> **9.2 修复** `[实证]`：
> 1. **M1**：`allocate_disjoint_slots()` 每 house 私有 cell 带，写盘前 `assert unique==total`。结果：U0050/U0200/U0800 唯一 cell = **350/1400/5600**，max_stack=**1**（旧 50/200/800、7×）。
> 2. **M5**：`[Basic]` 写入 `H1Tier` + `H1Fingerprint=H1FP1|<tier>|<hash12>`，`Name` 带 `fp:<hash12>`；`tools/h1_map_fingerprint.py` 读回重算校验，三档 PASS。指纹 hash = sha256(排序后的 `Section|Body` 对象行)[:12]，不含指纹字段本身。
> 3. 旧图冻结于 `out/re_work/h1_map_fix/backup_pre_fix/`（含 sha256 MANIFEST）。
>
> **9.3 验收口径**：A3 升级为**指纹门禁**（先核 `H1Fingerprint` 档位再计数）；A2 delta=`units_seen(H1)−units_seen(空图)`∈[0.8T,1.2T]；A5 国家对 2×2 + UnitCount=0 对照。M2（负载挂 Neutral）只出规格待试点。
>
> **9.4 证据**：`out/re_work/h1_map_fix/{build_report.json,fingerprint_report.json,cell_exclusion_proof.json,backup_pre_fix/}`；`tools/bench_maps/build_bench_maps.py`；`tools/h1_map_fingerprint.py`；本文件 §2–§4。
>
> **9.5 待实测**：① 真机读回指纹（防再发三轮皆 U0200）；② 国家对矩阵 + `UnitCount=0`；③ Neutral/Special 预置行是否实例化（M2 试点）；④ 修复后 units_seen 是否随 50/200/800 标度。
>
> **9.6 红线**：机制未闭环前 **H1 前提的性能 ROI 继续冻结**（ZC-9B 延续）。

---

## 9. 红线与合规

| 红线 | 触及？ |
|---|---|
| 改 `ra2render/**` / `ra2youli/**` / `ra2bench/**` / `gamemd.exe` | **否** |
| 改台账 `REVERSE_ENGINEERING_AND_PATCHES.md` / `ARCHITECTURE_ATLAS*` | **否** |
| 启动游戏 / 注入 / 写引擎内存 | **否**（纯离线生成 + 解析） |
| 未备份覆盖旧 H1 图 | **否**（backup_pre_fix 已冻结） |
| 超 M 轨写域 | **否**（见文首写作用域） |

---

## 10. 一句话给下游

> H1 三档图已从 7× 同格堆叠修成 **唯一 cell=条目数、max_stack=1**，并在 `[Basic]`/`Name` 落了 **H1FP1 指纹**（tier+内容 hash），`tools/h1_map_fingerprint.py` 可读回对拍；旧图在 `out/re_work/h1_map_fix/backup_pre_fix/`。下一步用「指纹门禁 + A2 delta + A5 国家矩阵」真机复测，通过前 H1 性能 ROI 仍冻结；Neutral 承载见 §6 规格。
