# W3-DOCFIX-1 · 修 `ARCHITECTURE_ATLAS.md` §0.1 的「主程序区 EIP 上界」——**gate 级缺陷 E-W3B-09**

> 来源：W3-Q7（QC-S2，Qoder CN）独立复核，见 `out/re_work/qc/W3_20261001/atlas_w3b/REPORT.md` `[0]` 第 3 条。
> 写域：**`docs/re/ARCHITECTURE_ATLAS.md` 单文件**（**append-only：只加注，不改原句、不删行**）。
> 派发背景：原 docs 写域属 Antigravity，但其额度已用尽（`Resets in ~54m`）⇒ 本卡**可由任一 harness 承接**。

## 1. 缺陷（原文摘录）

> **最大风险**：新发现 **E-W3B-09** —— ATLAS §0.1 工程公理把"主程序区"EIP 上界写成 **`0x008A0000`**，实测 **`ImageBase+SizeOfImage = 0x00B96000`**，**少 3 MB**；现写法会把 gamemd 内部 EIP（含 `.rsrc`/`.detour`/高段 `.data`）误判为"外部系统/驱动"，**动摇崩溃一票否决闸门**。

## 2. 为什么这是 gate 级

项目有一条**崩溃一票否决**闸门：真机崩溃时若 EIP 落在"主程序区"内 ⇒ 判为**我方代码责任**；落在"外部系统/驱动" ⇒ 判为环境问题可豁免。
上界写到 `0x008A0000` 时：
- `.rsrc` 约在 `0x00B7A000`、`.detour` 亦在高段、高段 `.data` 同样越过 `0x8A0000`
- ⇒ **真实属于 gamemd 自身的崩溃点会被归类成"外部系统/驱动"而豁免** ⇒ **闸门被绕过**。

**这与 Lead 的 `E-W3-01` 是同一个盲区的两次显形**：`E-W3-01` 是"用 `VA − 0x400000` 当 FileOffset 通式"，`E-W3B-09` 是"假设映像在 `0x8A0000` 就结束了"。**两处都源于"以为镜像只有 `.text/.rdata/.data` 三段"**。
（`E-W3-01` 已在 `docs/re/AGENT_TASK_TEMPLATE.md` 等 5 处落地，见 §3。）

## 3. 要做的事（**严格 append-only**）

1. **先自行复算**（不得直接采信 QC-S2 的转述）：
   - 从 `ra2youli/gamemd.exe` 读 `IMAGE_OPTIONAL_HEADER.SizeOfImage`，算 `ImageBase + SizeOfImage`
   - 列出**全部 5 个节**的 `VirtualAddress + max(VirtualSize, SizeOfRawData)`，取最大值，与上一步互相印证
   - 给出 `0x008A0000` 与真实上界之间的区间里**究竟有哪些节**
   - 若复算结果与 QC-S2 不符，**以其为准并单列勘误**，不要迁就
2. 在 ATLAS §0.1 该条**原地不动**的前提下，**紧随其后**插入一条加注块：
   ```
   > 【W3 勘误 E-W3B-09】原句「主程序区 EIP 上界 = 0x008A0000」**不成立**。
   > 实测 `ImageBase(0x400000) + SizeOfImage(<你复算的值>) = <结果>`；该区间内还含 `.rsrc`(<VA>) / `.detour`(<VA>) / 高段 `.data`。
   > ⇒ 用 `0x008A0000` 会把 gamemd 自身 EIP 误判为「外部系统/驱动」，**使崩溃一票否决闸门失效**。
   > 正确上界应采用 **`ImageBase + SizeOfImage`**（<值>）；依据：<你的复算命令与输出>；分级：[实证]
   > 参见：out/re_work/qc/W3_20261001/atlas_w3b/REPORT.md · 同源缺陷 E-W3-01（FileOffset 通式）
   ```
3. **顺手核对**：全库是否还有别处也用了 `0x008A0000` 或等价的"映像止于 8A0000"假设（`grep -rn "8A0000\|0x8a0000" docs/ tools/ ra2render/`）。有则**逐处加同样的注**。

## 4. 交付与门禁

- 交付：修订后的 `docs/re/ARCHITECTURE_ATLAS.md`；**并给出一份 `DOCFIX_EVIDENCE.md`**（写哪一行、插入行号、复算命令与原文输出、before/after 行数）
- **append-only 自证**：给 `before/after` 行数 + 用有序子序列判定证明**零行删除**（参照 `out/re_work/agy/W3_20261001/docs_landing/verify_docs_landing.py` 的断言 3 做法）
- 门禁：`python tools\verify_anchors.py` 须 **323/323 PASS**（原文粘贴）
- **不得**改 `ra2youli/**`、`ra2bench/**`、`ra2render/**`、`tools/**`、`out/re_work/qc/**`
- 回报 `[0]` 直接答：**复算出的真实上界是多少 / 与 `0x008A0000` 差多少 / 全库还有几处同源假设 / append-only 是否零删除**
