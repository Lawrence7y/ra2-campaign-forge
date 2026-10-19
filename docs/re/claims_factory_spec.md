# Claims Factory Spec — R-CLAIMS-FAC

工程化续作：T4 `R-VA-CLAIMS` 的可执行规则固化。
基线：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`。
只读静态复算，不启动游戏、不改二进制。

产出目录（本 spec 的可执行附件）：`out/re_work/re_sprint/R_claims_fac/`

| 文件 | 职责 |
|---|---|
| `window_norm.py` | 规则 1：入口窗宽归一 + 67 处假冲突合并 |
| `claim_schema.json` / `claim_schema.py` | 规则 2：claims 文本/JSON schema 与校验器 |
| `scan_filters.py` | 规则 3：E8 rel32 / 数据段误匹配机械过滤器 |
| `tests/fixtures_t4.json` | 规则 3 最小测试集（从 T4 样本抽取） |
| `tests/test_*.py` | 三套单元测试 |
| `factory_batch.py` | 规则 4：下一波 400 条悬空 VA 批量补证流水线 |

---

## 0. 背景与 T4 结论（输入约束）

T4（`out/re_work/re_sprint/R_va_claims/`）在 482 条悬空 VA 上抽样 80 条，固化三条工程问题：

1. **65 条 BSS 无 raw**：`.data` VirtualSize `0x367BE4` > SizeOfRawData `0x6C000`，
   raw 覆盖 VA 上界 `0x0087E000`，其上无文件字节。本体 hex 断言不可做，
   必须改「引用点指令断言」（`bss_ref`）或「区域断言」（`bss 0xVA = virtual`）。
2. **67 处假冲突**：与既有 claims 的字节差异 **全部** 是入口窗宽不一致
   （observed width-sets：`(8,16)×51`、`(4,16)×9`、`(1,8,16)×5`、`(4,8,16)×2`），
   字节前缀完全一致；`hard_byte_conflicts = 0`。窗宽归一后全部可合并。
3. **绝对 dword 扫描误匹配**：`struct.pack('<I', VA)` 全镜像 `find()` 会命中
   E8/E9 rel32 位移域、以及 .text 内 imm32 的**巧合字节**；
   反向地，线性扫 `E8` 建调用图会把 imm32 里的 `E8` 字节误判为 `call`。

---

## 1. 入口窗宽归一规则（Window Normalization）

### 1.1 标准入口窗

```
W_std = 16 字节
W(va)  = raw[va : va + min(16, raw_available(va))]
```

- `raw_available`：按节表段映射
  `off = SizeOfRawData 边界内可读长度`；BSS/虚拟段为 0。
- **禁止**把窗宽写成 4/6/8 来迁就历史 claims；历史窗是 `W_std` 的前缀。
- 可选截断（prologue 边界）：若 16B 内出现完整函数出口
  （`C3` / `C2 iw` / `C9 C3`）且该出口字节序列可被 capstone 在 VA 处线性解出，
  则 `W(va)` 可截断到出口指令末尾，但 **最少 4 字节**；无 capstone 时一律 16B。

### 1.2 归一与合并算法（可执行，见 `window_norm.py`）

```
normalize_hex(h) -> '53 57 8B …'   # 去杂空白、大写、按字节对齐
norm_bytes(h)    -> ['53','57','8B',…]

is_prefix(a, b)      # 较短者字节序列 == 较长者前 min(len) 字节
first_diff(a, b)     # 返回 (idx, ba, bb)；仅长度不同则 idx=min_len, 'EOF', 'EOF'

classify_pair(a, b):
    if a == b                         -> IDENTICAL
    if is_prefix(a, b)                -> WINDOW_VARIANT   # 假冲突，可合并
    else                              -> BYTE_CONFLICT    # 真冲突，不得合并
```

**合并策略（67 处假冲突）**：

1. 同 VA 多条 claims 全部 `normalize_hex`；
2. 若两两均为 `IDENTICAL | WINDOW_VARIANT` → 合并为 **最长窗** 一条；
   工厂输出强制重采到 `W_std=16`（有 raw 时）；
3. 只要出现一对 `BYTE_CONFLICT` → 该 VA 进 `conflicts` 队列，禁止静默合并，
   留人工/二次复算裁决；
4. 合并结果记录 `merged_from`（lib 路径列表）与 `window_widths`（历史宽度集合）。

**判定不变量**：`BYTE_CONFLICT` 当且仅当存在下标 `i < min(len_a, len_b)` 使
`a[i] != b[i]`。长度差本身永远不是冲突。

### 1.3 T4 实测

- `conflicts_final.prefix_length_only = 67`，`hard_byte_conflicts = []`。
- 归一后 67/67 → `WINDOW_VARIANT`，0 真冲突。见
  `out/re_work/re_sprint/R_claims_fac/out_window_norm_report.json`。

---

## 2. BSS / 引用点断言 Schema

### 2.1 断言类型

| type | 含义 | 可离线复算 |
|---|---|---|
| `raw` | VA 处有文件字节，断言 `entry_hex` | 是 |
| `bss_ref` | VA 无 raw，断言**引用它的 .text 指令字节** | 是（锚点指令可复算） |
| `bss_region` | VA 落在「虚拟存在、无 raw」区域 | 是（节表推导） |

### 2.2 文本格式（兼容 `tools/audit_bytes.py`）

```
# raw
0xVA = HEXBYTES                  # meta… | type=raw | grade=…
# bss 区域
bss 0xVA = virtual               # meta… | type=bss_region | grade=…
# bss 引用点（锚点指令 hex 断言 + 反向指向）
0xSITE_VA = HEXBYTES             # bss-xref -> 0xBSSVA | type=bss_ref | grade=…
```

等级取值：`[实证]` | `[推演]` | `[待实测]`（与 T4 三级证据等级一致）。

### 2.3 JSON 记录（`claims.jsonl`，一行一条）

```json
{
  "va": "0x0087F7E8",
  "type": "bss_ref",
  "grade": "[待实测]",
  "entry_hex": null,
  "window_width": 0,
  "segment": ".data(virtual)",
  "file_offset": null,
  "kind": "bss-global",
  "anchor": {
    "site_va": "0x0040D190",
    "hex": "B9 E8 F7 87 00",
    "asm": "mov ecx, 0x87f7e8",
    "covers_abs_at": "0x0040D191",
    "op": "mov",
    "form": "imm32"
  },
  "xref": {"n_call": 0, "n_jmp": 0, "n_abs_text": 3700, "n_abs_data": 0},
  "symbol_guess": "SuperWeaponClass 状态机/发射链",
  "merged_from": [],
  "window_widths": [],
  "notes": []
}
```

字段约束（JSON Schema 见 `claim_schema.json`）：

- `va`：`^0x[0-9A-F]{8}$`（大写定宽）。
- `type=raw` ⇒ `entry_hex` 必填且 `window_width = len(entry_hex.split())`，`anchor` 可空。
- `type=bss_ref` ⇒ `anchor` 必填：`site_va` + `hex`（≥1 字节）+ `covers_abs_at`
  （`site_va ≤ covers_abs_at < site_va+len(hex)`，且该 4 字节序列 == `pack(va)`）。
- `type=bss_region` ⇒ `entry_hex=null`，`anchor` 可空。
- `grade`：`raw` 有标准序言/调用点/ret 桩/PE 魔数 ⇒ `[实证]`；
  仅图谱推断 ⇒ `[推演]`；`bss_ref` 锚点本身可 `[实证]`，但**对象本体**仍标
  `[待实测]`（在 `notes` 里区分 `anchor_grade` 与 `body_grade`）。

### 2.4 BSS 锚点选取规则

1. 在 .text 内取**指令边界**上、指令立即数/位移覆盖 `pack(va)` 的站点
   （`fix_indirect_p2.py` 的 `find_aligned_site` 语义）；
2. 优先带名字的 5 字节形：`B8–BF imm32`、`A1/A3 abs32`、`C7 /0 abs32`、
   `05/0D/15/1D/25/2D/35/3D imm32`、`68 imm32`、`8D /r + abs`；
3. 锚点 hex 必须整体可离线从 `gamemd.exe` 复算；一个 BSS VA 至少 1 条锚点，
   高 xref（≥100）建议 2 条（读点+写点各一）。

---

## 3. 扫描过滤器规格（Scan Filters）

适用对象：绝对 dword 扫描（`xref_abs.py` 语义）与 E8/E9 调用图扫描。

### 3.1 机械规则

| ID | 名称 | 规则 |
|---|---|---|
| F1 | `E8-in-imm` | 线性扫 `E8`/`E9` 时，若该字节落在某已知 imm32 指令的操作数域内（前驱 opcode ∈ `B8–BF A1 A3 C7 68 05 0D 15 1D 25 2D 35 3D 69 81 8D` 且 imm 覆盖该字节），丢弃该「call/jmp」候选 |
| F2 | `rel32-coincide` | `find(pack(VA))` 命中偏移 `i`：若 `i` 落在任一**已确认** E8/E9 的 rel32 域 `[o+1, o+5)` 内，丢弃（那是相对位移，不是绝对引用） |
| F3 | `imm-cover` | .text 内命中必须被某条**解码指令**的立即数域覆盖（`insn.address ≤ i` 且 `i+4 ≤ insn.address+insn.size`）；否则记 `unverified_text`，不计入 `n_abs_text` |
| F4 | `section-class` | 命中节 ≠ `.text` ⇒ 分类 `n_abs_data`（`.rdata/.data`）或直接排除（`.rsrc/.detour/PE-header` 除非该 VA 本身在这些节） |
| F5 | `self-hit` | 命中偏移 == VA 自身文件偏移（对象本体字节恰好含自身地址）⇒ 排除 |
| F6 | `symmetry` | E8/E9 正向：`tgt = o+5+rel32+ImageBase`；`tgt` 必须落在某节的 `max(vsize,rsize)` 范围内，否则丢弃 |

F1 的「imm32 覆盖」判定：对命中字节 `i`，回看 `i-1` 处 opcode；
若属于上表，则「call 候选」不成立。该规则**不需要**完整反汇编，
适合 400 条批量；精确复核再上 capstone（F3）。

### 3.2 最小测试集（从 T4 样本抽取）

`tests/fixtures_t4.json` 收录并被 `tests/test_scan_filters.py` 断言：

| # | VA | 场景 | 期望 |
|---|---|---|---|
| T1 | `0x0087F7E8` @ site `0x0040D190` `B9 E8 F7 87 00` | imm32 低字节 `E8` 被误判 call | F1 丢弃伪 call；真 abs 引用保留（`covers_abs_at=0x0040D191`） |
| T2 | `0x0087F7E8` @ `0x0040D1B3` `05 E8 F7 87 00` | 同上（`add eax, imm32`） | F1 |
| T3 | `0x006CF240` 窗宽 8 vs 16 | 假冲突 | `WINDOW_VARIANT`，合并为 16B |
| T4 | `0x007E2800`（.rdata 对象，n_abs_text=218，n_call=0） | 对象在 .rdata，但引用点是 .text imm32 | F3 → `text-imm`；`rel32-coincide` 杂散剔除 |
| T4c | `0x006CF240` 的 .rdata 指针槽（n_abs_data=1） | 数据段指针 | F4 → `data-abs`，不进 `n_abs_text` |
| T5 | `0x007C5F00`（n_call=2029） | 真 E8 直调高频 | 保留 `n_call`，F6 目标在 .text |
| T6 | `0x00886B88` BSS + `0x004047E5` `B9 88 6B 88 00` | bss_ref 锚点 | schema 合法，`covers_abs_at=0x004047E6` |
| T7 | `0x0040D280` `8B 81 64 55 00 00 C3 90…` | 出口可截断 | prologue 边界窗 ≥ 7B，仍可扩到 16B |
| T8 | `0x00400000` `4D 5A` | PE 头 | `type=raw`，`kind=pe-base`，F4 不当代码 xref |

### 3.3 实测漏斗（482 悬空 VA 全量复算）

见 `out/scan_filter_report.json`：

- raw `find()` 总命中 → 剔 F2（rel32 重叠）→ 剔 F1（imm 内伪 call）→
  剔 F4/F5 → 得 `n_abs_text` / `n_abs_data` / `n_call`。
- 关键样本：`0x0087F7E8` raw find 3700 次，其中 3699 次为已知 imm32 前缀
  （真绝对引用），0 次落在 rel32 域严格起点；伪 call 风险来自
  **imm32 低字节 `E8`**（F1 覆盖）。

---

## 4. 工厂 Runbook —— 下一波 400 条悬空 VA 批量补证

共 **10 步**（`factory_batch.py` 实现 1–9，第 10 步人工/工具回归）：

1. **intake**：从 `out/re_work/atlas_rev/lead/atlas_va_crosscheck.json`
   取 `dangling`，扣除已有 claims（p1/p2/其它 lib）的 VA，得 400 条队列。
2. **window 采样**：每条按 `W_std=16` 采 `entry_hex` + `asm`（capstone 4 条）。
3. **xref census（带过滤）**：F1–F6 全开，产出 `n_call/n_jmp/n_abs_text/n_abs_data`。
4. **kind 判定**：`pe-base / code / ret-stub / ptr-or-data / ptr-or-vtable / bss-global / unknown`
   （沿用 `scan_p2.py` 分类表）。
5. **BSS 分支**：`raw_available=0` ⇒ 生成 `bss_region` + ≥1 条 `bss_ref` 锚点；
   锚点 hex 必须可复算，`covers_abs_at` 必须指向 `pack(va)`。
6. **冲突检查**：对既有 claims 跑 `classify_pair`；
   `WINDOW_VARIANT` 合并进 `merged_from`，`BYTE_CONFLICT` 进隔离队列。
7. **分级**：按 `claim_schema.py:grade_of` 规则打 `[实证]/[推演]/[待实测]`。
8. **双格式落盘**：`claims_batch.txt`（喂 `tools/audit_bytes.py`）+
   `claims_batch.jsonl`（喂 schema 校验器）。
9. **自检**：`python claim_schema.py claims_batch.jsonl` 全绿；
   `python tools/audit_bytes.py claims_batch.txt` 全 PASS（只读）。
10. **回归与归档**：`tools/verify_anchors.py --claims docs/re/anchor_claims.txt`
    不得回退；批次摘要写 `out_batch_summary.json`（覆盖率/冲突数/BSS 锚点数）。

### 4.1 批次配额（建议）

| 桶 | 配额 | 优先级 |
|---|---|---|
| 高 xref（≥50）code | 120 | 立刻可 `[实证]` |
| BSS 无 raw | 65–80 | 锚点断言，补齐 65 条缺口 |
| 普通 code | 120 | 序言+调用点即可 |
| ptr/data/vtable | 60 | 与 R8 vtable 槽对账 |
| 低 xref / unknown | 余量 | `[推演]` 兜底 |

### 4.2 出口判据

- 400 条 100% 有 `type` 且 schema 校验通过；
- `BYTE_CONFLICT` 有清单且不为静默合并；
- BSS 条目 100% 至少 1 条可复算锚点；
- 窗宽全部 16（或 prologue 截断且 ≥4）；`window_widths` 历史值只作审计。

---

## 5. 禁区与口径

- **禁写**：`tools/**`、`ra2render/**`、`gamemd.exe`、`ra2youli/**`、台账、看板、
  ATLAS、`out/reverse/**`。
- 可写：`out/re_work/re_sprint/R_claims_fac/**`、`docs/re/claims_factory_spec.md`。
- 映射口径与 `tools/audit_bytes.py` v3 一致：**段映射**，
  `off = SizeOfRawData + (VA − (ImageBase + VirtualAddress))`；
  PE 头 `off = VA − ImageBase`；一律不用裸 `VA − 0x400000` 跨节。
- `tools/` 内既有脚本只作**只读参考**，本工厂产物不得依赖对其的修改。
