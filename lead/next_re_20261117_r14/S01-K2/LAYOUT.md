# S01-K2 · LAYOUT — GetSize 槽契约双向核对（T5）

方法：RTTI TypeDescriptor 用**文件偏移扫描** `.?AV…@@`（`e_rtti3.py`：blob.find → `pe.get_rva_from_offset`+IB 得 name_va，TD=name_va−8）；
COL 由 `COL+0xC == TD` 定位（**不是** COL+8，那是 CD：`R14_COMMON §8.1 错源⑧`）；
vtable 由 `vtable[-1] == COL` 从 `.rdata` 定界（`§8.2⑦`：不得用 atlas 函数边界反推）。
证据：`EVIDENCE/rtti_targets.txt`、`getsize_candidates_v2.txt`、`alloc_points.txt`、`fn_55B880...`（见下）。

## 1. 交叉验证：方法正确性（LayerClass vtable 0x7E6060）

先从已知锚点验证链方法：
- TD `0x816B10` = `.?AVLayerClass@@`（`pe.get_rva_from_offset(0x416B18)+IB−8`）。
- COL `0x7FFC28`（`COL+0xC=TD`）→ vtable[-1] 得 **vtable `0x7E6060`**。
- vtable[4] = `0x40CF00`、vtable[7] = `0x5519B0` ——
  与 `R14_COMMON §4.2`（LayerClass vt=0x7E6060、Add 槽 `0x5519B0`）**逐值吻合** ⇒ 链方法正确 ✓。

## 2. LogicClass（TD 0x816B30，COL 0x7FA970，vtable 0x7E1900）

- TD `0x816B30` = `.?AVLogicClass@@`（fileoff `0x416B38`）；vptr 读得 `0x7F9594`（合法 RTTI vftable）。
- 两个 COL 命中 `COL+0xC==TD`：`0x7FA924`、`0x7FA970`；后者 `vtable[-1]` 得 **vtable `0x7E1900`**。
- 前 30 槽见 `getsize_candidates_v2.txt`；关键槽：

| 槽 | 值 | 字节形态 | 判读 |
|---|---|---|---|
| v[10] | `0x55B880` | `57 8B 7C 24 08 85 FF…` | `MapClass::PointerGotInvalid`（coverage S06 [已证]，**不是** GetSize；此即 §981 "slot 取错风险"实例：v[10] 形态是 push edi/mov，非 `B8 imm32`） |
| v[11] | `0x7FA9A0` | `00 00 00 00 00 00 00 00…` | **数据地址（BSS 区，全 0）**，不是函数！不得当 vftable 槽函数 |
| v[12] | `0x40CF30` | `56 8B F1 8B 46 04 C7 06 2C 19 7E 00…` | VectorClass 构造链（写 vptr `0x7E192C`），**非 `B8 imm32 C3`** |

- **扫描 30 槽：无任何 `B8 <imm32> C3` 形态**（判据"严格六字节 B8 imm32 C3"，`getsize_candidates_v2.txt` 记 none）。

## 3. GetSize 双向核对结论（fail-closed）

派卡要求"不能假定槽 12、分配点覆盖 6A imm8 等四形态、`0x4C9150` 桩排除"。核对结果：

| 项 | 结论 | 分级 |
|---|---|---|
| LogicClass 是否 AbstractClass 派生族 | **否**：vtable 布局是 `VectorClass`/容器式（v[11] 是数据、`0x40CF30` 写 vptr `0x7E192C`=VectorClass vt），v[12] 是构造链而非 size 常量 | [已证]（字节+RTTI 双支撑） |
| 槽 12 = GetSize（AbstractClass 惯例） | **不适用**于 LogicClass；强行套用会取到 `0x40CF30` 构造代码（非 `B8 imm32`） | [已证] |
| 严格 `B8 imm32 C3` 槽（30 槽内） | **0 个** | [已证]（穷举） |
| 分配点 `push <size> → operator new` 双点闭合 | **无法闭合**：镜像中 `0x7CA650` 是 `__chkstk`（主循环 `mov eax,0x1c28; call 0x7CA650` 分配栈帧），不是 operator new；按 operator new 扫描 `push imm → call` 得 **0 处**（`alloc_points.txt`）。LogicClass 是 `0x87F778` 处静态 VectorClass 实例（R14_COMMON §5），非堆 new 对象 | [已证]（0 处 + 静态实例） |
| `0x4C9150` 桩 | `33 C0 C3`（R14 COMMON §8.2②），本卡未把它计入（vtable 槽里也没出现） | [已证]（继承底座） |

**结论**：LogicClass 的 GetSize **不能定**（容器类、非 AbstractClass 族；30 槽无 size 常量形态；无堆分配点可双点闭合）。
按纪律 5（RTTI fail-closed）与 §981（槽号随前置虚函数数变化），**不臆造 size、不假定槽 12**。
`B8 imm32 C3` 判据的全镜像基线（666）/ 不要求 C3（837）来自派卡底座，本卡不逐条重数，只用于说明"裸形态不特异、必须叠加槽位锚定"。

## 4. WinMain 相关类

`0x6BB9A0`（游戏入口）与 `0x7CD80F`（CRT startup）在 coverage S01 均为 `[静态推断]` 函数入口，
**无 RTTI TypeDescriptor**（游戏入口是自由函数，非类方法）⇒ 无 GetSize 概念。
对它们只做"函数区间包含 + 序言"核对（已在 MAINLOOP.md §0），不做槽契约核对。

## 5. 布局复算方法（给审计员）

```
# RTTI 链（e_rtti3.py）
td = get_rva_from_offset(blob.find(b'.?AVLogicClass@@')) + IB - 8   # = 0x816B30
col = p where dword[p+0xC] == td                                    # = 0x7FA970
vt  = q+4 where dword[q] == col and q+4 in .rdata                   # = 0x7E1900
for i in 0..29: slot = dword[vt+4*i]; is_getsize = slot bytes[:1]==0xB8 and bytes[5:6]==0xC3
# 实测 0 命中
```
