# S12-Q2 PROGRESS · 取格路径静态复核

> 卡号 S12-Q2｜2026-11-17｜只读；未改 gamemd.exe / 台账 / 游戏文件；未 git commit。
> 双通道：A=capstone 5.0.7 `skipdata=True` 线性解码（1,394,186 条）；B=裸字节 E8 rel32 扫描 + RTTI 原始解析。两通道均不依赖 `function_atlas.tsv entry+size`。

## 结论表

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | `obj+0x520` = **BuildingTypeClass\***（非 MapClass）。RTTI：vtable `0x7E4570`→COL `0x7FC618`→TD `0x8193A8`→`.?AVBuildingTypeClass@@`；写点 13 处；槽 0x88 get-type。W177 真机结论静态独立闭合 | `[已证]` | `EVIDENCE\rtti_check.txt`、`w520_43B756.txt`、`q1_520_writes.txt`、`slot88_getter_459EE0.txt`、`two_channel_verify.txt` |
| 2 | 格坐标候选偏移数 **3**（`Location` +0x9C/X、+0xA0/Y、+0xA4/Z，int32 lepton；2D 取格用 X/Y）。写者 `SetLocation=0x5F6940`；读者 `GetMapCoords=0x41BEA0` 等，均 `sar 8` 输入 ⇒ 坐标非指针 | `[已证]` | `EVIDENCE\find_mapcoords.txt`、`again_slots.txt`、`getcell_slots_disasm.txt` |
| 3 | **路径 A（最稳）**：obj→Location(+0x9C/+0xA0)>>8→`idx=(Y<<9)+X`→`cellArray=dword[0x87F924]`→`CellClass*=dword[base+idx*4]`。MapClass 单例 `0x87F7E8`（`[+0x13C]=0x87F924`，399 处绝对引用）；`GetCellAt=0x5657A0`（1439 调用点双通道一致）；`GetMapCoords=0x41BEA0` | `[已证]` | `EVIDENCE\getcell_5657A0.txt`、`two_channel_verify.txt`、`getcell_slots_disasm.txt` |
| 4 | **路径 B（引擎权威）**：`obj->vtable[+0x1B8]`(0x41BEA0) 出参 CellStruct → `GetCellAt(0x5657A0)` with `ecx=0x87F7E8` → eax=CellClass\*。EIP 捕获点 `0x5657D5`/`0x41BEDA`；与 A 获取方式不同（内存重算 vs 调用点捕获）⇒ 两条独立可用路径 | `[已证]` | `EVIDENCE\find_getcell_impl.txt`、`getcell_slots_disasm.txt`、`getcell_5657A0.txt` |
| 5 | CellClass 链复核：链头 `cell+0xE4`/`+0xE8`、元素 `next=+0x30`。atlas 区间：挂 `0x47E8A0`[0x47E8A0,0x47EA8D)、摘 `0x47EA90`[0x47EA90,0x47EB97) | `[已证]` | `EVIDENCE\cellchain_47E8A0.txt`、`cellchain_47EA90.txt` |
| 6 | 越界/空槽 → `InvalidCell=0xABDC50`（`[0xABDC74]`=查询坐标）；`idx∈[0,0x40000)`，stride=4 | `[已证]` | `EVIDENCE\getcell_5657A0.txt` |

## 核心数字（给审计，1–3 个 + 复算方法）

1. **`obj+0x520` = BuildingTypeClass\***；13 个 +0x520 写点。
   - 复算：`python work\rtti_check.py 0x7E4570` → TD name `.?AVBuildingTypeClass@@`；`python work\verify_two_channel.py` → CH A 写点 13 = §673/§675 数；CH B 裸字节 `20 05 00 00` 命中 1184（含非指令，仅作独立发现通道，写点语义由 A 解码定）。
2. **格坐标候选偏移 = 3**（+0x9C/+0xA0/+0xA4）；MapClass 单例 `0x87F7E8`，格数组基址 **`0x87F924` = `[单例+0x13C]`**，stride **4**。
   - 复算：`python work\find_mapcoords.py`（+0x9C 读 1209 处，列 `sar 8` 窗口）；`python -c` 扫 `[0x87F924]` 绝对引用 = **399**；`0x87F7E8+0x13C=0x87F924` 手工核算。
3. **两路径关键地址**：路径 A `GetCellAt=0x5657A0` + `GetMapCoords=0x41BEA0`；路径 B 同两函数（捕获方式不同）+ foundation `0x5683C0`。
   - 复算：`python work\verify_two_channel.py` → 调用点 A=1439 / B(E8 rel32)=1439，`equal=True`；`python work\disasm_at.py 0x5657A0 5 30` 逐条核对 `shl eax,9` / `mov ecx,[ecx+0x13c]` / `mov eax,[ecx+eax*4]` / `ret 4`。

## 纪律符合性要点

- 双通道至少一条不依赖 atlas：CH B 纯裸字节+RTTI ✓；两通道不同源 ✓（1439=1439）。
- capstone `skipdata=True` ✓（`core_disasm.py`）；`boundary_check` 未使用（无需判断入口边界；站点归属用 atlas 区间包含）。
- thiscall `ecx` 来源回溯：`0x5657A0` 1439 调用点中路径 A/B 抽样逐一为 `mov ecx,0x87f7e8`（`find_getcell_impl.txt`）；`0x4544A0` 等带条件的经 `ecx=0x87f7e8` 立即数（`getcell_slots_disasm.txt`）。
- 站点归属用函数区间包含（`0x5657A0` size 56、`0x47E8A0` size 489、`0x47EA90` size 263 取自 atlas，仅作区间，非入口启发式）。
- 候选假设自证：`obj+0x520 是 TypeClass`（卡面猜测）由 RTTI+真机双通道证明；未信台账 §675（已作废：构造器真身 `0x43B740`，见 R14_COMMON §1）。
- 写"新发现"前已 grep 台账；`+0x520`=Type 系 §678 既有结论，本卡为独立复核非新发现；分级无虚高（路径 B 的 foundation 扩展标 `[静态推断]`）。

## 影响面 / 交接

- 本卡给出取格配方（§5 表）供后续真机卡：先由 obj 算 `CellClass*`，再读 `cell+0xE4/E8` 与 `+0x30` 链，即可判定"该格是否已被占用"——②-b `PROBE_TABLE` L7/L24/L25/L36 连带失效由此解除。
- 不改 `COVERAGE\coverage.tsv`；只交 `coverage_delta.tsv`（8 行）。
