# 卡 R17-LEDGER-1056 · 书记员起草台账 §1056（R17 第 2 轮 + 第 2 轮续 + 第 3 轮）

角色：书记员（只起草，不并表、不改台账正文）。
硬约束：**你不是台账的写者**。只把草稿写到自己的目录；台账由 Lead 逐字追加。

## 一、必须覆盖的事件（按此顺序成节，逐条给证据路径）
1. **H44 看板归档**：把 STATUS_BOARD.md 第 164–202 行（R16 第 1–7 轮 22 行 + R16 第 8–21 轮 17 行，共 39 行）逐字搬入 BOARD_ARCHIVE.md，missing=0；看板 279→240 行；archive 297,569→307,740 B / 3,128→3,171 行；before 副本两份。
2. **B4 迟到回执核对**（rcpt-4769bb40-1）：该批已在上一轮独立校验并并表（16 行、note unique 16、delta 逐字节对盘）；回执 3 行样本 005CB430/005CB440/005CB540 复核无遗漏。
3. **R7 静态卡**（R17-R7-REJECT-LAYER）：闭合 D-1 遗留 —— 目标格被占的拒绝到底由哪层产生。三问与答案。
4. **纠正 1（层级错）**：0x43F1E9 不是独立函数，是 0x43F180 这个 switch 函数的 case 1 / case 3 程序体；跳表 0x43FB0C 四项实读 0x43F1CA / 0x43F1E9 / 0x43F9A6 / 0x43F1E9；0x43F1E6 的 C2 04 00 是 case 0 的 ret 4 而非函数边界。⇒ Lead 派卡时问的「0x43F1E9 的调用点」是伪问题。
5. **纠正 2（层级错）**：0x47C738 不是函数入口，是 0x47C620 体内一条 E8 93 FC FF FF（call 0x47C3D0）的指令地址；而 0x449440 是函数入口 ⇒ 项目长期并列的「0x47C738 vs 0x449440」不在同一层级。建议措辞「占格闸调用点 0x47C738（非函数入口）」。
6. **失败判据链**（字节核准）：0x43F2AE call 0x47C620 → 0x43F2B3 test al,al → 0x43F2B5 je 0x43F504；0x47C620 内 0x47C738 call 0x47C3D0 → 0x47C73D cmp eax,ebp → 0x47C73F jne 0x47C853 → 0x47C853 xor al,al; ret 0xC。
7. **拒绝出口与失败值**：拒绝由 0x43F5D8 产生（块首），产生失败值的指令是 0x43F5E3 的 32 C0（xor al,al），由 0x43F5B1 的 74 25（je）选中。
8. **成败标志语义（关键，勿误读）**：[esp+0x23] 只有 2 个写点 —— 0x43F249（写 bl=0，无条件）与 0x43F4FF（写立即数 1），只置 1 从不复位 ⇒ 语义是「至少有一格走完了工作路径」，不是「全部格成功」。审计用两种独立方法在 [0x43F180,0x43F660) 恰命中 3 处且仅 3 处。
9. **0x47C620 直接调用点 10 处**（审计独立复算，集合相等）：43F2AE / 449482 / 47EE93 / 58865F / 58886E / 5FC6FA / 6D5A98 / 6D5D33 / 716209 / 71C554。
10. **未取得（照录，不得补白）**：0x43F180 与 0x449440 的调用者（直接 E8 均 0，未做 vtable/.rdata 扫描）；0x43F5D8 处 call 0x6F4A70 的语义；case 0 / case 2 是否也产生拒绝；0x47C620 精确函数尾界。
11. **审计标出的 1 字节笔误**（不影响结论）：执行方 REPORT.md 写「0x47C615 = C2 08 00」，实读 0x47C615 = 5E (pop esi)、C2 08 00 在 0x47C616。
12. **第 3 轮：环境变更（子代理通道）**：用户指示「执行子代理全部改用 DeepSeek harness 内部子代理、模型路由不变」。查明原先无内部通道，根因是 profiles/desktop/package.json 只装了 dsh-subagent-codex，cordis.patch.yml 里 @deepseek-ai/dsh-subagent（maxDepth 2）那个包不存在 ⇒ provider 永不注册 ⇒ subagent 工具永不挂载（harness_route_check 的「读不到白名单」是同一根因，不是配置缺失）。用户授权后装 @deepseek-ai/dsh-subagent@0.2.2-rc.3（精确 rc.3，因 peer 精确锁；npm latest 是很旧的 0.0.1-rc.1）。附带漂移：pnpm add 把 dsh-purge-community 1.6.93→1.7.20，已按 before-lock 原 commit accadd40 钉回 1.6.93，代价是 package.json 规格变成带 #commit 的钉死形式。备份目录 R17_LEAD_BASELINE\dsh_profile_before_subagent\。装后核对：@deepseek-ai/* 全家零漂移全 0.2.2-rc.3；新增 dsh-subagent + 两个传递依赖；dsh.dsh.bundles 逐字节未变；pnpm peers check 的 missing peer 是既有现象。
13. **通道激活后的首个探测**：subagent 工具已挂载，provider magpie-anthropic 可选模型四个（work/cn:deepseek-v4.1-flash、work/cn:hy4flash-free、work/cn:hy4flash、zcode/GLM-5.3-Flash）。探测卡实测回执「OK / 自报模型: 未回报」⇒ **身份仍不可校验**，与旧 pi 通道同病（R16-7 教训：不得把请求值当实际值）。处置：产物一律落盘、由 Lead 读文件取结论，不依赖回执正文。
14. **D-53 待裁未决**：②-b 收口 (A) 永久 [静态推断] / (B) 撤销 D-36(A) 单条。用户未裁前不代裁。

## 二、写法要求（逐条照做）
- **凡是数字，必须自己从盘上复算**，不得照抄卡面；复算值与卡面不符时**并列报出并说明差异**。
- 事件与事件之间用「事项 1/2/3…」编号，每事项给出**证据路径**（相对仓库根）。
- 类名/地址取不到写「未取得」，**严禁编造**。
- entry 一律 **8 位大写十六进制、不带 0x 前缀**；指令地址可用 0x 前缀（这是地址不是 entry）。
- 逐条 note/理由**必须互异**，不得复制粘贴同一句。
- 结尾必须写一行：「本草为 §1056 草稿，由 Lead 逐字追加；书记员未自行改动台账。」

## 三、要读的文件（只读，不得修改）
- lead\next_re_20261117_r14\STATUS_BOARD.md（末四段：R17 第 2 轮 / 第 2 轮续 / 第 3 轮；以及第 1 轮各段作上下文）
- lead\LEAD_LOCK（末尾 P/Q/R/S 四节）
- lead\next_re_20261117_r14\R17_R7_REJECT_LAYER\（REPORT.md、RESIDUAL.md、anchors.txt、sites.tsv）
- lead\next_re_20261117_r14\R17_AUDIT_R7\（VERDICT.md、byte_checks.tsv）
- lead\next_re_20261117_r14\R17_LEAD_BASELINE\（目录清单与文件名即可）
- lead\PENDING_DECISIONS.md（D-53 条目）

## 四、产物（只写这个目录）
lead\next_re_20261117_r14\R17_LEDGER_1056\
- SECTION.md —— 本草正文（Markdown，标题行以 «## §1056 · 书记员覆盖 R17 第 2 轮至第 3 轮（…）：…» 起）
- numbers.tsv —— 你复算过的每个数字（三列：名称 / 复算值 / 卡面值或来源）
- SELFCHECK.md —— 逐条自检：14 个事项是否全覆盖、哪些写了未取得、哪些数字与卡面不一致

严格时间预算 7 分钟；先落 numbers.tsv 再写正文。不执行任何逆向、不启动 gamemd、不写仓库根。
