# W155 · DISPATCH_SITE.md

> 卡：`lead\next_re_20261116_r12\W155_dispatch\`。静态分析：capstone 字节通道 + Ghidra 12.1.4 引用通道。未启动游戏、未 attach、未改游戏文件/主台账。

## 5 行摘要

1. [已证] `0x55B8F0` **是指令边界**：从已知函数入口 `0x55B880` 线性反汇编，`0x55B8DE c2 08 00 (ret 8)` 之后是 **15 个 `90` nop**（`0x55B8E1..0x55B8EF`），`0x55B8F0 = a1 b8 e9 a8 00 = mov eax,[0xA8E9B8]` 恰好落位；派发提示词里"`push 0x10000` 立即数中间"的前提不成立（`68 00 00 01 00` 在 `[0x55B000,0x55C000)` **0 命中**）。
2. [已证] `0x55B8F0` 确实是 **11 路 `Count`→`call [vtable+0x5C]` 阶梯**（11 个数组、每块 39 B、Count 进块读一次快照、`+0x98` 门、`ff 52 5c`），但 **双通道均零引用**：原始 `E8 rel32` 扫描命中 0、全文件 dword `0x0055B8F0` 命中 0、Ghidra `getReferencesTo(0x55B8F0)=0` 且 `functionAt/containing=NONE`（未建函数空洞）⇒ **不是每帧可达路径**。
3. [已证] 真正 **在每帧路径上** 的数组派发在 `0x55AFB0`（atlas entry 存在，size=1901，555 指令，9 回边）：调用链 `0x6BB9A0 → 0x48CCC0 → 0x55D360 →（0x55DC9E call）→ 0x55AFB0`；该函数含 **8 个** `call [reg+0x5C]`，逐一遍历 Team/DiskLaser/RadSite/局部向量/两个未命名数组/Factory/House（多数每次比较重读 Count，只有 2 处快照；门控为 `+0x98` 之外还有 null 检查和 mode `[0xA8B238]`）。
4. [已证] `0x55B960 = ff 52 5c` 是真实指令边界（从 `0x55B8F0` 线性反汇编落位），属于上述不可达阶梯的第 3 块（BulletClass，`Count=0xA8ED50`）；W151 另一个起点 `0x55B8C3` 落在 `89 0c 86`（`mov [esi+eax*4],ecx`，始于 `0x55B8C2`）内部，**不是边界**。
5. [已证] W151 复核：`BulletClass::AI 0x4666E0` 有 **2 个回边**（双通道一致，非字面"1 个"）；33 个直接 callee **并非全 nback=0**（6/33 有回边：0x427CB0/0x468D80/0x47C3D0/0x47C520/0x480510/0x65FA70；W151 自己报告第 134/160 行也承认 0x468D80 有 1 个）⇒ "全 nback=0" 错；但这些循环都不是全场对象数组遍历，**"0.65ms 不可能来自这段更新代码"的方向仍 `[静态推断]` 成立**，具体量化结论不成立。

---

## 0 · 方法与复跑命令

| 通道 | 命令 | 原始输出 |
|---|---|---|
| 字节级 capstone（边界图/模式扫描） | `python work\scan_dispatch.py` | `EVIDENCE\bytescan_sites.tsv`, `bytescan_stats.txt`, `bytescan_context.txt`, `bytescan_targets.txt` |
| 字节级 capstone（定点边界证明/候选排序） | `python work\analyze_candidates.py` | `EVIDENCE\targeted_bytes.txt`, `candidate_rank.txt`, `selected_full_disasm.txt`, `work\maps.pkl` |
| 字节级 capstone（阶梯全表） | `python work\dump_dispatch.py` | `EVIDENCE\dispatch_full_disasm.txt`, `dispatch_blocks.tsv` |
| 字节级（独立调用者扫描） | `python work\caller_bytes_raw.py` | `EVIDENCE\caller_bytes_raw.txt` |
| Ghidra 引用/函数/反编译 | 见 §0.1 | `EVIDENCE\W155All.log` |
| Ghidra 回边（修正版） | 见 §0.1 | `EVIDENCE\W155Branches.log` |
| capstone 回边/闭包 | `python work\bullet_loops.py` / `bullet_closure.py` | `EVIDENCE\bullet_loops_capstone.txt`, `bullet_closure_counts.txt` |

### 0.1 Ghidra 调用（实测 exit=0，`-noanalysis`，未重新复制/覆盖项目）

```
D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat ^
  D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_ghidra\W155 gamemd_auto ^
  -process gamemd.exe -noanalysis -scriptPath <卡目录>\work -postScript W155All.java *> <卡目录>\EVIDENCE\W155All.log
```
`W155Branches.java` 同上替换脚本名与日志名。两次运行输出末行均为 `INFO REPORT: Save succeeded for processed file: /gamemd.exe`。

> 纪律说明：任何"无引用"结论都由 **字节通道 + Ghidra 通道** 双出数；任何字节命中先做 **从已知函数入口线性反汇编** 的边界证明；未用"最大函数/热点/imul 分桶/窗口 cmp"等已失败判据。

---

## 1 · 候选 A：11 路阶梯 `0x55B8F0`（结构对、但静态不可达）

### 1.1 指令边界证明（[已证]）

| 地址 | 原始字节 | 指令 | 边界结论 | 证据 |
|---|---|---|---|---|
| `0x55B8DE` | `c2 08 00` | `ret 8` | 已知函数 `0x55B880`（atlas size=97）的末指令 | `targeted_bytes.txt:4,57` |
| `0x55B8E1..0x55B8EF` | `90` ×15 | `nop` ×15 | 函数尾填充；`0x55B8ED` 是 nop（**不是** `push` 立即数） | `targeted_bytes.txt:5-6,58-72` |
| `0x55B8F0` | `a1 b8 e9 a8 00` | `mov eax, dword ptr [0xA8E9B8]` | **是指令起点**（线性反汇编恰好落位） | `targeted_bytes.txt:7,73` |
| `0x55B8C3` | `0c 86 ...`（属于 `89 0c 86`） | — | **不是**边界；在 `0x55B8C2` 的 `mov [esi+eax*4],ecx` 内 | `targeted_bytes.txt:2,45-46` |
| `0x55B960` | `ff 52 5c` | `call dword ptr [edx+0x5C]` | **是**边界（从 0x55B8F0 线性反汇编落位） | `targeted_bytes.txt:10,203` |

字节搜索（复跑见 `targeted_bytes.txt:13-17`）：`68 00 00 01 00` 在 `[0x55B000,0x55C000)` **0 命中**；`a1 b8 e9 a8 00` **1 命中** = `0x55B8F0`；`FF 5x 5C` **19 命中**，其中 `0x55B912/939/960/987/9AE/9D5/9FC/BA23/BA4A/BA71/BA98` 即 11 个派发点。

`function_atlas.tsv` 中 **无** `0x55B8F0` 条目（未建函数的空洞）；Ghidra 同样 `functionAt=NONE / containing=NONE`，且该区间 `[0x55B8E1,0x55BAA0)` 的 Ghidra 指令列表为空（`W155All.log` 的 `== instructions ...` 段）。

### 1.2 遍历表（[已证]，`EVIDENCE\dispatch_blocks.tsv`）

每块模板（第 1 块 40 B，其余 39 B，末块 41 B）：
```
mov eax,[Count]          ; 进块读一次 = 快照
lea esi,[eax-1]          ; 上界 = Count-1，向下遍历
test esi,esi / jl <next> ; Count==0 跳过整块
mov ecx,[Items]
loop: mov ecx,[ecx+esi*4]
      mov al,[ecx+0x98]   ; skip 门：+0x98 == 0 则不派发
      test al,al / je <dec>
      mov edx,[ecx]
      call [edx+0x5C]
      dec esi / jns loop  ; 每次比较用寄存器，不重读 Count
```

| # | 块起点 | Count | Items | 数组类型 | 基类址 | call 地址 | `+0x98` 门 |
|---|---|---|---|---|---|---|---|
|1|0x55B8F0|0xA8E9B8|0xA8E9AC|AnimClass|0xA8E9A8|0x55B912|是|
|2|0x55B918|0x8B41A0|0x8B4194|BuildingLightClass|0x8B4190|0x55B939|是|
|3|0x55B93F|**0xA8ED50**|0xA8ED44|BulletClass|0xA8ED40|**0x55B960**|是|
|4|0x55B966|0xA8EB50|0xA8EB44|BuildingClass|0xA8EB40|0x55B987|是|
|5|0x55B98D|0xA8E3A0|0xA8E394|AircraftClass|0xA8E390|0x55B9AE|是|
|6|0x55B9B4|0xA83DF8|0xA83DEC|InfantryClass|0xA83DE8|0x55B9D5|是|
|7|0x55B9DB|0x8B4118|0x8B410C|UnitClass|0x8B4108|0x55B9FC|是|
|8|0x55BA02|0xA80218|0xA8020C|ParticleSystemClass|0xA80208|0x55BA23|是|
|9|0x55BA29|0xA8E998|0xA8E98C|TerrainClass|0xA8E988|0x55BA4A|是|
|10|0x55BA50|0x887398|0x88738C|VoxelAnimClass|0x887388|0x55BA71|是|
|11|0x55BA77|0xA8EC48|0xA8EC3C|WaveClass|0xA8EC38|0x55BA98|是|

数组身份来自 `W132_arrays\instance_arrays.tsv`（表内 `count`/`items`/`base` 列），映射由 `work\dump_dispatch.py` 自动完成。上界来源：**快照**（进块 `mov eax,[Count]` 一次；循环比较用 `esi`/`dec`）。按类型分块：**是**（11 个独立块）。skip 门：**全部 `+0x98`**（`8a 81 98 00 00 00` + `84 c0` + `je`）。无 `+0x74/+0x81` 门（本函数内未出现）。

### 1.3 可达性（[已证] 静态双通道：不可达）

| 通道 | 结果 | 证据 |
|---|---|---|
| 字节：`E8 rel32` 全 `.text` 扫描，目标落入 `[0x55B8F0,0x55BAA0)` | **0** | `EVIDENCE\caller_bytes_raw.txt:1-3` |
| 字节：全文件 dword `0x0055B8F0` / `0x0055B960` | **0 / 0** | 同上；对照 `0x4666E0`=1、`0x5F6250`=8（校验扫描有效） |
| 字节：`calledges.raw.log`（Ghidra 旧导出）行触及该区间 | **0** | `EVIDENCE\callers_ghidra_log.txt:1` |
| Ghidra：`getReferencesTo(0x55B8F0)` | **refToCount=0** | `W155All.log` `describe 0x55b8f0` 段 |
| Ghidra：`functionAt`/`containing` / 反编译 | **NONE / NONE / NO FUNCTION** | 同上 |

⇒ [已证] **不是每帧路径**；调用者链不存在于静态二进制。若要运行时可达，只能靠自修改/外部注入，本卡禁止验证 ⇒ 列为 `[未证]` 可能性，不作为结论。

---

## 2 · 候选 B：`0x55AFB0`（真正的每帧派发）

### 2.1 边界与函数身份（[已证]）

`function_atlas.tsv` entry=`0x55AFB0`、size=1901（十进制）、n_instr=555；Ghidra `FUN_0055afb0@0055afb0 size=1901 nInstr=555 backEdges=9`，字节通道线性反汇编同样 555 条 ⇒ 两通道一致。从 entry 线性反汇编到达全部 8 个 `call [reg+0x5C]` 地址，指令恰好落位（`EVIDENCE\selected_full_disasm.txt`，`bytescan_sites.tsv` 8 行，均 `boundary=1`，`insn_hex=ff525c`/`ff505c`，长度 3）。

### 2.2 调用者链（[已证]）

```
0x6BB9A0  →(0x6BE041 / 0x6BE061 call)→  0x48CCC0
0x48CCC0  →(0x48CE8A call)→  0x55D360
0x55D360  →(0x55DC9E call, e8 0dd3ffff)→  0x55AFB0
```
Ghidra：`0x55AFB0` callers=`[0x55D360]`，`refTo[1] from=0055dc9e type=UNCONDITIONAL_CALL`；`0x55D360` callers 含 `0x48CCC0`（ref `0x48CE8A`）；`0x48CCC0` callers=`[0x6BB9A0]`（refs `0x6BE041/0x6BE061`）。与 R11_COMMON §3.4 主链一致。

### 2.3 8 个派发点与遍历表（[已证]，`selected_full_disasm.txt`）

| # | call 地址 | 字节 | 遍历对象/数组 | 基类址/Items/Count | 上界来源 | skip 门 / 分块 |
|---|---|---|---|---|---|---|
|1|0x55B595|`ff 52 5c`|前段过滤后收集的局部向量|Items `[esp+0x24]`, Count `[esp+0x30]`（局部）|每次比较重读 Count（0x55B598）|前段 `call [eax+8]`（槽+8）过滤 + `[esp+0x2d]` 标志；按类型分块|
|2|0x55B5B8|`ff 52 5c`|DiskLaserClass|0x8A0208 / 0x8A020C / **0x8A0218**|快照（`0x55B5A1 mov eax,[Count]`, `lea esi,[eax-1]`）|无 `+0x98`；独立块|
|3|0x55B5E4|`ff 52 5c`|RadSiteClass|0xB04BD0 / 0xB04BD4 / **0xB04BE0**|快照（`0x55B5CD`）|无；独立块|
|4|0x55B610|`ff 52 5c`|调用方传入容器 `edi`|Items `[edi+4]`, Count `[edi+0x10]`|每次重读（0x55B613）|无；独立块|
|5|0x55B63E|`ff 52 5c`|未命名 DynamicVector（base 0xA83E00）|0xA83E00 / 0xA83E04 / **0xA83E10**|每次重读（0x55B641）|**mode 门** `[0xA8B238]`：==0 或 ==5 跳过（0x55B61B..0x55B627）；独立块|
|6|0x55B667|`ff 50 5c`|单对象（`[0x887324]`）|—|无循环|单次虚调用，非数组遍历|
|7|0x55B680|`ff 52 5c`|FactoryClass|0xA83E30 / 0xA83E34 / **0xA83E40**|每次重读（0x55B683）|无；独立块|
|8|0x55B6A6|`ff 52 5c`|HouseClass|0xA80228 / 0xA8022C / **0xA80238**|每次重读（0x55B6A9）|**null 检查** `test ecx,ecx / je`（0x55B6A0）；独立块|

补充：函数前段还有两个**不直接调 `+0x5C`** 的数组循环——`0x55AFE6..0x55B177` 以 `Count=0x8B40D8`/`Items=0x8B40CC` 筛选对象（循环内调 `0x6E53A0`），`0x55B526..0x55B580` 以 `Count=0x8B40F8`/`Items=0x8B40EC` 收集并用 `call [eax+8]`（槽 +8）过滤，为 #1 生成待派发向量。`+0x98` 门**不在这条路径**，而在不可达的候选 A 中（R11 §7281 关于"`+0x98` 只决定 `0x55B960 call`"的描述属于候选 A，不能套到候选 B）。

---

## 3 · 双通道对账（[已证]）

| 命题 | 字节通道 | Ghidra 通道 | 结论 |
|---|---|---|---|
| `0x55B8F0` 边界 | 从 `0x55B880` 线性反汇编落位，前缀 15 nop | 无函数/无指令（`functionAt=NONE`） | [已证] 字节是对的；Ghidra 空洞 ≠ 不是指令 |
| `0x55B960` 边界 | `ff 52 5c` 在 0x55B8F0 线性流中落位 | `refToCount=0`，无函数 | [已证] 同上 |
| 11 路阶梯引用 | `E8` 扫描 0、dword 指针 0、calledge 0 | `getReferencesTo=0` | [已证] 静态不可达（两通道一致） |
| `0x55AFB0` 调用者 | `e8 0dd3ffff @0x55DC9E`；atlas callers=`{0x55D360}` | `UNCONDITIONAL_CALL 0x55DC9E`；callers=`[0x55D360]` | [已证] 每帧可达 |
| BulletClass 回边 | 2（0x466764→0x46674E；0x4678F6→0x467879） | 2（同址，修正后 `W155Branches`） | [已证] 一致 |
| BulletClass 33 callee 的回边 | 6/33 有回边（1,1,1,1,11,1） | 6/33（同址同数） | [已证] 一致，W151 "全 0" 错 |
| `0x55AFB0` / `0x55D360` 回边 | 9 / 6 | 9 / 6 | [已证] 一致 |

---

## 4 · W151 复核（[已证] 数字；方向 `[静态推断]`）

- `BulletClass::AI 0x4666E0`：size=6422，1794 指令，**2 个回边**（双通道）。第 1 个 `0x466764→0x46674E` 是 W151 描述的"从 `AbstractClass*` 向量摘自己"（上界 `[0xB0F5C8]`，`+0x158` 门控）；第 2 个 `0x467879..0x4678F6` 调 `call [edx+0x1C8]` 并与 `[0x89DE70]*2` 比较（`selected_full_disasm.txt`），不是对象数组遍历。⇒ "只有 1 个真循环"按**回边字面数**为错（2）；按语义"只有 1 个数组遍历型循环"为 `[静态推断]` 成立。
- 直接 callee **33 个**（Ghidra 与 `calledges.raw.log` 均 33，一致）；回边非全 0：`0x427CB0`(1)、`0x468D80`(1)、`0x47C3D0`(1)、`0x47C520`(1)、`0x480510`(11)、`0x65FA70`(1)，其余 27 个为 0。W151 报告自身第 134/160 行也承认 `0x468D80` 有 1 回边，与第 93/13 行"全部 nback=0"自相矛盾 ⇒ [已证] "全 nback=0" 是错的。
- 深度≤4 闭包 **303** 函数（与 W151 数字一致），其中 **15** 个引用已知数组 Count（`EVIDENCE\bullet_closure_counts.txt`），但已抽查的 depth=1 `0x421EA0`（引用 AnimClass Count `0xA8E9B8`）回边=0，符合"内联 Add/Remove 模板"解释；**未逐个语义复核 15 个** ⇒ "无一遍历全场对象数组"仍 `[静态推断]`，不能升 `[已证]`。
- 结论方向：这些循环规模与形态都不支持"每发子弹 0.65 ms 来自 AI 更新代码"；具体成本来源（绘制/blit）本卡未查 ⇒ `[未证]`。

---

## LEAD_AUDIT · 核心可抽验数字

> 每条只需"地址 + 反汇编命令"即可复算。命令见 §0；以下原始输出均在 `EVIDENCE\`。

| 项 | 地址 | 字节（hex） | 长度/常量 | 复现位置 |
|---|---|---|---|---|
|A1|`0x55B8DE`|`c2 08 00`|3 B（`ret 8`）|`targeted_bytes.txt:4,57`|
|A2|`0x55B8E1..0x55B8EF`|`90` ×15|15 B nop 填充|`targeted_bytes.txt:5-6,58-72`|
|A3|`0x55B8F0`|`a1 b8 e9 a8 00`|5 B；立即数=`0xA8E9B8`（AnimClass Count）|`targeted_bytes.txt:7,73`|
|A4|`0x55B8C3`|`0c 86`（属 `89 0c 86`）|非边界；始于 `0x55B8C2`|`targeted_bytes.txt:2,45-46`|
|A5|`0x55B960`|`ff 52 5c`|3 B；BulletClass Count `0xA8ED50`/Items `0xA8ED44`|`targeted_bytes.txt:10,203`|
|A6|`68 00 00 01 00` 搜索域|—|`[0x55B000,0x55C000)` **0 命中**|`targeted_bytes.txt:14`|
|A7|11 个 call|`ff 52 5c` ×11|地址 `0x55B912/939/960/987/9AE/9D5/9FC/BA23/BA4A/BA71/BA98`；块长 39 B（首 40、末 41）|`dispatch_blocks.tsv`, `targeted_bytes.txt:17`|
|A8|skip 门|`8a 81 98 00 00 00`|6 B，对象 `+0x98`|`dispatch_full_disasm.txt`|
|B1|`0x55DC9E`|`e8 0dd3ffff`|5 B；目标 `0x55AFB0`|`selected_full_disasm.txt`, `W155All.log`|
|B2|`0x55AFB0` 8 个 call|`ff525c`×7 + `ff505c`×1|3 B/条，地址见 §2.3|`bytescan_sites.tsv`, `selected_full_disasm.txt`|
|C1|`0x4666E0` 回边|—|2：`jl@0x466764→0x46674E`；`jl@0x4678F6→0x467879`|`bullet_loops_capstone.txt`, `W155Branches.log`|
|C2|33 callee 中有回边者|—|`0x427CB0`(1) `0x468D80`(1) `0x47C3D0`(1) `0x47C520`(1) `0x480510`(11) `0x65FA70`(1)|同上|
|D1|`0x55AFB0`/`0x55D360` 回边|—|9 / 6|`candidate_rank.txt`, `W155Branches.log`|
