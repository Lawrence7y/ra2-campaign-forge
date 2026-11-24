# SLOTS.md — S16-K3 槽契约（T1）

数据全部来自 `.rdata` 实测（vtable 定界从 COL / `vtable[−1]` / 表间边界做，不用 atlas 反推），
RTTI 走 `COL + 0xC → TD + 8` 内联名（读不到 fail-closed）。复跑 `work/t1_slots.py` → `EVIDENCE/E01_t1_slots.txt`。

## 0. 三类主虚表身份（RTTI 自走链）

| 类 | 主 vtable | COL (`vtable[−1]`) | TD | RTTI 名 | off | 码槽数 | 终止符 |
|---|---|---|---|---|---|---|---|
| AbstractClass | `0x007E1F50` | `0x007FB118` | `0x008177C8` | `.?AVAbstractClass@@` | 0 | **24** | slot24 = COL ptr `0x7FB160` → `.?AVINoticeSource@@`（INoticeSource 子表，不是第 25 个函数） |
| SuperClass | `0x007F3FE8` | `0x0080B610` | `0x008423E0` | `.?AVSuperClass@@` | 0 | **24** | slot24 = `0x00000000` 非码 |
| SuperWeaponTypeClass | `0x007F4090` | `0x0080B6C8` | `0x00842600` | `.?AVSuperWeaponTypeClass@@` | 0 | **28** | slot28 = `0x44610000` 浮点常量非码（末码槽 v[27]=`0x6CEF80`） |

- 三类各有 4 张 vtable（off = 0 / 4 / 8 / 12），主表取 off=0；这与 S16-K1 §943 / a-S16-K2-B ★E 一致。
- SWT 28 槽 = AbstractTypeClass 27 槽 **+1**（该类新增 1 个虚函数），SuperClass 24 槽 = AbstractClass 24 槽（只覆写），均 ≥ 基类，自洽。

## 1. 关键槽逐格（三类对照）

| 槽 | AbstractClass | SuperClass | SuperWeaponTypeClass | 契约（KB22 §0） |
|---:|---|---|---|---|
| 0 | `0x410260` | `0x410260` | `0x410260` | QueryInterface |
| 1 | `0x410300` | `0x410300` | `0x410300` | AddRef |
| 2 | `0x410310` | `0x410310` | `0x410310` | Release |
| 3 | **`0x4C9150`** | `0x6CDEB0` | `0x6CE7C0` | GetClassID（抽象桩 / 覆写） |
| 4 | `0x410450` | `0x410450` | `0x410450` | IsDirty |
| 5 | **`0x4C9150`** | `0x6CDEF0` | `0x6CE800` | **Load**（抽象桩 / 覆写；覆写体首调 `0x410380`） |
| 6 | **`0x4C9150`** | **`0x6CDFD0`** | **`0x6CE8D0`** | **Save（COM, IStream\*+BOOL）**（抽象桩 / 覆写；覆写体首调 `0x410320`） |
| 7 | `0x4103E0` | `0x4103E0` | `0x4103E0` | GetSizeMax |
| 8 | `0x4105A0` | **`0x6CE220`** | **`0x6CEFE0`** | 标量删除析构 |
| 9 | `0x410470` | `0x410470` | `0x410470` | Init |
| 10 | `0x410480` | `0x6CDFF0` | `0x410480` | PointerExpired |
| 11 | `0x4C9150` | `0x6CE200` | `0x6CE8F0` | WhatAmI（抽象桩 / 覆写） |
| 12 | **`0x4C9150`** | `0x6CE210`→`0x80` | `0x6CE900`→`0x100` | **Size/GetSize**（抽象桩 / 覆写） |
| 13 | **`0x410410`** | `0x6CE020` | `0x6CE910` | **AbstractClass::Save（基类序列化块）** |
| 14 | `0x410490` | `0x410490` | `0x410490` | CalculateChecksum |
| 15–23 | 同 KB22 | 同 KB22 | 同 KB22（16 为覆写） | 见 KB22 §0 |
| 24 | COL ptr（停） | `0`（停） | `0x410C20` | AbstractClass 在此换 INoticeSource 子表 |
| 25–27 | — | — | `0x410B90`/`0x6CEA20`/`0x6CEF80` | SWT 补槽（25=`LoadFromINI` 基类, 27 末槽） |

## 2. 任务点名三问（实测回答）

1. **槽 6 是什么？** = COM `IPersistStream::Save(IStream*, BOOL)`。**在 AbstractClass 上确为纯虚桩
   `0x4C9150` = `33 C0 C3`（`xor eax,eax; ret`）**——已实测确认（E01 slot6）。审计 a-S16-K2-B ★B 的断言成立。
   派生类（SuperClass/SWT 等 54 类）把它覆写成调用共享包装器 `0x410320` 的函数。
   ⇒ 需注意区分「槽 6 的**契约名**是 Save」与「AbstractClass.v[6] 的**实现**是空桩」；
   后者意味着**不能**从「基类槽 6 有 Save 实现」推导派生函数的语义（这正是旧卡的假前提之一）。

2. **槽 12 是什么？** = `Size/GetSize`。AbstractClass 自身是抽象桩 `0x4C9150`；
   派生覆写为 `B8 <imm32> C3`：`SuperClass v[12]=0x6CE210 → 0x80`、`SWT v[12]=0x6CE900 → 0x100`，
   与 S16-K1 §943 构造器分配 `push 0x80` / `push 0x100` 双向核对吻合（已入账，本卡复核保持一致）。

3. **槽 13 是什么？** = **基类序列化块 `AbstractClass::Save`**（KB22 §3）。实测 `AbstractClass.v[13]=0x410410`，
   函数体写 `+0x10`(UniqueID, dword) 与 `+0x20`(Dirty, bool) 两个字段后 `ret 4`，
   与 KB22 §3 逐字吻合 ⇒ **KB22 对齐，无冲突**。派生类 `SuperClass v[13]=0x6CE020`、`SWT v[13]=0x6CE910` 覆写。

## 3. 「Save 到底在哪个槽」——全项目一致结论

**两个不同的 Save，两个不同的槽，KB22 §1.1 已明确区分，本卡实测完全吻合：**

| 概念 | 槽号 | 基类实现 | 语义 |
|---|---:|---|---|
| COM `IPersistStream::Save(IStream*, BOOL)` | **6** | `AbstractClass.v[6]=0x4C9150`（空桩） | 引擎存档入口；派生覆写调 `0x410320`（共享包装器，非虚） |
| `AbstractClass::Save`（基类序列化块） | **13** | `0x410410` | 只写 `+0x10`/`+0x20` 两字段，是槽 6 覆写体的被调者 |

⇒ 给审计员的单一答案：**「存档入口 Save」= 槽 6**；**「AbstractClass::Save 函数名所指的序列化块」= 槽 13**。
0x6CDFD0 / 0x6CE8D0 位于槽 6，正确定名是 `SuperClass::Save` / `SuperWeaponTypeClass::Save`（COM Save），
**不是** `AbstractClass::Save`，也不是「槽 13 的 Save」。

## 4. 与 KB22 的对账结论

- 槽 0–13 的**地址与定名逐格吻合** KB22 §0/§1.1/§3；槽 24 是 COL 指针（KB22 §4.1）亦吻合。
- **无 DISAGREE 需报**（KB22 与实测一致）。唯一要澄清的是措辞：KB22 写「槽 6 = Save（抽象桩）」，
  a-S16-K2-B 写「槽 6 = Save 在 AbstractClass 上不成立」——两者不矛盾：前者说的是**槽契约名**，
  后者说的是**基类无真实实现**（空桩）。本卡统一按此口径表述。
