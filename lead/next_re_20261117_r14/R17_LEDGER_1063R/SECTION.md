## §1063 · 书记员覆盖 R17 第 11 轮（一条结论作废 + 一处方法学缺陷 + 交付件同步）：两条负面记录与五项配套证据

### 事项 1 · R25 slot #107 交集结论作废
- 事件：`R17_R25_SLOT107` 用「R12 hit host ∩ R23 ctor host」按精确相等求交，0x1AC 与 0x124 均得 0 条，据此下「`0x449440` 未取得」。交集为零系坏数据所致，非事实。
- 作废理由（与后续各项互异）：交集的两个输入列都不是可信函数入口集；R23 `ctor_sites.tsv` 的 `call_target` 列才是 `0x43B740`/`0x43B680`（被调目标），host 列 15 行中有 4 行与逐点定界真实 host 不同；R12 `hits.tsv` 的 host 又受 C3/C2 字节扫缺陷污染（见事项 3）。两者相乘，零交集无证明力。
- 🔴 红线一：**R25 的结论不得引用（该结论不得引用）**。
- 证据：`R17_R25_SLOT107/REPORT.md`（第一、二、三步）、`R17_R25_SLOT107/intersect.tsv`（仅表头，零命中）、`R17_R23_CALLER_PATH/ctor_sites.tsv`（仅核 host 列）、`R17_R27_SLOT107_V2/REPORT.md` 第 0 节。
- 复算：交集 0x1AC=0、0x124=0，见 numbers.tsv 事项 1 两行，与卡面一致。

### 事项 2 · R26 `0x5A6510` 角色判定
- Q1：扫 1214 张 vtable / 14044 个槽值，`0x5A6510` 0 命中 ⇒ 它不在任何 vtable 槽内（不是虚方法）；vtable 基址/槽号/类名均记「未取得」。
- Q2：`0x5A6510` 只有 1 处直接调用，site `0x5A531E`（调用者入口 `0x5A5020`，边界 PASS）。
- Q3：`0x5A6860` 那次 slot73 派发的返回值被丢弃——下一条 `0x5A6866 mov edx,[esp+0x1c]` 随后覆盖 EAX，无 test/compare/保存 ⇒ 该调用是命令/副作用型，不是查询。
- Q4：场景推断 2 条，最高强度「中」（候选 A 中立建筑放置、候选 B 一次性批量尝试器）；确切游戏语义名未取得，均不写成事实。
- 定性理由（与事项 1 互异）：本项不是交集作废，而是「零 vtable 命中 + 单点直接调用 + 返回值丢弃」三条正向字节证据叠加，把 `0x5A6510` 定位为非虚方法、副作用型调用。
- 证据：`R17_R26_HOST_ROLE/_result.json`、`vtable_hits.tsv`（空表）、`callers.tsv`、`REPORT.md`（Q1–Q4）。
- 复算：1214 / 14044 / 0 / 1 均与卡面一致。

### 事项 3 · 🔴 方法学缺陷：函数入口不能按字节扫 C3/C2
- 事件：site `0x5A6860` 被 R12 记 `host=0x5A6810`，但 `0x5A6810` 绝非入口——其前字节 `0F BF C3`（`movsx eax,bx`）中的 C3 只是 modrm 字节，被当成 `ret` 误判。真 host 是 `0x5A6510`（`83 EC 70` 序言），真 fn_end 是 `0x5A691C`（其后 `90 90 90 90` 填充）。
- 同一行 R12 的 `verdict = NON_TARGET(base from stack)` 亦错：基址来自 `0x5A66D9 8B E8`（`mov ebp,eax`），是构造出的对象，非栈槽。
- 🔴 红线二：**入口判定禁止按字节扫 C3/C2**；反例即 `0F BF C3`（`movsx eax,bx`）——其中 `C3` 为 modrm，不是 `ret`。
- 正确做法：用可信入口集（`.rdata` 全部 vtable 槽值，约 14,044 个，均为函数入口）+ 严格线性解码，不用 C3/C2 字节搜索。
- 缺陷机理（与事项 1 互异）：事项 1 是输入列选错，本项是判定算法错——把操作数字节当操作码，属方法学层面，影响所有按该法归因的 host，而非仅某一交集。
- 证据：`R17_R12_VT_OFFSET/hits.tsv` 被点名行 `0x5A6860`（host=0x5A6810, fn_end=0x5A6920, verdict=NON_TARGET）、`R17_R27_SLOT107_V2/REPORT.md` 第 0/1 节、`R17_R28_R12_REPAIR/work.py` 注释（no C3/C2 byte scan）、`R17_R26_HOST_ROLE/_result.json`（函数 0x5A6510..0x5A691C 锚点）。

### 事项 4 · R28 缺陷量化（354 行逐一重新归因）
- 总量：`host_changed` 129 行、`fn_end_changed` 125 行、`position_assert` 翻转 5 行；`verdict = NON_TARGET(base from stack)` 64 行中需重分类 19 行。
- 按类：call 267 行（host 变 84 / fn_end 变 76 / assert 翻 1）、mov 70 行（35 / 39 / 3）、other_cmp 1 行（1 / 1 / 0）、other_test_imm 7 行（5 / 5 / 1）、stack_ff5424 9 行（4 / 4 / 0）。自洽校验：84+35+1+5+4=129；76+39+1+5+4=125；1+3+0+1+0=5。
- `base_source` 为空 43 行；`verdict = NON_TARGET(base from stack)` 64 行，其中 19 行需重分类；严格解码仍有 167 行 unresolved。
- 口径说明：`R17_R28_R12_REPAIR/stats.tsv` 记录的是早期中间态（108/82/4/33），已被 `R17_R28_R12_REPAIR/REPORT.md` 取代，不得引用；`REPORT.md` 才是权威。
- 🔴 红线三：**形态命中数不受 host 修正影响**。依据：`REPORT.md` Q4 重扫表给出 call@0x124=181、call@0x1AC=86、mov 55+15=70、other_cmp=1、other_test_imm=7、stack_ff5424=9，其余形态 0；合计 267+70+1+7+9=354。另经 `host_fix.tsv` 按 class 计数同样得 call 267 / mov 70 / other_cmp 1 / other_test_imm 7 / stack_ff5424 9，合计 354。两路独立核算，修正前后形态命中数不变的结论保持不变。
- 量化理由（与事项 1、3 互异）：前两项定性与作废，本项是把缺陷折算成可核对的差分计数——host/fn_end/assert 三列变更多寡，恰证字节扫入口法污染的规模；`NON_TARGET` 旧判名中 19 行应重分类，而形态计数恒定则说明污染只在归因层、不在形态层。
- 证据：`R17_R28_R12_REPAIR/host_fix.tsv`、`R17_R28_R12_REPAIR/REPORT.md`、`entries.json`、`interim.json`、`work.py`。
- 复算：卡面（派发卡）当时引的是 `stats.tsv` 的 108/82/4/33，本次修订按 `host_fix.tsv` 与 `REPORT.md` 更正为 129/125/5/19；这是 Lead 派发卡引用过期中间态造成的，不是执行方错（见 numbers.tsv 事项 4 各行）。

### 事项 5 · R27 正向法重做 slot #107
- 15 个构造点真实 host 与 R23 那列有 4 个不同（`0x5A66D4` / `0x5A96F8` / `0x5CAB60` / `0x7396C3` 这 4 点 host 不一致）。
- 在这些真实 host 内：`0x1AC` 命中 0 条；`0x124` 对照命中 6 条（正控，说明扫描器能命中已知形态）。
- ⇒ `0x449440` 的调用方仍未取得，且这次是方法可靠的负结果（建立在可信入口集 + 严格解码上，不再建立在坏数据上）。
- 边界：只证「15 个真实 ctor host 内未发现」，不证全局不存在；对象经全局/成员字段长距离传递、跨函数传入、非这两个 ctor 构造等情形未覆盖；不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）。
- 方法理由（与事项 1 互异）：事项 1 因输入列坏而作废；本项换用正向可信入口集重跑，同样得零命中，但零命中的性质从「坏数据产物」升级为「方法可靠的负结果」，二者结论表面同、证据等级不同。
- 证据：`R17_R27_SLOT107_V2/ctor_hosts.tsv`、`dispatch_hits.tsv`、`REPORT.md`（第 0/2/3/4 节）。
- 复算：15 / 4 / 0 / 6 均与卡面一致。

### 事项 6 · 交付摘要已同步（`R17_DELIVERY_R11`）
- `DELIVERY_SUMMARY.md` 7,466 → 10,214 B / 64 → 74 行（≤110 上限内）。
- 新增 `§2.5` 四条（定名链 + 限制、槽定位、调用方链 + 边界、覆写关系 + 语义未取得）与 §3 行 7/8（对账三版三数须带口径；433 不得当升级用）。
- `verify.py` PASS；备份 `wx` 独占创建成功（bytes=7466、sha256 与 before 一致）。
- 同步理由（与前述各项互异）：前五项均为分析结论，本项是交付件字节/行数与禁改集合的结构性核对，只有净插入、既有行零改动，属文档落地而非新的逆向结论。
- 证据：`R17_DELIVERY_R11/REPORT.md`、`R17_DELIVERY/DELIVERY_SUMMARY.md`、`R17_DELIVERY_R11/DELIVERY_SUMMARY.before_R11.md`。
- 复算：7466 / 10214 / 64 / 74 / 110 均与卡面一致。

### 事项 7 · GLM 第五卡（`zcode/GLM-5.3-Flash`，自报 `bigmodel-api/GLM-5.3-Flash`）
- 8 项全 AGREE、`OVERALL: CONSISTENT`。
- 确认看板第 10 轮段的 host `0x5A6510`、两条边界、双口径并列、以及「只写数字不写口径不可引用」均在位。
- `LEAD_LOCK` AC4 与台账 §1062 的六个数完全相同：口径 S（严格基名）397/32/383、口径 C（`X_Y`↔`X@Y`）403/26/377。
- 一致性理由（与事项 1、5 互异）：事项 1 结论作废、事项 5 负结果升级；本项是独立第二意见对既有文本与表内算术逐位复核得 CONSISTENT，既非作废也非新负结果，而是外部校验通过。
- 证据：`R17_GLM_TXT_5/VERDICT.md`、`STATUS_BOARD.md`（行 233–238）、`R17_LEDGER_1062`（事项 3 所载六数）。
- 复算：8 AGREE / 六数 397/32/383、403/26/377 均与卡面一致。

本草为 §1063 草稿，由 Lead 逐字追加；书记员未自行改动台账。