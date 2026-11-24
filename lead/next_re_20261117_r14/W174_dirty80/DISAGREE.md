# W174 · DISAGREE / 与台账 & 规范冲突

1. **§924-3 / §925-2「全镜像 `byte [reg+0x80]` 写 = 179 处 / 83 个函数，写值绝大多数是 1... ⇒ `[+0x80]` 是脏标记」**——数字成立，但**外延被否证**。本卡实证：179 写点中仅 52 处（41 函数）在 ObjectClass 族函数内（`+0x80=NeedsRedraw`，YRpp `ObjectClass.h:281`）；**111 处（31 函数）在 TeamClass 函数内**（`+0x80=StepCompleted`，YRpp `TeamClass.h:88`；`0x6E9140` 由原始 vtable `0x7F4730+0x5C` 实证为 TeamClass slot23），另 16 处类属 [未证]。故不能把 179 处统称「脏标记写点」。证据 `EVIDENCE/w174_vtable_raw_verify.txt`, `w174_class_decision.txt`。

2. **§925-2「写 1 的站点分布在大量状态变更点（`0x6E9140` 38 处、`0x6ECA70` 11 处...）」作为脏标记证据**——这两处**恰好是 TeamClass `StepCompleted`**，不是 ObjectClass 脏标记，论据失效。证据同上 + `w174_this_origin_probe.txt`（`0x6E9140` 首指令 `mov esi,ecx`，随后读写 `[esi+0x83]`=IsSuspended、`[esi+0x7d]`=NeedsToDisappear 等 TeamClass 字段簇）。

3. **§924-3「全镜像写点归因 83 函数」的方法学**（台账未写明归因法）：本卡发现若用原始 atlas 区间包含（`entry+size`），`0x6E9140`/`0x6ECA70` 等 38 处因 atlas size 低估而 [未归属]，只得 79 函数。台账 83 的函数集与 `entry_at_or_before` / M3 区间包含全等——推测台账用的是后者。这违反 W174 卡纪律第14/5条对 `entry_at_or_before` 的禁令，但结论数值正确。证据 `EVIDENCE/w174_attrib_analysis.txt`。

4. **R13_COMMON §1 作废索引第 40 行「`[+0x80]` 的精确语义 [未证]（179 写点只抽样 6 个）」**——本卡把抽样扩到全量并给出分类，同时推翻「全为 ObjectClass」的前提；但 ObjectClass 侧 `[+0x80]` 的语义（脏标记）本身**未推翻**，仍与 §925-2 一致。这是**部分一致、部分更正**。

5. **不冲突项（确认）**：写 0 的 14 处消费站点与 §925-2 完全吻合；`0x438BF0`（`cmp al,cl / je` 才置 1）与 `0x43DA80`（谓词满足才置 1）两处条件置位上下文逐字节复核无误；§925-2 把 `0x6D98EF` 写值更正为 0 是对的（本卡 `w174_writes.tsv` 该行 `src=0`）。
