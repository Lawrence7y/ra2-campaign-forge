# KB · `00_global_skeleton` — PE 结构与全局骨架

> 本文件由 RE-ATLAS 线独立复算产生。凡标 [实证] 的条目，均为从
> `ra2youli/gamemd.exe` 字节直接读出，并在 `re_atlas/tools/` 下有可重跑脚本。
> 证据标准沿用 `docs/re/EVIDENCE_STANDARD.md`；置信度分级：实证 / 推演 / 社区。

---

## 0. 目标二进制与指纹

| 项 | 值 | 证据 |
|:---|:---|:---|
| 路径 | `ra2youli/gamemd.exe` | 生产路径（部署件），**不是** `.ra2opt/orig` 备份 |
| 大小 | 4,825,360 B | 文件 stat |
| sha256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` | `sha256sum` |
| ImageBase | `0x00400000` | PE 可选头 +0x1C |
| 入口 RVA | `0x007CD80F` | PE 可选头 +0x10（AddressOfEntryPoint） |
| .text sha256 | `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738` | `ra2re rtti` 自算 |

**⚠ 快照纪律**：同目录 `ra2youli/.ra2opt/orig/gamemd.exe` 是 ra2opt 的备份件
（sha256 `db26430…`），与生产件**仅差 2 字节**：文件偏移 `0xAE` 与 `0xB2`，
**都在可选头的 `CheckSum` 字段（`0xB0..0xB3`）里**——
live = `00 00 40 00`（`0x00400000` = 4,194,304），
orig = `00 00 10 00`（`0x00100000` = 1,048,576）。
`TimeDateStamp`（`0xA8..0xAB`）两份都是 `00 00 00 00`，**未被修改**。

⇒ 代码段逐字节完全相同，本线一切 .text 结论对两者通用；
差异只在 PE 校验和，属 ra2opt 改 LAA/头字段后的正常重算残迹。
但**任何引用都应标明用的是哪一份**，因校验和不同即 sha256 不同，
按哈希做"母本未改动"门禁时会误判。
（逐字节 diff 证据：`re_atlas/evidence/binary_identity.txt`。）

---

## 1. PE 段表 [实证]

`re_atlas/evidence/claims_verify.txt` 头部即本表，由 `verify_claims.py` 打印。

| 段 | RVA | VirtualSize | RawPtr | RawSize | 备注 |
|:---|---:|---:|---:|---:|:---|
| `.text` | `0x00001000` | `0x003DF38D` | `0x00001000` | `0x003E0000` | 代码。**vsize < rawsize**，见下 |
| `.rdata` | `0x003E1000` | `0x00030074` | `0x003E1000` | `0x00031000` | 只读数据、RTTI、导入名 |
| `.data` | `0x00412000` | `0x00367BE4` | `0x00412000` | `0x0006C000` | 可写。**vsize ≫ rawsize**：未初始化部分即 BSS |
| `.rsrc` | `0x0077A000` | `0x00018128` | `0x0047E000` | `0x00019000` | 资源。**FileOffset = VA − 0x6FC000** |
| `.detour` | `0x00793000` | `0x00002718` | `0x00497000` | `0x00003000` | 模组内嵌 blob。同 `.rsrc` 偏移口径 |

### 1.1 三条易踩的换算规则 [实证]

1. **`.text` / `.data` / `.rdata`**：`FileOffset = VA − 0x400000`。
   三段 RawPtr == RVA，所以 VA−ImageBase 就是文件偏移。这也是全项目
   "`VA − 0x401000` 再按 .text 起点索引"那套口传算法的来源——两者等价，
   但只在前三段成立。
2. **`.rsrc` / `.detour`**：`FileOffset = VA − 0x6FC000`。
   本线实测：`.rsrc` RVA `0x77A000` → RawPtr `0x47E000`，差 `0x2FC000`；
   换算成 VA 口径即 VA−`0x6FC000`。与 `docs/re/PERF-RENDER01` 的结论一致。
3. **`.data` 的 BSS 尾部没有 raw**：`vsize 0x367BE4` vs `rawsize 0x6C000`，
   即 `0x412000+0x6C000 = 0x47E000` 之后、到 `0x77A000` 之前全是零填充。
   任何"在 .data 里读字节断言"的检查都必须先判 `delta < rawsize`，
   否则会把 BSS 读成后续段的字节。`verify_claims.py` 用
   `in-section-but-beyond-raw` 显式区分这一类。

---

## 2. 函数边界与命名覆盖率基线 [实证]

**方法**：线性 capstone 扫描在本件上**不可用**——它只解出 155,215 条指令、
覆盖 .text 的 **11.1%**，在段内嵌数据处失步。
这与既有记录（capstone 单次 disasm 截断）同源，本线再次复现。
正确做法是**递归遍历**：以 PE 入口 + 全部 rel32 `E8`/`E9` 目标 + 全部虚表槽为根，
沿 call/jcc 边推进。

| 指标 | 数值 | 来源 |
|:---|---:|:---|
| .text 范围 | `0x00401000` .. `0x007E1000` | 段表 |
| 根集合 | 9,183 rel32 + 6,499 虚表槽 + 1 入口 | `fn_walk.py` |
| 实解指令数 | 1,447,234 | 同上 |
| 发现函数入口 | **15,224** | 同上 |
| 有名字的入口 | 551（**3.62%**） | 与 `symbol_map.json` 交集 |
| 语料命名点总数（.text 内） | 1,304 | `extract_symbols.py` |
| 其中不在入口上 | 753 | 函数体内站点或数据 |

**口径声明**：`15,224` 是"被至少一条边到达的入口"下界，不是真值上限；
间接跳转（跳表）目标只进了 `E8/E9` 静态集，未做分派表恢复，故真值应更大。
命名率 3.62% 是**保守下界**（许多语料名字指向函数体内的站点而非入口）。

---

## 3. RTTI 类清单与虚表 [实证]

工具：`python -m ra2re rtti ra2youli/gamemd.exe --out re_atlas/evidence/rtti`
（仓库既有工具，本线只调用、未修改）。产出 `re_atlas/evidence/rtti/`。

### 3.1 自洽性检验结果（工具自带，用于证明解析口径正确）

| 头部宽度假设 | 有效描述符 | 共享 `type_info` vtable 占比 | 判定 |
|:---|---:|---:|:---|
| 8 字节 | 988 | 100.0%（1 个不同值） | **← 选中** |
| 12 字节 | 125 | 41.6% | 否 |
| 16 字节 | 105 | 43.8% | 否 |

⇒ 本件是 **MSVC 8 字节 TypeDescriptor 头部**口径，且 `type_info` vtable 全局只有 1 个。
这同时说明：**不能用"COL 签名 0"之类的判据区分 game.exe/gamemd.exe**——
两者共享同一 RTTI 形态，区分须靠别的手段。

### 3.2 解析统计 [实证]

| 项 | 数量 |
|:---|---:|
| 装饰名 | 988 |
| 类描述符 | 988 |
| 拿到 CompleteObjectLocator | 954 |
| 拿到 vtable 地址 | 954 |
| 拿到 >1 层基类链 | 698 |
| vtable[0] 落在 .text | **954 / 954**（100%） |

### 3.3 与语料的交叉核对 [实证]

`xcheck_vtables.py` 把 ATLAS §11 主表里的虚表行与本次 RTTI 独立结果比对：

| 结果 | 数量 |
|:---|---:|
| 虚表地址一致 | **20** |
| 不一致 | **0** |
| 语料侧无 RTTI 对应 | 14（全是 §11.1 的**全局变量**，本就不是虚表） |

⇒ ATLAS §11 的虚表地址列**无一处错**。另有 14 条"缺"是索引口径混用
（§11.1 单例表被正则一起捞到），不是缺陷。

---

## 4. 主要全局对象地址

这些是 §11.1 的种子，本线**只做登记与交叉标注**，逐条字节复算留待后续模块
（多数需要"解引用层级"语义判定，单靠字节无法确证指针 vs 实例）。

| 符号 | VA | 层级 | 来源 | 置信度 |
|:---|:---|:---|:---|:---|
| `TacticalClass` 单例指针 | `0x00887324` | `TacticalClass**` | ATLAS §11.1 | 社区/待复算 |
| ↳ RTTI 侧类名 | **`Tactical`**（VT `0x007F4348`，25 槽，基 `AbstractClass`） | — | 本线 RTTI 复算 | 实证 |
| ↳ 另有 `TacticalClass@DisplayClass` | VT `0x007E608C`，33 槽，基 `GadgetClass→LinkClass` | **不是**战术视口类 | 本线 RTTI | 实证 |
| `MapClass` 实例 | `0x0087F7E8` | 直接实例 | ATLAS §11.1；本线在 `0x0072A0AE` 见 `mov ecx, 0x87F7E8` 实参 [实证旁证] |
| `ScenarioClass*` | `0x00A8B230` | 一级解引用 | ATLAS §11.1 | 社区/待复算 |
| `RulesClass*` | `0x008871E0` | 一级解引用 | ATLAS §11.1 | 社区/待复算 |
| `HouseClass::Player` | `0x00A83D4C` | `HouseClass**` | ATLAS §11.1；本线在 `0x0050B716` 见 `mov edx,[0xA83D4C]` 后与 `ecx` 严格比对 [实证] |
| `HouseClass::Array` | `0x00A80228` | 动态向量 | ATLAS §11.1 | 社区/待复算 |
| `PathFinder` | `0x0087E8B8` | 直接实例 | ATLAS §11.1 | 社区/待复算 |
| `SpatialGrid` | `0x00887888` | 直接实例（400 桶） | ATLAS §11.1 | 社区/待复算 |
| `CurrentFrame` | `0x00A8ED84` | `uint32_t` | ATLAS §11.1 + claims `0x0055DE73/79/81` | **实证**（claims 字节断言 323/323 PASS） |
| `VoicesEnabled` | `0x008464AC` | `uint8_t` | ATLAS §11.1 | 社区/待复算 |
| 游戏模式标志 | `0x00A8B238` | `uint32_t` | 本线 `0x0050B6F0` 反汇编 [实证] | **实证**（新增，见 §5） |

---

## 5. 本线新增实证（语料未记或记法不同）

### 5.1 `0x0050B6F0` — `HouseClass::IsPlayerControl`

字节序列（`B8 01…` 起）：
`a1 38 b2 a8 00` = `mov eax,[0x00A8B238]`；`85 c0`；`75 1d`。
两分支：`[0xA8B238]==0` 时读 `[ecx+0x1EC]`/`[ecx+0x1ED]` 布尔或；
否则 `mov edx,[0xA83D4C]`（`HouseClass::Player`）→ `cmp ecx,edx; sete al; ret`。

⇒ **三种命名同时存在于语料**（`House::RadarVisible` / `HouseClass::RadarVisible`
/ `HouseClass::IsPlayerControl`）。按函数语义（是否本地玩家控制）与 ATLAS §21
的 217 处直调语境，本线采纳 **`HouseClass::IsPlayerControl`** 为正式名，
另两名为同义描述。分类：ALIAS，非缺陷。

### 5.2 `0x00871E38`…（占位，待后续模块填）

---

## 6. 冲突与勘误清单（详见 `../CONFLICTS.md`）

| # | 对象 | 语料说法 | 本线复算 | 处置 |
|:--|:---|:---|:---|:---|
| G-1 | `TeamTypeClass` 实例尺寸 | ATLAS §11.2：288 / `0x120`，取证 `0x6F29C0: mov eax,0x120; ret` | **248 / `0xF8`**；`vtable[12]=0x006F20B0` = `B8 F8 00 00 00 C3` | **ATLAS 错**（取证 VA 与返回值双错）；⏳ 待异族核验 |
| G-2 | `AITriggerTypeClass` 实例尺寸 | ATLAS §11.2：256 / `0x100`，取证 `0x420990` | **272 / `0x110`**；`vtable[12]=0x0041FFE0` = `B8 10 01 00 00 C3` | **ATLAS 错**，与语料 E-AIT-1 双通道一致 |
| G-3 | 虚表全表 | — | 20/20 一致、0 不一致 | 无缺陷 |
| G-4 | `RadarClass` 实例尺寸 | ATLAS §11.2：4864 | `vtable[12]=…` 体首是 `mov eax,[ecx]`，非 `mov eax,imm` | **口径不适用**：该槽不是 `GetSize`，ATLAS 取证方式在此类失效 |
| G-5 | `WWMouseClass` 实例尺寸 | ATLAS §11.2：96 | 同 G-4：`mov eax,[ecx+0x20]` | 同 G-4 |

**G-4/G-5 的意义**：`vtable[12] == AbstractClass::GetSize` 这个前提
**并非对所有类成立**。凡用该槽反推尺寸的结论都须先验"体首是否 `mov eax,imm`"，
否则会把一个访问器当成尺寸函数。本线 `xcheck_sizes.py` 已把该判定写成门禁
（`NO-IMM` 分支），后续凡引用 §11.2 尺寸者都应先跑一次。
