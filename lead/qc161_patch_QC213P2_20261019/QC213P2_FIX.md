# QC213P2 探针扩展报告 · 败北触发链定谳探针（qc151_trip_qc213p2.py）

- 日期：2026-10-19
- 对象：`lead\qc151_u0400_trip\qc151_trip.py`
- 改前锚（现行）：sha256 `37c1d4351cdf7033306a76892fcc19d2f7e182176e0205e1e67cadfa01470ad0`（381,363 B / LF 6,967 / CR 0）——**起跑前实测确认在锚**。
- **产物（补丁副本）**：`qc151_trip_qc213p2.py`，sha256 `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`（399,508 B / LF 7,291 / CR 0）。
- 补丁副本制：**live 文件零改动**（改前改后锚 sha 均为 `37c1d435…`，见 RECEIPT §1）。
- 判读依据：`spawnfix9_freeze_20261019\WIPE_TRIGGER_ANALYSIS.md` §5.1 探针表 + 「附：关键地址速查」（VA→file_off 一律 VA−0x400000，逐项在速查表核对）。

---

## 1. 探针节（§10.8d · 嵌套哨兵 `>>> QC213P2-BEGIN probe … <<< QC213P2-END probe`）

纯新增只读节；三块哨兵（probe / arm / finalize）与 QC213 的架构同构。删三块 = 锚 `37c1d435…` **逐字节还原**（实测，§4-④）。

### 1.1 地址表（VA / file_off 成对，速查表核对）

| 量 | VA | file_off | 速查表出处 |
|---|---|---|---|
| RulesClass | `0x008871E0` | `0x004871E0` | 速查「RulesClass」 |
| RulesClass+0x8E8（Arr8E8） | `0x008872C8` | `0x004872C8` | 速查「RulesClass+0x8E8（败北判据第四项数组）」 |
| ShortGame 全局 | `0x00A8B262` | `0x0068B262` | 速查「ShortGame 全局」 |
| SessionClass | `0x00A8B230` | `0x0068B230` | 速查「SessionClass」 |
| SessionClass+0x14B6 | `0x00A8C6E6` | `0x0068C6E6` | 报告 §1.2（`0x0052D1F5` 拷贝源） |
| HouseClass::Array Items | `0x00A8022C` | `0x0068022C` | 既有 QC213（§10.8b） |
| HouseClass Count | `0x00A80238` | `0x00680238` | 同上 |
| CurrentFrame（锚点） | `0x00A8ED84` | `0x0068ED84` | 既有 `MEASURE_CURRENT_FRAME_VA` |

读取全部走 `_rpm_u32_qc213p2_base`（= QC213 包装 = 锚 `_rpm_u32`，RPM 只读、失败返 None 不抛）；u8 一律 4 字节对齐 dword + 移位取字节。

### 1.2 P1 · RulesClass+0x8E8 解引链（判据第四项）

按 `0x004F8F4C → 0x004F8F54 → 0x004F8F5A → 0x004F8F61` 逐指令解引，**每一级单独落 rec**（任何一级失败即该级 `null`，下级随之 `null`，不写 0）：

| 级 | 读法 | readings 键 | 预测（§5.1 P1） |
|---|---|---|---|
| 1 | rd32(`0x008871E0`) | `p{frame}_qc213p2_p1_rules` | 非 0（RulesClass 指针） |
| 2 | rd32(rules+0x8E8) | `..._p1_arr8e8` | 非 0（数组基） |
| 3 | rd32(arr+0x8) = Arr8E8[1] | `..._p1_elem1` | **NULL** |
| 3b | `elem1 == 0` | `..._p1_elem1_null` | **True** |
| 4 | rd32(elem1+0xDF8) | `..._p1_idx_df8` | elem1 为 NULL 时 `null`（不可测） |
| 5 | 每屋 `[list@H+0x5550+0x4][idx]`（idx < `[list+0x8]`） | `p{frame}_qc213p2_h{i}_p1_c5550_idx` | **0** |
| 5b | `idx >= [list+0x8]` | `..._h{i}_p1_idx_ge_cap` | 视 idx 而定；True ⇒ 引擎 `0x49FAE0` 扩容清零尾部 ⇒ 计数 0 |
| 辅 | rd32(H+0x5560) = list@0x5550 Count | `..._h{i}_p1_c5550_count` | 与 QC213 `c5560` 同址互核 |

**判据映射**：§1.3 条件表达式末项 `(Arr8E8[1]==NULL ∨ Count(list@H+0x5550[idx])==0)`。`p1_elem1_null=True` 即该项**恒真、不参与判负**，与「f300 时 c5588=22 仍被判负」自洽；若 `elem1_null=False` 且 `p1_c5550_idx>0`，则 f300 判负无法由常规判定解释，须重开 §1.3 分析。

### 1.3 P2 · 每屋 HouseTypeClass+0x1A6

`rd32(H+0x34)` → HouseTypeClass* → 对齐取 `+0x1A6` 字节（`0x004F8EAC/0x004F8EAF` 门）。

| readings 键 | 预测（§5.1 P2） |
|---|---|
| `p{frame}_qc213p2_h0_ht1A6` | **0** |
| `..._h1_ht1A6` | **0** |
| `..._h2_ht1A6` | **1** |
| `..._h3_ht1A6` | **1** |

`=1` 即 `0x004F8EB7 jne` 跳过该屋（h2/h3 免疫的结构原因）。`null` = `htc34` 读失败或为 0（不可测，不写 0）。

### 1.4 P3 · ShortGame 全局 vs 会话副本

| readings 键 | 读法 | 预测（§5.1 P3） |
|---|---|---|
| `p{frame}_qc213p2_p3_shortgame_glob` | byte@`0x00A8B262` | **0**（ShortGame=no） |
| `..._p3_shortgame_sess` | byte@`[SessionClass+0x14B6]` | **0** |
| `..._p3_equal` | 两者相等 | **True**（恒等） |

`p3_equal=False` ⇒ `0x52D1F5` 拷贝时序有变，分支选择（`0x4F8EC4 je` vs `0x4F8EC6`）需重勘。

### 1.5 P5 · 清洗循环前置位

`rd32(SessionClass)` 取 dword，`byte[1] = (dword>>8)&0xFF`（即 `0x4FC16C` 的 `test ah,8`）。

| readings 键 | 预测（§5.1 P5） |
|---|---|
| `p{frame}_qc213p2_p5_sess_byte1` | 原值照记 |
| `..._p5_clean_bit` | **0x08** |
| `..._p5_clean_set` | **True** |

`False` ⇒ `0x4FC179-0x4FC1AE` 清洗不执行，f373 的 22 步兵清零需另找路径。

### 1.6 P4 · 逐帧阶梯（早闩 + f250-f450）

- **阶梯常量可配**：`QC213P2_LADDER_SRC = (10,) + tuple(range(250, 451))`（源 202 帧）；`_qc213p2_ladder_effective()` 去重升序后按 `QC213P2_LADDER_CAP = 64` **截断**。
  - 本版实际生效：`QC213P2_LADDER = (10, 250, 251, …, 312)`（64 帧），`QC213P2_LADDER_DROPPED = 138`（实测，§4-③）。
  - 截断事实随 arm 行（`ladder_dropped`/`ladder_src_n`/`ladder_n`）与 arm note 落 rec，finalize 行复记。
  - **⚠ 交接口径**：默认 64 帧帽使逐帧窗只覆盖到 f312，**不含 f313-f450**。要覆盖到 f450 需把 `QC213P2_LADDER_SRC` 收窄（例如 `(10,) + tuple(range(313, 451))`，139 帧仍超帽，需再裁）或调高 `QC213P2_LADDER_CAP`——两者都是一行常量改动，**未在本补丁内擅改**（本卡要求「不上限爆炸」优先）。
- **早闩（frame≈10）**：`early_done=False` 时**首拍必落**快照（`kind="early"`），键=实际帧号。若首拍帧号 ∈ 阶梯集则同时计入 `latched`（去重不重复快照）。
- **逐帧档**：`frame ∈ QC213P2_LADDER_SET` 且未闩 ⇒ 落 `kind="latch<帧>"`；同帧不重采。
- **每帧字段**（`_QC213P2_HOUSE_FIELDS`，每屋 7 项）：`x2F0`/`c5574`/`c5588`/`def1F5` + `id30`/`isHuman1EC`/`htc34`；另加 `ht1A6` 与 P1 三项 ⇒ 每屋 11 项。
- **判据（§5.1 P4）**：h1 的 `c5574` 归零点落在 (270, 300]；`def1F5` 在**同帧或紧随其后**置 1。若 `def1F5` 领先于 `c5574` 归零 ⇒ 存在另一判据（ShortGame=yes 分支被意外选中）。

### 1.7 采样架构与门控

- **挂载**：`_rpm_u32` 同名包装第二层——本块先存 `_rpm_u32_qc213p2_base = _rpm_u32`（即 QC213 包装），再重定义 `_rpm_u32`；调用链 `P2 包装 → QC213 包装 → 锚`（实测，§4-③）。off ⇒ 逐字直通（零行为差异）。
- **激活**：**不新增 CLI 开关**；arm 块条件 `getattr(args,"measure",0) and _nav_verdict=="OK"`（与 QC213/measure 簇同源）。缺省 `--measure=0` ⇒ 零执行、零 rec 行。
- **去重**：`latched` 字典（键=帧号字符串），每档只采一次；`latched_n` 计数。
- **冻结看门**：帧钟不变持续 ≥`QC213P2_FREEZE_S`(2.0 s) ⇒ 补 `frozen_final` 快照后 `done=True`（与 QC213 同纪律）。
- **错误帽**：`QC213P2_ERR_CAP=3`；`read_fail`/`bad_vector`/`exception` 只记不抛，达帽 `done=True`。
- **枚举哨兵**：`items==0` 或 `count>64` ⇒ `bad_vector`（本轮零 house 行）；`items/count` 读失败 ⇒ `read_fail`。预期 `count=4`。

### 1.8 readings 键表（组=QC213P2）

- 快照头：`p{frame:06d}_qc213p2_kind`（`early` / `latch<帧>` / `frozen_final`）、`p{frame:06d}_qc213p2_meta_count`
- P1：`p1_rules` / `p1_arr8e8` / `p1_elem1` / `p1_elem1_null` / `p1_idx_df8` / `h{i}_p1_c5550_count` / `h{i}_p1_c5550_idx` / `h{i}_p1_idx_ge_cap`
- P2：`h{i}_ht1A6`
- P3：`p3_shortgame_glob` / `p3_shortgame_sess` / `p3_equal`
- P5：`p5_sess_byte1` / `p5_clean_bit` / `p5_clean_set`
- P4：`h{i}_x2F0` / `h{i}_c5574` / `h{i}_c5588` / `h{i}_def1F5` / `h{i}_id30` / `h{i}_isHuman1EC` / `h{i}_htc34`
- 探针级：`qc213p2_probe_error`、`qc213p2_probe_armed`（MEASURE 组）、`qc213p2_probe_final`（MEASURE 组）
- 帧号 = **实际帧号 6 位零填**（非阶梯值；早闩可能是 `p000009_` 等）

### 1.9 与 QC213 的关系（不互相覆写）

- QC213 三点闩锁 `QC213_LATCH_FRAMES=(300,600,1800)` **原样保留**（实测仍为 `(300,600,1800)`），作为交叉复核源。
- 本探针使用**独立的** `_QC213P2_PROBE` 与独立阶梯，不写 `_QC213_PROBE["latch_frames"]`；`--probe-frames` 阶梯仍只作用于 QC213。
- 同帧下 QC213 与 QC213P2 各自落行，键前缀不同（`p{frame}_h{i}_…` vs `p{frame}_qc213p2_h{i}_…`），无冲突。

## 2. 防御性收口（真机纪律）

- `_qc213p2_tick` 整体 try/except ⇒ 内部异常记 `probe_error{kind:"exception"}` 并收口，**绝不抛**（measure 循环零扰动）。
- 包装器对基础读的契约外异常同样收口（记 error、返回 None）；off 时逐字直通（异常语义与锚一致）。
- 读失败不抛（`_rpm_u32` 既有契约）；探针全走只读原语族；零写入、零注入、零新增 sleep、零新开句柄（复用 measure 句柄）。
- 未测值一律 `null`（Recorder 纪律：不可测写 null，不写 0）。

## 3. 差异清单（hunk）

| hunk | 位置（补丁副本行） | 行数 | 内容 |
|---|---|---|---|
| A | 3263-3548 | 286 | QC213P2 probe 节（紧跟 `# <<< QC213-END probe` 之后） |
| B | 6910-6927 | 18 | QC213P2 arm（紧跟 `# <<< QC213-END arm` 之后） |
| C | 6976-6995 | 20 | QC213P2 finalize（紧跟 `# <<< QC213-END finalize` 之后） |

**差异 = 且仅 = 上述三块**：`difflib` 全文件差分实测 `ADDED_LINES=324 / REMOVED_LINES=0`（3 块内容 286+18+20=324 行），无修改行、无删除行、无重排行。

## 4. 自测记录（全部在 `%TEMP%`，零落仓库）

| 项 | 结果 | 证据 |
|---|---|---|
| ① `py_compile` | **PASS** | `py_compile.compile(..., cfile=%TEMP%\qc213p2_final_*\x.pyc, doraise=True)` ⇒ 390,463 B |
| ② `argparse --help` 冒烟 | **PASS** | rc=0；stdout 与锚**逐字节相同**（`stdout_identical True`）；`--probe-frames`/`--measure` 均在 |
| ③ 模块级 importlib exec + 常量 | **PASS** | 阶梯 64 帧 / 丢弃 138；`on=False`；地址与 file_off 逐项等于 §1.1 |
| ④ 反向重建 | **PASS** | 删 3 块 ⇒ 381,363 B / `37c1d435…` **MATCH True** |
| ⑤ 合成地址空间回放（P1/P2/P3/P5/P4） | **PASS 22/22** | 逐值断言（§5） |
| ⑥ 闩锁/早闩/冻结/错误帽/off 直通 | **PASS** | 5 项场景（§5） |
| ⑦ 禁止面扫描 | **PASS** | 三块内 `WriteProcessMemory`/`time.sleep`/`OpenProcess`/… 全为 0 |

**未做**：真机趟（本卡明确不做）。真机数值（P1-P5 实际读数）**未验证**，本件只证明 instrument 正确，不预设真机结果。

## 5. 合成回放明细

合成地址空间（`%TEMP%` 内 importlib exec 真模块 + 猴子补丁 `_rpm_u32_qc213p2_base` 注入内存）：

- P1：4 级解引逐级命中；`Arr8E8[1]=0x12350000`、`idx=3`、`h1` 的 `[list+0x4][3]=5`、Count=22 ⇒ 7/7 PASS。
- P2：h0/h1 `+0x1A6=0`、h2/h3 `=1` ⇒ 4/4 PASS。
- P3：glob=0、sess=0、equal=True ⇒ 3/3 PASS。
- P5：byte1=0x08、bit=0x08、set=True ⇒ 3/3 PASS。
- P4：h1 `x2F0=0`/`c5574=242`/`c5588=92`/`def1F5=0`、`meta_count=4` ⇒ 5/5 PASS。
- 闩锁：帧序 7→10→249→250→251→252→252→300→450 ⇒ `early` 于 f7；latched={10,250,251,252,300}（300 在截断窗内）；252 重拍不重采；非阶梯帧（313）零行。
- 冻结：帧钟不变 5 s ⇒ `frozen_final` + `done`。
- 错误帽：`count=100` 连续 5 拍 ⇒ error 行**恰 3**（帽）+ `done=True`。
- off：`_rpm_u32` 直通锚、返回值 42 原样、零快照。

**回放中发现并修正的设计点（诚实申报）**：初版 P3 全局读用了 `_qc213p2_u8(handle, 0x00A8B262, 0)`——基址未对齐，实际会读 `0x00A8B260` 并取 byte0（错位）。合成回放报 FAIL 后改为 `_qc213p2_u8(handle, VA & ~3, VA & 3)`，重跑全绿。此修正使读数符合「对齐 dword + 移位」纪律，也避免跨页边界风险。

## 6. 运行口径（交接）

```
python qc151_trip_qc213p2.py … <既有必选参数> --measure 1
```
- readings 判读：
  - P1：`p1_elem1_null` 全帧应为 `True`；若 `False` 且 `h1_p1_c5550_idx>0` ⇒ 判据理解需重开。
  - P2：`h2_ht1A6`/`h3_ht1A6` 应为 1（免疫门）；h0/h1 为 0。
  - P3：`p3_equal` 应恒 True 且 glob=sess=0。
  - P5：`p5_clean_set` 应恒 True。
  - P4：看 `h1_c5574` 首次归零帧与 `h1_def1F5` 首次为 1 的帧序关系；`early` 快照（f≈10）看 h1 是否开局即 `c5574=0`（零出生签名）。
- 未闩档（如 `p000450` 缺）= measure 窗内未达该帧号或已被 64 帧帽截断（看 arm 行 `ladder_dropped`），**非失败**。
- `frozen_final` 出现 = 帧钟冻结 ≥2 s（战局终/卡）。
