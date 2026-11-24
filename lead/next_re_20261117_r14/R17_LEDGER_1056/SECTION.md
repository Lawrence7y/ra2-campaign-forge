## §1056 · 书记员覆盖 R17 第 2 轮至第 3 轮（14 项）：看板归档、回执核对、R7 静态结论与子代理通道环境变更

### 事项 1 · H44 看板归档
- 证据路径：`lead/next_re_20261117_r14/STATUS_BOARD.md`、`lead/next_re_20261117_r14/BOARD_ARCHIVE.md`、`lead/next_re_20261117_r14/R17_LEAD_BASELINE/STATUS_BOARD.before_H44.md`、`lead/next_re_20261117_r14/R17_LEAD_BASELINE/BOARD_ARCHIVE.before_H44.md`。
- 复算：before 看板 279 行（50,262 B）；第 164–202 行共 39 行，其中第 164–185 行 22 行、第 186–202 行 17 行。39 行均在 BOARD_ARCHIVE.md 中逐行命中，missing=0。事件时点看板 279−39=240 行；归档 297,569 B / 3,128 行变为 307,740 B / 3,171 行。before 副本恰两份。
- 核对理由：我用 before 副本重新编号并逐行比对归档正文，而不是引用看板摘要；当前 STATUS_BOARD.md 已因后续追加 R17 第 2 轮及续节变成 259 行，故 240 行是 H44 事件时点数，不是当前文件行数。

### 事项 2 · B4 迟到回执核对（rcpt-4769bb40-1）
- 证据路径：`lead/next_re_20261117_r14/R17_HYG_A1_B4/delta.tsv`、`lead/next_re_20261117_r14/R17_HYG_A1_B4/work.py`、`lead/next_re_20261117_r14/COVERAGE/coverage.tsv`、`lead/next_re_20261117_r14/R17_LEAD_BASELINE/coverage.before_hyg.tsv`、`lead/next_re_20261117_r14/STATUS_BOARD.md`、`lead/LEAD_LOCK`。
- 复算：delta 数据行 16，note 去重后 16；旧第 4 列 sha1 对 before coverage 16/16 命中，新第 4 列 sha1 对当前 coverage 16/16 命中；SENTENCE 常量长度 65，16/16 行第 4 列以该常量结尾并含 §12.6。样本为 6452/005CB430、6453/005CB440、6454/005CB540，三行 entry 均与当前表一致。
- 核对理由：该批此前已并表，所以对回执只做“是否已落盘”的反向验真；逐行重算前后 sha1 后没有发现需要二次并表的缺口。

### 事项 3 · R7 静态卡（R17-R7-REJECT-LAYER）
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`。
- 三问与答案：① `[esp+0x23]` 的全部写点和值来源——写点 2 处、读点 1 处，值来自本块自己写死的 0/1 常量；② 0043F180 与 0043F1E9 的关系及调用点清单——两者不是两个函数，0043F1E9 是 0043F180 switch 的 case 1/case 3 程序体；③ 失败值的最终产生指令——0x43F5E3 的 `32 C0`（`xor al,al`）。
- 核对理由：REPORT.md 恰有 Q1/Q2/Q3 三个题头；本项闭合的是 D-1 留下的“哪一层产生拒绝”问题，三问顺序与卡面一致。

### 事项 4 · 纠正 1（层级错）
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`。
- 复算：跳表 0043FB0C 四项为 0043F1CA / 0043F1E9 / 0043F9A6 / 0043F1E9；0043F1E9 无自身序言，直接使用由 0x43F191 建立的 edi；0x43F1E6 的 `C2 04 00` 是 case 0 的 `ret 4`。0043F1E9 直接 E8 命中 0。
- 核对理由：审计 C1 用字节和序言形态同时排除“独立函数”读法，因此派卡时追问“0043F1E9 的调用点”本身就是把 case 程序体误当函数入口所形成的伪问题。

### 事项 5 · 纠正 2（层级错）
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`、`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`。
- 复算：0x47C738 的 `E8 93 FC FF FF` 解出 rel32=-877（即 -0x36D），目标为 0047C3D0；该地址是 0047C620 体内的一条指令，00449440 才是函数入口。0047C738 与 00449440 的直接 E8 命中均为 0。
- 核对理由：审计 C2 已把 rel32 独立解算到 0047C3D0，故“0x47C738 vs 0x449440”不是同级比较；建议统一写“占格闸调用点 0x47C738（非函数入口）”。

### 事项 6 · 失败判据链（字节核准）
- 证据路径：`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`。
- 复算：0x43F2AE `E8 6D D3 03 00` call 0047C620 → 0x43F2B3 `84 C0` → 0x43F2B5 `0F 84 49 02 00 00` je 0x43F504；0047C620 内 0x47C738 call 0047C3D0 → 0x47C73D `3B C5` → 0x47C73F `0F 85 0E 01 00 00` jne 0x47C853 → 0x47C853 起收尾块 `5F 5E 5D 32 C0 5B 83 C4 08 C2 0C 00`。
- 并列差异：卡面把“`xor al,al`”简记在 0x47C853；盘上 byte_checks.tsv C6 显示 0x47C853 是收尾块首，`32 C0` 的精确指令地址是 0x47C856。差异仅是指令起点与块首的粒度不同，不改变 al=0 的结论。
- 核对理由：逐跳重算 rel32/rel8 后，两条链的跳转目标均与审计 C5/C6 一致；我把 0x47C856 写入数字表以免后续引用把块首误当 xor 起点。

### 事项 7 · 拒绝出口与失败值
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/RESIDUAL.md`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`。
- 复算：拒绝块首为 0x43F5D8；0x43F5B1 的 `74 25` 选中该块；失败返回值由 0x43F5E3 的 `32 C0` 产生。0x43F5DB 的 call 006F4A70 语义未取得。
- 核对理由：决定点和产出点必须分开写，前者是 je 的选择，后者是 xor 的返回值；“拒绝由哪条指令产生”在单一地址口径下应报块首 0x43F5D8，并附产出指令 0x43F5E3。

### 事项 8 · 成败标志语义
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`。
- 复算：`[esp+0x23]` 写点仅 0x43F249（`88 5C 24 23`，写 bl=0）与 0x43F4FF（`C6 44 24 23 01`，写立即数 1），读点 0x43F5AB；capstone 锚点遍历和原始字节扫描在 [0x43F180,0x43F660) 都恰命中 3 处。标志初始化为 0 后只置 1、从不复位。
- 核对理由：这个变量的语义是“至少有一格走完工作路径”，不能翻译成“全部格成功”；若所有格都被跳过，它保持 0 并触发事项 7 的拒绝块。

### 事项 9 · 0047C620 直接调用点
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/sites.tsv`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`、`lead/next_re_20261117_r14/R17_AUDIT_R7/byte_checks.tsv`。
- 复算：直接调用点 10 处，审计独立扫描集合与执行方清单相等：0x43F2AE / 0x449482 / 0x47EE93 / 0x58865F / 0x58886E / 0x5FC6FA / 0x6D5A98 / 0x6D5D33 / 0x716209 / 0x71C554。
- 核对理由：我只收“直接 E8 解算到 0047C620”的站点，不把跳表或间接调用混入该清单，因此两个产物逐项对照后为集合相等。

### 事项 10 · 未取得（照录，不得补白）
- 证据路径：`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`、`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`。
- 未取得四项：① 0043F180 与 00449440 的调用者（直接 E8 均 0，未做 vtable/.rdata 扫描）；② 0x43F5D8 处 call 006F4A70 的语义；③ case 0 / case 2 是否也产生拒绝；④ 0047C620 的精确函数尾界。
- 核对理由：这些边界外的问题没有可执行证据支撑，保持“未取得”比从相似形态外推更可靠；审计 C9 的 0 命中只证明无直接 E8，不证明没有间接到达。

### 事项 11 · 审计标出的 1 字节笔误
- 证据路径：`lead/next_re_20261117_r14/R17_AUDIT_R7/VERDICT.md`、`lead/next_re_20261117_r14/R17_R7_REJECT_LAYER/REPORT.md`。
- 复算：执行方 REPORT.md 写“0x47C615 = `C2 08 00`”；审计实读 0x47C615 = `5E`（pop esi），`C2 08 00` 在 0x47C616。
- 核对理由：这只是一处相邻一字节的记位偏差，0047C620 的锚点及其余字节均正确，因此登记为笔误而不升级为结论必改项。

### 事项 12 · 第 3 轮环境变更（子代理通道）
- 证据路径：`lead/LEAD_LOCK`、`lead/next_re_20261117_r14/R17_LEAD_BASELINE/dsh_profile_before_subagent/`。
- 复算与照录：原先无内部通道，根因是 baseline `package.json` 只有 dsh-subagent-codex 0.2.2-rc.3，而 `cordis.patch.yml` 配置的 @deepseek-ai/dsh-subagent（maxDepth 2）未安装，provider 不注册、subagent 工具不挂载；harness_route_check 的“读不到白名单”同源。用户授权后装 @deepseek-ai/dsh-subagent@0.2.2-rc.3，因为 peer 精确锁该版本；npm latest 是 0.0.1-rc.1。pnpm add 使 dsh-purge-community 1.6.93→1.7.20，随后按 before-lock commit accadd4062d6aa739d3bbf83f355515c99423baf 钉回 1.6.93，package.json 规格变为带 #commit 形式。备份目录含 package.json / pnpm-lock.yaml / pnpm-workspace.yaml / cordis.patch.yml / cordis.yml / installed_before.json。装后记录为 @deepseek-ai/* 零漂移且均 0.2.2-rc.3，新增 dsh-subagent 与 dsh-chunked-list、dsh-util-values 两个传递依赖，dsh.dsh.bundles 逐字节未变，missing peer 为既有现象。
- 并列差异：当前 live profile（`C:\\Users\\Administrator\\.dsh\\profiles\\desktop\\package.json`）已写 1.7.20 tgz，未保留卡面/LEAD_LOCK 所记的 1.6.93 #commit 钉死规格；这是事件之后的新一轮环境漂移，不能反推事件时点记录错误。
- 核对理由：我用 baseline 配置文件复核了“缺包 + maxDepth 2 + rc.3 peer”的因果链，同时把当前 profile 的后续漂移单列，避免把两个时间截面混写。

### 事项 13 · 通道激活后的首个探测
- 证据路径：`lead/next_re_20261117_r14/_cards/R17-LEDGER-1056.md`、`lead/LEAD_LOCK`。
- 复算与照录：卡面称 subagent 工具已挂载，provider magpie-anthropic 可选模型四个：work/cn:deepseek-v4.1-flash、work/cn:hy4flash-free、work/cn:hy4flash、zcode/GLM-5.3-Flash；探测卡回执“OK / 自报模型: 未回报”，因此身份仍不可校验。
- 并列差异：LEAD_LOCK P/Q/S 三次列举的 whitelist 均为 3 个模型，不含 work/cn:hy4flash；本次可用工具调用只返回 provider 字符串“magpie-anthropic — Magpie · Anthropic”，未返回模型清单，也未找到持久化探测产物。复算值记为“模型数 4（卡面）/ 3（LEAD_LOCK）/ 未取得（本会话工具）”，自报模型身份记为“未取得”。
- 核对理由：沿用 R16-7 教训，请求值不能代替实际值；既然回执没有模型身份，产物一律落盘并由 Lead 读文件取结论，不依赖回执正文。

### 事项 14 · D-53 待裁未决
- 证据路径：`lead/PENDING_DECISIONS.md`、`lead/LEAD_LOCK`。
- 照录：D-53 仍列在待裁项，二选一为 (A) 永久以 `[静态推断]` 收口 ②-b；或 (B) 撤销 D-36(A) 的“不写线程上下文”单条。用户未裁前，本草不代裁。
- 核对理由：PENDING_DECISIONS.md 第 61–70 行仍保留“请裁二选一”，LEAD_LOCK 也记待裁 1 条，故本草只移交选择项、不作口径变更。

本草为 §1056 草稿，由 Lead 逐字追加；书记员未自行改动台账。
