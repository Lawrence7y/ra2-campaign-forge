# R122 跨家族审计报告（hy4 审计员，独立复算）

- 审计对象：`/home/t628/projects/ra2-campaign-forge/_r122/r122a_objs35.{py,json}`、`r122b_allvec.{py,json}`、`r122f_reconcile.{py,json}`、`ra2bench/gamemd.exe`
- 本报告全部数字来自 `_r122/audit2/recalc.py` 的实际输出 `_r122/audit2/recalc.out`；引用格式 `[TAG]` 表示 recalc.out 中同名行的输出。
- 实测 `gamemd.exe` SHA-256：`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（`[SHA256]`）；与三份产物中登记的 SHA 一致。
- Capstone 版本：5.0.7（`[CAPSTONE]`）。
- 复算脚本自测：`[SELFTEST]` 三行全部 PASS（正控、空边界负控、skipdata 关闭负控）。
- 内存纪律：`md.detail=False`，全段只用 `disasm_lite`，边界集合存整数 `set`，没有把全量 detail 对象常驻。

## 结论摘要

1. “提前中断”归因成立且被实测复现：skipdata 关闭时停在 `0x46f5a0`，仅覆盖 452000/4063232 字节；开启时覆盖到 `0x7e1000`。主会话把残缺边界当全集，导致 r122f 的 F1/F2 FAIL。
2. 正确边界（skipdata 开启）下：raw 目标 1159 / 站点 1777；clean 目标 1142 / 站点 1748；丢弃 17 目标 / 29 站点。VectorClass 族 clean 目标 142（35 内 + 107 外）。
3. 严格双形态（恰 2 次写入、恰 1 Dynamic + 1 Vector、同元素）：总数 138 = 35 内 + 103 外。主会话 r122f 的 `dual_form` helper 实际不是严格定义，但其偶然给出同样的 103 外。
4. `0x00abfda0` 有 **9 个**真实写入站点：1 个 Dynamic、1 个 Vector、7 个重复 Dynamic。严格定义不满足；只满足“至少各一个”的宽松定义。因此 deepseek 的 104 是宽松口径，主会话的 103 在严格定义下正确；但两家的 helper 都不够严谨，应统一到严格定义。
5. r122a 与 r122b 共 35 条 ck() 断言中，绝大多数是二进制事实检查；但存在 1 条占位断言、若干命名大于 cond 的弱断言，以及 S5a/S5b 两条“假反控”（它们验证的是 `rd()`/`name_of_vtable()` helper 的行为，不是独立二进制事实）。详见 A5。

---

## A1 两种 capstone 扫描模式（全段 .text）

`.text`：base `0x401000`，原始字节 4063232，末地址 `0x7e1000`（`[TEXT]`、`[SECTION] .text`）。

| 项目 | skipdata=False | skipdata=True |
|---|---:|---:|
| 指令条数 | 155215 | 1394186 |
| 最后一条结束地址 | `0x46f5a0` | `0x7e1000` |
| 覆盖字节数 | 452000 | 4063232 |
| 是否到达 .text 末地址 | 否 | 是 |
| `.byte` 伪指令条数 | 0 | 66 |
| 边界集合大小 | 155215 | 1394120 |

数据来源：`[A1_OFF]`、`[A1_ON]`。探针：`0x46f5a0` 与 `0x7e1000` 在两种边界集合中均不存在（`[A1_PROBE]`），因为边界集合记录的是指令**起始地址**，不是结束地址；这不影响判定。

**判定**：主会话对 F1/F2 的归因成立。skipdata 关闭时确实在 `0x46f5a0` 提前停住，只覆盖 452000 字节；把 155215 个残缺边界当全集，会误杀大量合法站点。`[SELFTEST] PASS :: negative: skipdata 关闭能复现扫描中断` 独立复现了这一点。

---

## A2 正确边界下的 c7 05 写 BSS 重算

raw 口径为纯字节扫描 `c7 05 <BSS>, <imm32>`；clean 口径要求每个站点的起始地址在 skipdata=True 的边界集合中。

| 指标 | 数值 | 输出行 |
|---|---:|---|
| 全段 `c7 05` 字节命中 | 1971 | `[RAW]` |
| raw 目标数 | 1159 | `[A2_RAW]` |
| raw 站点数 | 1777 | `[A2_RAW]` |
| clean 目标数（skipdata=True 边界） | 1142 | `[A2_A3_ON]` |
| clean 站点数 | 1748 | `[A2_A3_ON]` |
| 被丢弃目标数 | 17 | `[A2_A3_ON]` |
| 被丢弃站点数 | 29 | `[A2_A3_ON]` |

对比 r122f 报的 1159 / 709：raw 目标数一致；r122f 的 clean 目标 709 是错误边界造成的。作为反证，用 skipdata=False 的残缺边界重算，clean 只有 136 目标 / 168 站点，丢弃 1023 目标 / 1609 站点（`[A2_A3_OFF]`），量级与 r122f 的 709 相符，进一步支持归因。

---

## A3 VectorClass 族与双形态重算

分类定义：clean 口径下，目标任一写入站点的 vptr 经 MSVC RTTI 解析后名字含 `VectorClass@` 即计入族（Dynamic 与 Vector 都含该子串）。双形态严格定义：恰 2 次写入，且恰 1 个 `.?AV?$DynamicVectorClass@` + 1 个非 Dynamic 的 `.?AV?$VectorClass@`，且两者元素类型相同。

| 指标 | raw（无边界） | clean（skipdata=True） | 输出行 |
|---|---:|---:|---|
| VectorClass 族 BSS 目标 | 142 | 142 | `[A2_A3_ON]`、`r122b` JSON |
| 其中 35 内 | 35 | 35 | `[A2_A3_ON]` |
| 其中 35 外 | 107 | 107 | `[A2_A3_ON]` |
| 严格双形态总数 | 138 | 138 | `[A2_A3_ON]` |
| 严格双形态 35 内 | 35 | 35 | `[A2_A3_ON]` |
| 严格双形态 35 外 | 103 | 103 | `[A2_A3_ON]` |
| 宽松“≥1 Dynamic + ≥1 Vector”35 外 | 104 | 104 | `[A2_A3_ON]` 的 `looseOutside35` |

来源行均为 `[A2_A3_ON]`。raw 与 clean 在这些族/形态计数上一致，是因为被边界丢弃的 17 个目标都不是 VectorClass 族；差异只体现在 clean 目标总数（1142 vs 1159）。

`[A2_A3_OFF]`（残缺边界）得到 vec=20、严格双形态=18，说明 skipdata 关闭会严重破坏族统计。

---

## A4 对象 `0x00abfda0` 逐站点判定

`[A4_HEADER]`：raw 站点 9 个，skipdata=True clean 站点也是这 9 个；skipdata=False 的残缺边界集合里 0 个。9 个站点全部在正确边界上（`[A4_SITE]` 的 `in_ON_BOUNDS=True`）。

原始 10 字节与 RTTI 解析（`[A4_SITE]`）：

| # | 站点 | 原始 10 字节 | vptr | RTTI 类名 |
|---:|---|---|---|---|
| 1 | `0x5d5af1` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 2 | `0x5d5b28` | `c705a0fdab0040ed7e00` | `0x7eed40` | `.?AV?$VectorClass@PAVMultiplayerGameMode@@@@` |
| 3 | `0x5d5e45` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 4 | `0x5d5ea5` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 5 | `0x5d5f01` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 6 | `0x5d604d` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 7 | `0x5d60a0` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 8 | `0x5d6181` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |
| 9 | `0x5d61d4` | `c705a0fdab0020ed7e00` | `0x7eed20` | `.?AV?$DynamicVectorClass@PAVMultiplayerGameMode@@@@` |

即：1 个 Vector 写入 + 8 个 Dynamic 写入（其中 7 个是重复写入同一 vptr `0x7eed20`），元素类型均为 `PAVMultiplayerGameMode`。

**判定**（`[A4_VERDICT]`）：
- 严格定义（恰 2 次写入）：**不满足**。
- 宽松定义（至少各一个）：**满足**。
- r122f 的 `dual_form` helper 实际口径（名字列表里恰 1 Dynamic + 1 Vector）：也不满足，因为它要求各 1 个名字；`0x00abfda0` 有 8 个 Dynamic 名。遍历结果显示该 helper 的 outside 集合与严格定义完全相同，差集为空（`[A4_DUAL_HELPER_DIFF]`）。

**103 vs 104 差异判定**：
- `0x00abfda0` 是一个“同元素 Dynamic+Vector 形态”对象，但不是“恰好 2 次写入”的对象。
- 主会话报的 outside=103 对应严格定义（也对应 r122f helper 的实际行为）；deepseek 报的 104 对应宽松“≥1 each”定义。
- 若采用任务卡给出的严格定义，**主会话的 103 正确，deepseek 的 104 多算了 `0x00abfda0`**。但主会话 r122f 的 helper 表述与实现不符，必须补上 `len(sites)==2` 检查，避免使用“严格”名义却靠偶然一致。

补充：`[A4_SYMDIFF_STRICT]` 显示 raw 与 clean 的严格 outside 集合对称差为 0，说明 `0x00abfda0` 不是边界过滤造成的差异，而是口径定义差异。

---

## A5 r122a / r122b 的 ck() 断言逐条审计

cond 列摘自脚本源码中的 `ck(name, cond, detail)` 第二个实参；验证内容列是审计员对 cond 的独立解释；“一致”列判断断言名是否准确描述了 cond 真正验证的内容。

### A5.1 r122a_objs35.py（24 条）

| # | 断言名 | cond 实际表达式 | 真正验证了什么 | 一致 | 问题/应改 |
|---:|---|---|---|---|---|
| 1 | S2a 孪生函数被 call rel32 指向的入口数 | `len(calls) == 36` | `calls` 中不同 call 目标数恰 36（35 孪生 + 1 个 `0x680f70`） | 一致 | 无。建议 detail 注明第 36 个入口地址。 |
| 2 | S2b 站点总数 | `total_sites == 37` | 所有 call 目标的站点数合计 37 | 一致 | 无。 |
| 3 | S2c R121 的 35 站全在本次重扫结果里 | `set(R121_TWINS) <= set(CK_SITES)` | 硬编码的 35 站集合是重扫站点集合的子集 | 一致 | 无。这是拿硬编码 R121 清单验证重扫结果，方向合理。 |
| 4 | S2d 多出的 2 站 | `sorted(set(CK_SITES) - set(R121_TWINS)) == [0x67d193, 0x67e62b]` | 重扫站点相对 R121 清单恰好多出两个指定地址 | 一致 | 无。 |
| 5 | S2e 35 站前置指令全为 mov edx,imm32 | `len(cands) == 35 and not bad_shape` | 35 站的 `site-7` 字节为 `ba`，`site-2..-1` 为 `8b ce` | 基本 | cond 只查固定偏移字节形态，没有用 capstone 验证指令边界。应改为在边界集合中要求 `site-7` 是 `mov edx, imm32` 起点且长度 5，下一站 `site-2` 是 `mov ecx,esi` 起点。 |
| 6 | S2f 35 个 edx 互不相同 | `len(set(EDX)) == 35` | 35 个提取出的 edx 值互异 | 一致 | 无。 |
| 7 | S1a 35 个 edx 全在 .data 节 | `all(r[1] == '.data' for r in regs)` | 每个 edx 经 `sec_of` 落在 `.data` 虚拟范围 | 一致 | 无。 |
| 8 | S1b 35 个 edx 全在 .data 的 BSS（无文件字节）区 | `all(r[0] == 'BSS' for r in regs)` | 每个 edx ≥ `.data` 原始字节末端 | 一致 | 无。 |
| 9 | S1c BSS 区边界 | `all(BSS_LO <= a < BSS_HI for a in EDX)` | 35 个 edx 落在计算出的 BSS 区间内 | 一致 | 与 S1b 重复；保留即可。 |
| 10 | S1d 读 BSS 字节必须被拒 | `rd(EDX[0], 4) is None` | 自己写的 `rd()` helper 拒绝越过 SizeOfRawData 的读取 | **假反控** | 验证的是脚本 helper 行为，不是独立二进制事实。应改为：用 PE 段表断言 `EDX[0] >= .data.va + .data.SizeOfRawData`（已有 S1b），并删除本条或改名为“rd() 拒绝 BSS 读”。 |
| 11 | S2g c7 05 写 BSS 的目标总数 > 1000 | `len(writes) > 1000` | 纯字节扫描的 BSS 目标数超过 1000 | 部分 | 名字说“目标总数”，cond 只验证 >1000。应改为 `len(writes) == 1159` 并同时断言站点数 1777。 |
| 12 | S2h 35 个目标全被 c7 05 写过 | `all(a in writes for a in EDX)` | 35 个 edx 都是 raw 写入目标 | 一致 | 无。 |
| 13 | S2i 35 个目标每个恰好被写 2 次 | `list(per.items()) == [(2, 35)]` | 这 35 个目标在 raw 口径下每个恰 2 个写入站点 | 一致 | 无。注意这是 raw 口径；若改 clean 口径数字会变，应注明。 |
| 14 | S2j 全库里恰好 2 次写入的目标 < 25% | `0 < n_two < 0.25 * len(writes)` | 全库恰好 2 次写入目标占比 <25% | 部分 | cond 只验证比例，不足以推出 detail 宣称的“不是口径假象”。应补充这 241 个目标的站点都在边界集合内，并用 skipdata=True 边界重算。 |
| 15 | S3a 70 次 vptr 写入全部解析出 RTTI 类名 | `all(w['name'] for o in objs for w in o['writes'])` | 70 个写入点的 vptr 经 COL/TD 链能解出以 `.?AV` 开头的名字 | 一致 | 应补断言 vptr 落在 `.rdata` 且 COL signature=0 的计数，避免 helper 偶然通过。 |
| 16 | S3b 70 个类名互不相同 | `len({w['name'] for o in objs for w in o['writes']}) == 70` | 70 个类名字符串互异 | 一致 | 无。 |
| 17 | S3c 70 次写入全是 VectorClass/Dynamic 族 | `all('VectorClass@' in (o['writes'][0]['name'] or '') and 'VectorClass@' in (o['writes'][1]['name'] or '') ...)` | 每对象两站名字都含 `VectorClass@` | 部分 | 只查了两个站；若每对象写入数不是 2 不会被发现。应加 `len(o['writes'])==2`（S2i 已覆盖，但本条应自含）。 |
| 18 | S3d 每对象 = 一个 Dynamic 体 + 一个 Vector 体 | `order_ok == 35`，其中 `dyn = 'DynamicVectorClass@' in a`、`vec = 'DynamicVectorClass@' not in a and 'VectorClass@' in a`，只检查第一站是 Dynamic、第二站是 Vector | 仅验证 35 个对象里第一站 Dynamic、第二站 Vector 的数量 | **名字大于 cond** | cond 依赖 `w[0]`/`w[1]` 的排序，没有显式要求每对象恰 2 站。应改为按名字集合判定恰 1 Dynamic + 1 Vector，并加 `len(writes)==2`。 |
| 19 | S3e 两 vtable 元素类型相同 | `same_elem == 35`，比较 `a.split('VectorClass@')[1].split('@@@')[0]` | 前两站解析出的元素字符串相同 | 部分 | 若对象有 >2 站，本条只看前两站。应改成遍历全部名字并先断言恰 2 站。 |
| 20 | S3f 元素类型全为 PAV* | `all(e.startswith('PAV') for e in elems)` | 35 个 `elems` 字符串都以 `PAV` 开头 | 部分 | `elems` 只取 `o['writes'][1]`（第二站），漏掉第一站。应对全部 70 个名字解析出的元素类型做检查。 |
| 21 | S3g 35 个元素类型互不相同 | `len(elems) == 35` | `elems` 集合大小为 35 | 部分 | 同 S3f，`elems` 来自第二站；应改成全部站点。 |
| 22 | S5a 反控：edx+1 解不出合法类名 | `all(x[0] is None for x in c1)`，`c1 = [name_of_vtable(u32(a + 1) or 0) for a in EDX[:10]]` | 把 edx+1 当指针读 4 字节，再喂给同一个 `name_of_vtable`，检查返回 None | **假反控** | 验证的是自己 helper 对错位输入的反应；`u32(a+1)` 读的是 BSS（实际会被 `rd` 拒绝，返回 None→0→`name_of_vtable(0)`），所以必然失败。应改成：在 `.rdata` 里找真实存在的另一个 vptr，断言其类名不同于本对象；或直接用 PE 段表断言 `edx+1` 不是任何已知 vptr。 |
| 23 | S5b 反控：vptr+4 解不出合法类名 | `all(x[0] is None for x in c2)`，`c2 = [name_of_vtable(v + 4) ...]` | 真实 vptr +4 后喂给 `name_of_vtable`，检查返回 None | **假反控** | 同样是 helper 行为；而且 vptr+4 落在另一个 vtable 槽位，可能合法但 RTTI 不同。应改成断言 `name_of_vtable(v+4)` 的结果不等于原类名（若非 None），并检查它落在 `.rdata` 内；不要要求 None。 |
| 24 | S5c 正控：真实 vptr 解得出类名 | `all(x[0] for x in c3)` | 前 10 个对象第二站的 vptr 能解出名字 | 一致 | 无。 |

### A5.2 r122b_allvec.py（11 条）

| # | 断言名 | cond 实际表达式 | 真正验证了什么 | 一致 | 问题/应改 |
|---:|---|---|---|---|---|
| 1 | B0 重算得 35 个对象 | `len(OBJ35) == 35` | 排除两个非孪生站后，call 前导提取出的不同 edx 有 35 个 | 一致 | 与 r122a S2f 有重复；可接受。 |
| 2 | A1 VectorClass 族 TD 数量 > 300 | `len(VEC_TD) > 300` | `.?AV?$` 开头的 RTTI 名里匹配 VectorClass 模板的 TypeDescriptor 数量 >300 | 部分 | 名字说“数量 >300”，cond 就是阈值；建议写实际期望 396 并断言，避免阈值过松。 |
| 3 | A2 VectorClass TD 占全部 RTTI 名的比例 | `len(VEC_TD) < len(TD_NAMES)` | 族 TD 数小于全部 RTTI 名数 | **占位/弱断言** | 这是几乎必然为真的弱条件（detail 给出 396/634）。改名“族 TD 不是全部 RTTI”，或改成 `len(VEC_TD) == 396 and len(TD_NAMES) == 634`。 |
| 4 | B1 写入侧扫到 c7 05 写 BSS 的站点数 | `sum(len(v) for v in BSS_WRITES.values()) > 1000` | raw 站点数 >1000 | 部分 | 名字说“站点数”，cond 只是 >1000。应改成 `== 1777` 并同时断言目标数 1159。 |
| 5 | B1b UNRESOLVED 归因：不是全部节外 | `_land['sentinel(0/0xffffffff)'] > 0 and _land['above-all-sections'] > 0` | 至少有一个哨兵值和至少一个高于所有节的 imm32 | **名字大于 cond** | detail 说“多数是哨兵值”，但 cond 只要求各 >0。应改为 `sentinel > above_all + inter_gap + ...` 或直接断言 792 是最大类。 |
| 6 | B2 全库 VectorClass 族全局静态对象数 | `len(ALL_VEC_OBJS) >= 35` | raw 口径下至少被一次 VectorClass vptr 写入的 BSS 目标数 ≥35 | **名字大于 cond** | 断言名说“全库…数”，cond 只验证下界 35。应改成 `== 142`（正确边界下也是 142）。 |
| 7 | B3 35 个是它的子集 | `set(OBJ35) <= set(ALL_VEC_OBJS)` | 35 个 edx 目标都在 ALL_VEC_OBJS 中 | 一致 | 无。 |
| 8 | B4 存在 35 之外的其他对象 | `len(EXTRA) > 0` | 35 外至少有 1 个 | 部分 | 名字说“存在”，cond 只要求 >0；建议写实际 107。 |
| 9 | B5 35 个各自恰一个非 Dynamic Vector vtable | `all(v is not None for v in s35_elem.values())` | 对每个 35 目标，`names` 里非 Dynamic 名字恰 1 个 | 一致 | `vtable_name` 失败会被忽略为 None，但名字仍算；可接受。 |
| 10 | B6 35 外“Dynamic+Vector 同元素”形态数 | `len(extra_dual) > 0` | 35 外满足“恰 1 Dynamic + 1 Vector 且元素相同”的对象至少 1 个 | **名字大于 cond** | 名字是“对象数（决定 35 是否=全体）”，cond 只验证 >0。应改成 `== 103`，并明确“恰 2 次写入”还是“至少各一次”。 |
| 11 | B7 35 外同形态对象无一被孪生调用站调用 | `not (set(a for a,b in extra_dual) & invoked)` | 35 外同形态对象与 35 个 edx 调用目标集合无交集 | 基本 | detail 说“37 个孪生调用站”，但 `invoked` 只收集了 35 个有效前导的 edx（脚本循环用的是 `for s in R121_TWINS`）。应改为收集全部 37 站，或把断言名/detail 改为“35 个孪生调用站”。 |

### A5.3 占位断言与假反控汇总

| 类型 | 断言 | 文件:大致行号 | 为什么有问题 | 应改 |
|---|---|---|---|---|
| 占位（cond 恒真/近乎恒真） | A2 | r122b_allvec.py:115 | `len(VEC_TD) < len(TD_NAMES)` 几乎必真 | 改成精确计数 396/634 |
| 名字大于 cond | B1b | r122b_allvec.py:196 | 声称“多数是哨兵”，cond 只要求 sentinel>0 且 above>0 | 改成 sentinel 为最大类 |
| 名字大于 cond | B2 | r122b_allvec.py:205 | 声称“全库…数”，cond 只 `>=35` | 改成 `==142` |
| 名字大于 cond | B6 | r122b_allvec.py:246 | 声称“对象数决定 35 是否=全体”，cond 只 `>0` | 改成 `==103` 并写明严格定义 |
| 假反控 | S1d | r122a_objs35.py:143 | 验证自己的 `rd()` 拒绝读 BSS，不是二进制事实 | 改为段表事实断言，或改名 |
| 假反控 | S5a | r122a_objs35.py:247 | edx+1 落在 BSS，`u32` 被自己的 `rd()` 拒绝→0→helper 失败；必然通过 | 改为与真实不同 vptr 的对比 |
| 假反控 | S5b | r122a_objs35.py:251 | 验证 `name_of_vtable` 对 vptr+4 的返回，不是独立事实；且 vptr+4 可能是合法 vtable 槽 | 改为断言名字不同，而非 None |

---

## 主会话必须改的（编号清单）

1. **`_r122/r122f_reconcile.py:110-111`**：边界构建必须开 `skipdata=True` 已做，但 F0a/F0 的 detail 里“实测 9.4s / RSS 500MB”和“停在 0x46f5a0”等注释要写成审计复算值：OFF 停 `0x46f5a0`、覆盖 452000；ON 覆盖 4063232、到 `0x7e1000`。当前注释是背景说明，没有机器可读复核；建议把两种模式都跑一遍并打印对照。
2. **`_r122/r122f_reconcile.py:179-188`**：`dual_form()` 补 `len(sites) == 2` 检查，且注释改成“严格定义”。当前实现只看名字列表里各一个 Dynamic/Vector，若某目标有 1 Vector + 2 Dynamic 会被误计入。审计复算显示当前数据集上它偶然给出 103（`[A4_DUAL_HELPER_DIFF]`），但定义与实现不符。
3. **`_r122/r122f_reconcile.py:133-141`**：F1 的期望值应改为 clean=1142（主会话写对了，但 FAIL 是因为代码当时边界残缺）。同时把 dropped 的 17 目标 / 29 站点写入 JSON 固定字段，便于跨家族对齐（`[A2_RAW]`）。
4. **`_r122/r122f_reconcile.py:158-159`**：F2 期望 142 正确；应把 35 内/35 外（35/107）也写成独立断言，而不是只断言总数。
5. **`_r122/r122f_reconcile.py:201-212`**：F4/F5 是 `cond=True` 占位断言（只打印 detail）。应改成条件断言，例如 `n_clean == 138 and out_clean == 103`；F5 应断言 `len(set_raw ^ set_clean) == 0`（审计复算严格口径下对称差为 0，`[A4_SYMDIFF_STRICT]`）。
6. **`_r122/r122a_objs35.py:143`**：S1d 假反控改名或改成独立段表事实断言。
7. **`_r122/r122a_objs35.py:220-228`**：S3c/S3d/S3e 依赖 `w[0]`/`w[1]`，应显式断言每对象 `len(writes)==2`，并用名字集合判定 Dynamic/Vector，避免排序假设。
8. **`_r122/r122a_objs35.py:239-242`**：S3f/S3g 的 `elems` 只取第二站；应对全部 70 个名字解析元素类型。
9. **`_r122/r122a_objs35.py:245-252`**：S5a/S5b 两条假反控要重做；edx+1 落在 BSS 导致 `u32` 被 `rd()` 拒绝，与 RTTI 解析能力无关。
10. **`_r122/r122b_allvec.py:115`**：A2 占位断言 `len(VEC_TD) < len(TD_NAMES)` 改成精确计数。
11. **`_r122/r122b_allvec.py:196-201`**：B1b 改成“sentinel 是最大类”的断言，而非各 >0。
12. **`_r122/r122b_allvec.py:205,210,246`**：B2/B4/B6 把 `>=35`、`>0`、`>0` 改成精确期望 142/107/103，并写明严格定义。
13. **`_r122/r122b_allvec.py:252-261`**：B7 detail 说 37 站，但 `invoked` 只收集 35 站；改为收集 37 站或修正文案。
14. **口径统一结论**：`0x00abfda0` 9 次写入（1 Vector + 8 Dynamic，7 次重复 Dynamic），严格定义不满足，宽松定义满足。主会话与 deepseek 必须统一用严格定义；采用严格定义时，主会话 103 正确，deepseek 104 是把 `0x00abfda0` 按宽松口径算入了。
