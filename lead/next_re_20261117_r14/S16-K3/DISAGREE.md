# DISAGREE.md — S16-K3 与既有材料的冲突引节号

> 原则：只列**实质冲突/假前提**；与 KB22 的槽位实测一致（SLOTS.md §4），无 DISAGREE。

## D1 · 与 S16-K2 `PROGRESS.md:23,25` / `E04` 的假前提 —— **本卡推翻（依据文字层）**
- 旧文：「`call 0x410320(AbstractClass::Save)`」「与 `docs/re/superweapon_re.md:708-721` 逐字吻合」，
  并据此称 `0x6CDFD0`/`0x6CE8D0` 的 Save 语义来自「基类 Save 槽号一致」。
- 反证（E02/E01）：`0x410320` 在 `.rdata/.data` dword 出现 **0 次**、在 1214 张 COL 根 vtable 作槽值 **0 次** ⇒ 非虚；
  `AbstractClass.v[6]=0x4C9150` 纯虚桩；真正 `AbstractClass::Save` 是 **slot 13 = `0x410410`**。
- 裁决：与 a-S16-K2-B ★B 一致 —— 4 条地址/语义成立，但**依据文字必须改写**；本卡已改写（LAYOUT.md §0/§2）。

## D2 · 与 `docs/re/superweapon_re.md:701-721` 的标注 —— **文档含同一假前提**
- 文档 10.1 节把 `0x00410320` 标为「`AbstractClass::Save`：Raw Struct Memory Dump，通过 `this->Size()` 写 128 字节」。
- 实测：`0x410320` 是 `E_POINTER` 守卫 + IStream 写 dword 的**共享 Save 包装器**（非虚、非类方法）；
  `AbstractClass::Save` 真身 `0x410410`（slot 13）只写 `+0x10`/`+0x20` 两个字段、无 Size() 全量 dump（KB22 §3 逐字吻合）。
- 本卡不改该文档（只读），只在此声明 `PROGRESS.md:23` 引用它是**错源**；后续引用须走本卡 E02/E01/KB22。

## D3 · 与 S16-K2 `PROGRESS.md:7` / `DOD.md:5` 的达标结论 —— **口径变更，非算术错**
- 旧文：named 83/90 = 92.22% ⇒「跨阈」，声称 S16 DoD 第 1 条达标。
- 按 STATUS_BOARD **R14-R14**（line 370-381）：DoD 判 **S**，`Class::sub_` 占位不计 ⇒ **49/90 = 54.44%，不达标**。
- 83/90 作为 **L 口径面板数**仍成立（本卡复算一致），但**不得再用于宣称 S16 跨双线**。本卡 DOD 已按 S 改写。

## D4 · 与 S16-K2 `PROGRESS.md:18` 的「不用 GetSize 判据」 —— **部分保留，部分更新**
- 旧文避开 §969 `B8 imm32 C3`（837 vs 666）与 §972 imm8 陷阱；本卡同样**不把 GetSize 当作 4 条 Save/dtor 的定名依据**（正确）。
- 但槽 12 复核仍成立：`SuperClass v[12]→0x80`、`SWT v[12]→0x100`（E01），与 §943/S16-K1 吻合；
  引用时须写清「这里是 `B8 imm32 C3` **双证**之一（配构造器 push），不是单一判据」（STATUS_BOARD line 341-344）。

## D5 · 与 S16-K2 `DOD.md:7`「本卡新增 Save/dtor 补齐存档/销毁末端」 —— **保留但降级描述**
- 补齐末端的事实成立（LAYOUT §2）；但旧卡把 4 条说成「规范型」，其中 `0x6CEFE0` 实为**复杂析构**
  （写 4 vtable + 全局 0xA8E330 注销 + 基类析构 0x4109C0），a-S16-K2-B ★B 已指出；本卡按复杂型描述。

## D6 · 与 a-S16-K2-B ★B「54 类 v[6] / 43 类 v[5]」 —— **微差，已独立复核**
- 本卡 1214 表全扫：**v[6]→`0x410320` = 54 类**（吻合）；**v[5]→`0x410380` = 41 类**（审计报 43）。
- 差异原因：审计用另一扫描窗深（本卡 `body_calls` 到首个 `ret` 止，见 `work/t2_forwarders.py`）；
  **零交叉污染结论两方一致**（v[6]→Load=0、v[5]→Save=0），不影响定名。报数差异记为口径微差，非冲突。

## D7 · 与 KB22 §0/§1.1/§3/§4 —— **无冲突**
- 三类槽表逐格复算吻合（SLOTS.md §4）：AbstractClass 24 槽、slot6 空桩、slot12 GetSize 空桩、slot13 基类块 `0x410410`、
  slot24 COL ptr；SuperClass 24 槽 / SWT 28 槽。无 DISAGREE 需报。
- 唯一措辞澄清：KB22「槽 6 = Save（抽象桩）」指**槽契约名**，a-S16-K2-B「槽 6 = Save 在 AbstractClass 上不成立」
  指**基类无真实实现**（空桩）。两者不矛盾，本卡统一按 SLOTS.md §3 表述。
