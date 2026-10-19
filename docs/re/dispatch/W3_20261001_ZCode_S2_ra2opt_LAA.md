# W3-ZC-S2 · `ra2opt` LAA 位错位缺陷修复（**独立会话包** · 与 ra2render/真机轨并行）

> 本包由 **Lead 亲跑复算发现**，属于 `ra2opt` 工具链缺陷，**不涉及 `ra2render/**`、不涉及真机**，因此可在**独立 ZCode 会话**中与 Z1/Z2/Z3 并行。
> 写作用域唯一：`ra2opt/**` + `out/re_work/zcode_live/W3_20261001/ra2opt_laa/**`。**禁止**碰 `ra2render/**`、`docs/**`、游戏目录、`tools/**`。

## 1. 缺陷（Lead 已实证，请自行复算确认）

`ra2opt/pe.py` 把 **Large Address Aware** 的读写落在**错误的 PE 字段**上：

| 位置 | 现码 | 问题 |
|---|---|---|
| `pe.py:10` 注释 | `+70 DllCharacteristics (2)  bit 0x20 = IMAGE_FILE_LARGE_ADDRESS_AWARE` | **字段错**：LAA 不属于 `DllCharacteristics` |
| `pe.py:35` | `IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020` | 常量名与字段绑定错 |
| `pe.py:88-90` | `def laa(self): return bool(self.dll_characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE)` | 读错字段 |
| `pe.py:248-249` | `value = info.dll_characteristics \| IMAGE_FILE_LARGE_ADDRESS_AWARE …`（`set_laa`） | 写错字段 |
| `pe.py:67-82` | `PEInfo` 字段表**根本没有 COFF `Characteristics`** | 真正的 LAA 字段从未被读取 |

**事实**：
- LAA 位 = **COFF File Header `Characteristics`** 的 `0x0020`（`IMAGE_FILE_LARGE_ADDRESS_AWARE`），位于 `e_lfanew + 0x16`。
- `DllCharacteristics` 的 `0x0020` 按 PE 规范是 **`IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA`**（`ra2opt/pe.py:36` 自己也把 `NX_COMPAT` 定义为 `0x0100`，可交叉印证）。
- `ra2opt` 的 `apply perf` 把 `DllCharacteristics` 从 `0x0000` 改成 `0x0020` 并写入 `SizeOfStackReserve` 1MB→4MB —— 即 `ra2youli/gamemd.exe`（`73201cc0…`）与出厂件（`DB264305…`）之间**仅有的 2 字节差异**。
- 该 `0x0020` 位**实际惰性**：`DYNAMIC_BASE`（`0x0040`）未置，HIGH_ENTROPY_VA 无效果。
- **出厂件的 COFF `Characteristics` 本来就是 `0x032F`（LAA 已置）** ⇒ `ra2opt` 声称的"开 LAA"既非必需、也**没有真正动到 LAA 位**；`ra2opt laa off` 同理**关不掉 LAA**。

## 2. 复算要求（先证伪再动手）

1. 自写脚本读两枚 exe（`ra2youli/gamemd.exe` 与 `ra2youli/.ra2opt/orig/gamemd.exe`）的 `e_lfanew`、COFF `Characteristics`、`DllCharacteristics`、`SizeOfStackReserve`，**输出原文**贴进回报。
2. 证明两者的 COFF `Characteristics` **相同**且 `0x0020` 位**均已置**。
3. 证明 `0xAE/0xB2` 两字节差异落在 `DllCharacteristics` 与 `SizeOfStackReserve`，**不在任何节内**（与 `docs/re/baseline_integrity_note.md` §三 一致）。

## 3. 修复要求

1. `PEInfo` 增加 **COFF `characteristics`** 字段并在解析时读入（`e_lfanew + 4 + 18`）。
2. **`laa` 属性改读 COFF `Characteristics` 的 `0x0020`**；**`set_laa` 改写该字段**。
3. 新增独立属性 `high_entropy_va`（`DllCharacteristics` 的 `0x0020`），**与 LAA 解耦**；`ra2opt` 若要保留"写 0x0020"的旧行为，必须**改名并注明这是 HIGH_ENTROPY_VA、且需要 DYNAMIC_BASE 才有效**。
4. `optimize.py` 的 `perf` profile：`"开 LAA"` 文案须改为对 **COFF 字段**的操作；若出厂件已置 LAA，应输出 `already_set` 而非假装变更。
5. `summary()`/`ident` 输出同步（`laa: true/false` 与 `high_entropy_va` 分列）。
6. **兼容性**：`restore`/回滚路径必须仍能把 `DllCharacteristics` 还原为出厂值（`0x0000`）、`SizeOfStackReserve` 还原 `0x00100000`，**不得**因本次修复而改变既有备份/回滚语义。

## 4. 测试（必须实跑，原文粘贴）

- 运行既有 `ra2opt/tests.py`（或 `python -m ra2opt.tests`）→ 全绿。
- **新增回归测试**：在**副本**上验证 ①读出厂件得 `laa=True`（COFF 0x032F）②`laa off` 后 **COFF 位真的清掉**（这是旧码做不到的）③`laa on` 可复原 ④`DllCharacteristics` 的 `0x0020` 与 LAA 不再互相污染。
- **禁止**对 `ra2youli/gamemd.exe`、`ra2bench/gamemd.exe`、`D:\Red2\**` 做任何写操作；测试只在 `out/re_work/zcode_live/W3_20261001/ra2opt_laa/sandbox/` 的副本上做。
- 收尾贴：两枚游戏 exe 的 sha256 **与开工一致**（证明只读）。

## 5. 交付物

- 修复后的 `ra2opt/**` 源码
- `out/re_work/zcode_live/W3_20261001/ra2opt_laa/{REPORT.md, claims.txt, runs/*.txt}`
- 回报按 `docs/re/AGENT_DELIVERY_FORMAT.md` §A 的 10 节骨架；`[3]` 勘误里请给出 **`docs/OPTIMIZE.md:26,53,58,198` 的订正文本块**（**不要直接改 docs/**，交 Lead）
- 若发现 Lead 上述结论有误，**以你的复算为准**并单列说明
