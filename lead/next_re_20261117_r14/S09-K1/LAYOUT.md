# S09-K1 LAYOUT — 类布局与虚表字节级取证（T1–T4）

目标 `ra2youli\gamemd.exe` · SHA-256 `73201CC0…F67476` · ImageBase `0x400000` · 只读。
卡号 S09-K1｜静态卡，**未跑真机**｜capstone 全程 `skipdata=True`。
全部脚本在 `work/`，可复跑；原始输出在 `EVIDENCE/`。

---

## T1 类清单（RTTI 实测）

### T1.0 方法与定界（回放方法，复算基线）

自建 RTTI 表，链严格按 **`COL + 0xC → TD`，`TD + 8` = 内联 name 字符串**（`.?AV…@@`）。
- TypeDescriptor 签名：本镜像全部 TD 的 `pVFTable = 0x7F9594`，`spare=0`，name 在 `+8` **内联**（不是指针）。读 `u32(TD+8)` 得到 `.?AV` 的 ASCII，绝不可当指针。
- COL(x86)：`+0 sig=0 / +4 offset / +8 cdOffset / +0xC pTD / +0x10 pCHD`。读 `COL+8` 得到的是 `cdOffset`（多为 0），不是 TD ⇒ 会得 `TD=0/name='?'`，本卡 fail-closed 拒绝。
- 实测：**988 TD / 1214 COL**；vtable = `vtable[-4]` 指向 COL 的位置 +4。
- 槽数从 `.rdata` 自己数：扫 `.rdata` 所有 `dword==合法COL` 的位置 P（1214 个 = 1214 张表），vtable=P+4，从 vtable 逐 dword 读，值落在 `.text[0x401000,0x7E1000)` 即算一槽、遇非代码值停，下一 COL 位置作硬上界。**不用 function_atlas entry+size 反推**。
- **基线复算：1214 表 / 14,044 槽 — 与审计 §8.1「14,044 槽 / 1,214 表」逐位吻合**（证据 `EVIDENCE/E01_vtable_baseline.txt`；脚本 `work/t1_vtable_enum_v2.py`）。这证明本卡的 RTTI+定界方法与审计同源且无误。

> 注：`vtables_v2.json` 记 13,351 槽（已知错，少 693）；本卡自数得 14,044，不信 JSON。

### T1.1 S09 主要类（RTTI 名 / TD / COL / vtable / 槽数 / 父类 CHD 实测）

父类由 CHD → BaseClassArray → BaseClassDescriptor 的 TD 取得，**不按名字猜**。
完整表见 `EVIDENCE/T1_all_classes.tsv`（1214 行）与 `EVIDENCE/E00_rtti_s09_classes.txt`。

| RTTI 名 | TD | COL | vtable | 槽数 | 父类(CHD 实测) |
|---|---|---|---|---:|---|
| SidebarClass | 0x816C38 | 0x8095B8 | 0x7F3058 | 55 | PowerClass |
| DisplayClass | 0x816BD8 | 0x7FFCB8 | 0x7E6114 | 50 | MapClass |
| MouseClass | 0x816C90 | 0x7FAB38 | 0x7E1964 | 55 | ScrollClass |
| WWMouseClass | 0x84E638 | 0x80EC60 | 0x7F7B2C | 18 | **Mouse**（RTTI 名，非 MouseClass） |
| SelectClass@StripClass@SidebarClass | 0x83F8F8 | 0x809568 | 0x7F2FCC | 34 | ControlClass |
| SBGadgetClass@SidebarClass | 0x83F8C8 | 0x809510 | 0x7F2F44 | 33 | GadgetClass |
| CommandClass | 0x826F38 | 0x804468 | 0x7EBE3C | 9 | （CHD 无 base，根） |
| TabClass | 0x816C58 | 0x805EA0 | 0x7EDFB4 | 55 | SidebarClass |
| ScrollClass | 0x816C70 | 0x809060 | 0x7F1094 | 55 | TabClass |
| GadgetClass | 0x81D0D0 | 0x800AB0 | 0x7E92BC | 33 | LinkClass |
| Tactical | 0x842A38 | 0x80B9A8 | 0x7F4348 | 25 | AbstractClass |
| RadarClass | 0x816BF8 | 0x8083C0 | 0x7F0344 | 54 | DisplayClass |
| PowerClass | 0x816C18 | 0x808118 | 0x7EFF54 | 54 | RadarClass |
| ListClass | 0x81D110 | 0x805218 | 0x7ED10C | 51 | ControlClass |
| CheckListClass | 0x81D128 | 0x7FD150 | 0x7E4F84 | 51 | ListClass |
| EditClass | 0x820280 | 0x7FFF60 | 0x7E81A4 | 39 | ControlClass |
| DropListClass | 0x820298 | 0x7FFF20 | 0x7E7FCC | 46 | EditClass |
| SliderClass | 0x829DF8 | 0x805308 | 0x7ED21C | 45 | GaugeClass |
| ToolTipManager | 0x844998 | 0x80C888 | 0x7F57AC | 6 | （根） |
| CCToolTip | 0x849EE0 | 0x80E560 | 0x7F74C4 | 6 | ToolTipManager |

**继承链（CHD 实测，逐层）**：
`IGameMap → GScreenClass → MapClass → DisplayClass → RadarClass → PowerClass → SidebarClass → TabClass → ScrollClass → MouseClass`（`0x87F7E8` 为这一串的共用单例实例）。
另一链：`AbstractClass → Tactical`（`Tactical` 的 RTTI 名无 `Class` 后缀，RTTI 权威）。
`WWMouseClass → Mouse`（独立单例 `0x887640`）。`CommandClass`（根）+ 约 40 个 `*CommandClass` 子类（各 9 槽，parent=CommandClass）。

> ⚠️ **结构性判据**：S09 的 UI 主类属 **IGameMap（COM 风格）层次**，不是 AbstractClass 层次。这决定了它们的 slot11/12 **不是** WhatAmI/GetSize（见 T2/T4）。

### T1.2 多继承次级虚表（COL.offset≠0，本卡识别但不误算）

同类的次级 vtable 有独立 COL，`offset=21784(=0x5518)`，例如 `MouseClass@0x7E195C`、`TabClass@0x7EDFAC`、`ScrollClass@0x7F108C`（this 调整接口）。本卡槽数统计以 `offset=0` 主表为准；次级表已在 `T1_all_classes.tsv` 列出（offset 列）。

---

## T2 GetSize 双向核对

**判据先验基线（纪律 1）**：全镜像 `mov eax,imm32(5B)+ret` 候选约 638（本卡严格口径；审计 §969 宽松口径 837），其中真正落在某类 slot12 的 71（≈11%）⇒ **单看 `B8 imm C3` 无鉴别力**，必须叠加「该值确在本类 vtable 槽 12」。本卡全程叠加。

| 类 | slot12 fn | 体首 | 判据A imm | 判据B 分配点 | 结论 |
|---|---|---|---|---|---|
| **Tactical** | 0x6DC460 | `B8 18 0E 00 00 C3` | **0xE18=3608** | `push 0xE18; call 0x7C8E17`@0x52C681/0x599D6D/0x6853A1/0x687604/**0x6BF83C** | **闭合 [已证]** |
| Tactical WhatAmI(slot11) | 0x6DC450 | `B8 38 00 00 00 C3` | 0x38=56 | — | [静态推断]（WhatAmI 不做分配核对） |
| SidebarClass | 0x4F4410 | 复杂函数（`call [eax+0x2c]` 等） | 无立即数 | — | **[未证]**（非标准 GetSize 形态，见下） |
| DisplayClass/MouseClass/TabClass/ScrollClass/RadarClass/PowerClass | 0x4F4410 | 同上 | 无 | — | [未证] |
| SelectClass@Strip/SBGadgetClass/GadgetClass | 0x4E14C0 | 复杂函数（多层 `[eax+8]` 遍历） | 无 | — | [未证] |
| CommandClass | 0x536000 | 复杂函数（sprintf 风格） | 无 | — | [未证] |
| WWMouseClass | 0x7BA350 | `mov eax,[ecx+0x20]; ret` | 字段 getter，非 GetSize | — | [未证] |

**Tactical 双向核对证据链（[已证]）**：
- 判据A：`vtable 0x7F4348 + 12×4 = 0x7F4378`，其值为 `0x6DC460`，体首 `B8 18 0E 00 00 C3` ⇒ `GetSize=0xE18`。
- 判据B：`0x6BF83C: push 0xE18; call 0x7C8E17(operator new)` → `call 0x6D1C20(ctor)` → `0x6D1D54: mov [esi],0x7F4348(vtable)`。两处独立对上 0xE18。
- 证据 `EVIDENCE/E02_getsize_tactical.txt`；脚本 `work/t2_ctor_scan.py`/`work/t2_getsize_probe.py`。

**为何 S09 UI 主类 slot12 不是 `B8 imm C3`**：RTTI CHD 证明它们走 `IGameMap` 层次（COM），slot11/12 被共享的复杂函数占用（`0x4F43F0`/`0x4F4410` 由 SidebarClass/DisplayClass/MouseClass/TabClass/ScrollClass/RadarClass/PowerClass 共用；`0x4E1570`/`0x4E14C0` 由 SelectClass/SBGadget/Gadget 共用）。`0x4F4410` 体首为 `mov eax,[ecx]; call [eax+0x2c]…`，是派发包装，不是返回常量的 GetSize。**按纪律 9（停机核验）与「对不上报冲突 + [未证]，不选一个看起来对的凑」，本卡对这些类报 [未证]，不臆造尺寸。**

---

## T3 字段布局（增量双支撑，仅列本卡新证；S09-F1 已闭合部分不重做）

对每个字段要求「该类自己的写点 + 读点双重支撑」；偏移不定语义（纪律 4，跨类陷阱 +0x94/+0x184/+0x80 一律不跨类套用）。

### DisplayClass（方法体区间 v[48]=LMBUp `0x4AB9B0`、v[45]=清拖拽 `0x4AC310`、v[47]=LMBDown `0x4AC380`）

| 偏移 | 宽度 | 类型 | 写者地址（区间内全集） | 读者地址（≥3 采样） | 语义 | 分级 |
|---|---|---|---|---|---|---|
| +0x11CF | 1 | bool | 0x4ABCFD(`mov byte,0`)、0x4AC4A0(`mov byte,al`) | 0x4ABC94、0x4AC387 | **DraggingRectangle**（框选拖拽中；S09-F1 已定性，本卡补字节读写点） | [静态推断] |
| +0x11D0 | 1 | byte | 0x4ABD07(0)、0x4AC294(0)、0x4AC345(1)、0x4AC4A6(0) | 0x4AC436 | 拖拽附带状态（v45 成批清族之一，0x4AC310 内） | [静态推断] |
| +0x11B3 | 1 | bool | 0x4AC6B4/0x4AC78C(0)、0x4AC7A7(1)、0x4AC7CA/0x4AC874(0) | 0x4AC395、0x4AC496、0x4AC70B | LMBDown 模式标志（写入 0/1，读于 0x4AC380 段） | [静态推断] |
| +0x11A4 | 4 | ptr | （本区间仅读） | 0x4AB9F1、0x4ABB0A、0x4ABBB3、0x4ABBEF | **CurrentBuilding**（建筑放置指针；clue doc 同名，本卡读点坐实） | [静态推断] |
| +0x11A8 | 4 | ptr | 0x4ABB10、0x4ABB24、0x4AC45E…（W=9） | 0x4ABA35、0x4ABB20、0x4AC46F…（R≥3） | 当前放置/选择关联对象 | [未证]（读写点足，语义未坐实） |

> 全部为 `mov [ebp/esi/ecx+off]` 形式（thiscall/栈帧内 this），非跨类套用。证据 `EVIDENCE/T3_field_scan_output.txt`；脚本 `work/t3_field_scan.py`。
> 跨类警告：`+0x80`（精灵脏标记）、`+0x94`（ObjectClass 层索引）、`+0x184`（Anim DelayTimer）在 DisplayClass 不按那些语义解释；本卡未对它们下结论。

### S09-F1 已坐实、本卡对齐但不重做
侧栏 `SidebarClass+0x1544` 4×Tab、Tab 宽 `0xF94`、Cameo stride `0x34`/上限 75/Count@+0x54/Cameos@+0x58、基址 `0x880D2C`（见 S09-F1 §2/VERDICT §2）；坐标映射 `0x6D6590` 公式；选中集容器 `0xA8EC78`。这些已在 §950 入账，本卡不重复取证（见 T5）。

---

## T4 虚表槽语义（字节级；拿不到证据写 [未证]）

全部 12 条期望槽值经本卡**独立重读槽地址 4 字节**逐条复核 OK（证据 `EVIDENCE/E03_vtable_slot_semantics.txt`；脚本 `work/t4_slot_verify.py`；来源 R8_ui_crt.md §21.1，其 179/179 字节断言本卡不复述、只复核槽位现值）。

| 类 | 槽 | 槽地址 | 实现地址 | 一句语义 | 分级 |
|---|---:|---|---|---|---|
| SidebarClass | 16 | 0x7F3098 | 0x6A6C30 | Draw（每帧 UI 壳，含雷达链调用） | [已证]（槽值+源码名双源） |
| SidebarClass | 33 | 0x7F30DC | 0x6AC210 | Draw_It | [静态推断] |
| SidebarClass | 34 | 0x7F30E0 | 0x6ABD30 | tooltip/悬停 | [静态推断] |
| SidebarClass | 50 | 0x7F3120 | 0x6A5BF0 | 建按钮 | [静态推断] |
| SelectClass@Strip | 31 | 0x7F3048 | 0x6AAD00 | Cameo 点击→生产事件 | [已证]（S09-F1 复核 v[31]） |
| DisplayClass | 48 | 0x7E61D4 | 0x4AB9B0 | LMBUp 点选/框选收口 | [已证]（S09-F1 复核 v[48]） |
| DisplayClass | 47 | 0x7E61D0 | 0x4AC380 | LMBDown | [静态推断] |
| DisplayClass | 45 | 0x7E61C8 | 0x4AC310 | 清拖拽状态 | [静态推断] |
| DisplayClass | 33 | 0x7E6198 | 0x4AE4F0 | Draw_It(world) | [静态推断] |
| MouseClass | 19 | 0x7E19B0 | 0x5BDC80 | SetCursor | [静态推断] |
| MouseClass | 40 | 0x7E1A04 | 0x40D280 | RightMouseButtonUp | [静态推断] |
| CommandClass | 8 | 0x7EBE5C | 0x4C9150 | **抽象默认桩**（46 子类各自覆写 Execute） | [已证]（字节=桩 + §946 同名桩） |
| WWMouseClass | 0x38/4=14 | 0x7F7B64 | 0x7BA380 | 坐标换算(v[0x38]) | [静态推断] |
| WWMouseClass | 0x44/4=17 | 0x7F7B70 | 0x7B9D90 | ScreenToClient(v[0x44]) | [静态推断] |
| Tactical | 11 | 0x7F4374 | 0x6DC450 | WhatAmI→0x38 | [已证]（B8 38 C3） |
| Tactical | 12 | 0x7F4378 | 0x6DC460 | GetSize→0xE18 | [已证]（双向核对） |

> ⚠️ 纪律：`ret 0xC` 判据不特异（非 65/69 槽命中 672 次，§969）；本卡未用 `ret 0xC` 判任何槽语义。`0x6AAD00`(v31)/`0x4AB9B0`(v48) 的 [已证] 由 S09-F1 审计复核（VERDICT §7 可升级项），本卡只复核槽值一致。
