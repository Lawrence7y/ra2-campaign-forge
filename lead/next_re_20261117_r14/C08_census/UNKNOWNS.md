# C08 · UNKNOWNS（未证 / 待 P1 细化）

本文件记录本片普查中**未能证明**的部分。所有一行语义均为 `[未证]` 猜测，未写新 `[已证]` 发现。

## 1. 309 个零证据函数（source=none → S22 兜底）
- `EVIDENCE/classification_trace.tsv` 中 `source==none` 共 **309** 行：无 self_known 名、无 vtable 槽（真实槽数下）、无源文件模块、无强字符串、无亲戚名投票、无导入 API。
- 全部归 S22 仅为兜底，**不是已证归属**。集中在 0x6E–0x70 段（Swizzle/存档小 wrapper、Team/AI 内联方法）与 0x71 尾段（TeleportLocomotion 周边未具名 wrapper）。
- 建议 P1 用 YRpp 头文件地址名二次扫描 / re_atlas kb 具名方法再细化。

## 2. 284 个 TClassFactory 泛型工厂方法（归 S22，实例化类型未用于归属）
- 本片 0x6BF750 起有约 71 组 `TClassFactory<V*>` 虚表，每组 4 槽（Create/Find/…），共 **284 函数**。已验 `0x6BF750`/`0x6BF8D0`/`0x6BFA50` 的 slot0 body **MD5 完全相同**（`8b44240c5385c07509 b803400080 5bc20c00…`），与实例化 T（Tactical/Cell/EMPulse）无关 ⇒ 泛型基础设施，一律归 S22 core=False（med），**不按嵌入 T 虚高判级**。
- 这些方法对具体 T 的语义（创建/查找哪类对象）`[未证]`；P1 可按其静态实例全局（如 `0x7F7C90`）与调用链反推每种工厂的服务对象。这是相对 C05/C06「模板类按元素类型归 core」的**有意修正**，见 DISAGREE.md。

## 3. 三通道 atlas 空洞（call32 2 / jmp32 2 / jmp8 37 = 41 行 / 41 独立地址）
口径见 `PROGRESS.md` 核心数字 3。未证部分：
- **37 个 jmp8 洞目标**：引用站点 100% 在洞内（sites_in_fn=0 或引用站点 owner=None），首指令分布 mov/push/test/cmp/rep movsd 等，形态为**未建模代码块内短跳分支标签**。按 R14-R1 判据（align16 + prev∈{nop,ret,jmp} + 非分支标签）**不计入疑似真入口**。若干地址首指令是 `test eax,eax ; jne`（如 `0x6E1E7C`/`0x6E1EDC`/`0x6E1F3C` 等 7 处），明确是循环/判空分支标签。
- **1 个 jmp32 非入口**（`0x6CA204`）：align16=0（末位 4）、prev=other、首指令 `mov edx,[esp+0x14]`，引用站点 `0x6CA288` 在同一洞内 ⇒ 洞内分支标签，不计入疑似真入口。
- **1 个 jmp32 疑似真入口**（`0x6C89D0`）：align16=1、prev=nop、首 `mov eax,[ecx+4] ; test ; je`，非分支标签首指令，形态像小 getter/inline 方法；但其引用站点 `0x40F295` 与两个 call32 的站点（`0x6C6C6F`/`0x6E8154`）同在洞内（owner=None），即**调用方也未被 atlas 建模**。按 R14-R1 三判据计入疑似真入口，但「引用来自未建模块」这一事实 `[未证]`，需 P1 证真。
- **疑似真入口合计 3 是上界**：verify_core（第三通道 pefile+op_str）独立复算同为 3，地址集合 `{0x6C8900, 0x6E8000, 0x6C89D0}` 一致。
- boundary_check：本片 41 目标均为指令边界或洞内标签，未出现 span≥max_bytes 的 bail；若出现按纪律 #3 保留 None 不当 False。

## 4. 模板容器类的归属（本卡已修正，与其他片口径不同）
- 类型如 `T_DynamicVectorClass_PAVSubTitle__`、`T_VectorClass_VSwizzlePointerClass__`、`T_DistributionObject<...>` 等，C05/C06 按「字符串包含匹配」把元素类型对应的 Sxx 判为 core（计入 high）。C06 UNKNOWNS §4 已标注这是固有偏差并建议 P1 统一修正。
- 本卡实现该修正：`GENERIC_WRAPPERS`（TClassFactory/VectorClass/DynamicVectorClass/DiscreteDistributionClass/DistributionObject）先于 core 规则识别，一律归 S22 core=False。后果：本片 TClassFactory 284 + 模板容器若干不再虚高，S06/S13/S19 的 high 归 0（这些子系统在本片仅有泛型工厂虚表，无 core 类直接命中）。见 DISAGREE.md。

## 5. 具名函数语义仍为猜测 / 本片已证地址照引不推翻
- 101 个 `[已证]` 仅证明「名字来自 YRpp/kb 地址名」，不证明其一行语义（如 `SuperClass::SetCharge`、`TeamClass::AI`、`TacticalClass::RegisterDirtyArea` 的具体行为）。语义列均按名推测，标 `[未证]`。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`；本片地址段内若涉及已证事实均按台账原结论引用，本卡不推翻、不新增 `[已证]`。台账 §923–§928 的具名地址（矿石价值 0x485020、绘制链 0x5F4B10/0x5F4D30/0x5F5F40 等）均在 C05/C06 片，本卡未触碰。本片唯一台账直接命中是 `0x006E8000`（§877「不在函数图谱内、未验」的 AbstractClass 数组零引用候选），本卡仅列为疑似真入口，与台账「未验」口径一致。
