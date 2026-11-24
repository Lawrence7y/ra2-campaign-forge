# 卡 R17-LEDGER-1057 · 书记员起草台账 §1057（R17 第 4 轮：R8/R9 双卡 + 两次异族审计 + 一次第三方裁决）

角色：书记员（只起草，不并表、不改台账正文）。你不是台账写者：只把草稿写到自己的目录，台账由 Lead 逐字追加。

## 一、必须覆盖的事件（逐条给证据路径）
1. **R8 卡（R17-R8-RESIDUAL，deepseek）**：闭合 R7 留下的四个「未取得」。四问结果 + 执行方自记的**三处锚点陷阱**（C2 判序、节界用 vsize 吞掉 .rdata、0x47CA70 须按标签起步）。
2. **审计 R8（跨家族 hy4）**：判 A1 DISAGREE / A2 AGREE（但要求把「虚派发」降级为推断）/ A3 AGREE / A4 AGREE / A5 DISAGREE（「唯一作用=副作用」被放进事实段）；必改 5 条。
3. **地址权威表（A1 的实质）**：0x43F24B / 0x43F501 / 0x43F5AD 是 SIB=0x24 字节位置，**指令起始**权威值为 0x43F249 / 0x43F4FF / 0x43F5AB（R7 对）；jne 起始 0x47C73F（R7 挂在 0x47C73D 错，其目标 0x47C853 正确）；0x47C853 实为 `5F`(pop edi)，`32 C0`(xor al,al) 在 **0x47C856**（执行方对）。
4. **R9 卡（R17-R9-VTABLE-CONSUMER，deepseek）**：先独立复现 R8 的「唯一静态引用」，再判 R8 的表形态不成立，报连续 350 槽串 [0x7E3E8C,0x7E4403]、槽号 #85/#119；零取用者；RTTI 类名未取得。
5. **第三方裁决卡（R17-ADJ-RDATA-RUN，deepseek，单问题）**：text-only 极大连续槽段 = **[0x7E3EBC,0x7E43C4) 共 322 槽**；0x7E3FE0 = **#73**、0x7E4068 = **#107**；两种 .text 上界口径结果一致（灰区槽数为 0）。判**甲(R8 段界)对、乙(R9)错**：R9 左端早 12 槽、右端晚 16–17 槽、共多 28 槽，且串内含 0x7FC2B0/0x7FC360/0x7FC298 等**非 .text** 值。
6. **审计 R9（跨家族 hy4）**：判 B1 AGREE（12 个候选立即数各 0 命中，正控/反控全通过）/ B2 DISAGREE（独立复算同为 322 槽，与裁决卡一致，确认 R9 错）/ B3 DISAGREE（**发现 12 处 ctor 形态立即数装表写**）/ B4 AGREE（.rdata 装饰名 0、无 pTD，未取得诚实）；必改 4 条。
7. **B3 发现的边界必须写清**：12 处 `mov [esi/ebp+off], imm32` 的目标槽是 **0x7E3E90 / 0x7E3E98 / 0x7E3EA0 / 0x7E3EBC**（即串的 #0 附近），内容分别是 0x410590/0x410580/0x4105E0/0x410260（均 .text）；site 落在三个 host 内（0x43B680–0x43B740、0x43B740–0x43BCDE、0x43BCF0–0x43C0CA），位置断言 host <= site < fn_end 均成立。⇒ **这些取用者消费的是串的前几个槽，不是 #73/#107**。该结论为**审计单源**，未做二次复核，引用须标注。
8. **本轮净结论（供后续引用）**：0x43F180 与 0x449440 各有且**仅有 1 个**静态数据引用（.rdata 0x7E3FE0 / 0x7E4068），E8/E9 直接调用均为 0，且**没有任何指令以立即数装载这两个槽或其邻槽** ⇒ **调用者与槽偏移均未取得**；「虚派发」仍为**推断**（该区间确为 vtable 型数据：前几槽有 12 处 ctor 装表实证；但 #73/#107 无装表点、无取用点）。
9. **§1056 四项「未取得」的现状（必须并列，防下游误引）**：0x47C620 精确尾界 **已取得 = 0x47CA7C**（函数体 [0x47C620,0x47CA7C)，1 个成功 epilogue + 9 条 early-exit 尾巴，10 条 `C2 0C 00`）；case 0 / case 2 **已取得 = 均不产生拒绝**（恒 al=1）；0x6F4A70 语义 **仍未取得**（仅标为推断，强度中）；两函数调用者 **仍未取得**。⇒ **引用 §1056 的这四项必须同引 §1057**。
10. **一处 Lead 级环境发现**：live profile 的 dsh-purge-community 已写 1.7.20 tgz（非 LEAD_LOCK 记的 1.6.93 #commit 钉死），package.json mtime 晚于该记录；且该 profile 的 dependencies 与 node_modules 中**已无任何 @deepseek-ai/* 包**。⇒ 通道**可用性**是实测事实（subagent 工具已挂载、provider magpie-anthropic、4 个模型可选），但安装来源为**未取得**；不得把 LEAD_LOCK 的装后核对当作当前截面。
11. **派发通道切换**：本轮起派发改走内部 subagent 工具；首个探测回执「OK / 自报模型: 未回报」⇒ **身份仍不可校验**（与旧 pi 通道同病）。故本轮全部结论的可信度建立在**异族审计 + Lead 对盘复算**上，不建立在通道身份上。
12. **方法学（本轮两次生效，建议入 COMMON）**：① 负面结论必须自带**正控与反控**，否则「0 命中」不可采信；② 单源结论一律降级为**推断**并标强度；③ 独立分析互相矛盾时，用**单问题裁决卡**由第三方自算，禁止 Lead 自行推断或默认采信一方。

## 二、写法要求（逐条照做）
- 凡数字**必须自己从盘上复算**，不得照抄本卡面；复算值与卡面不符时**并列报出并说明差异**。
- 事项用「事项 1/2/3…」编号，每事项给**证据路径**（相对仓库根）。
- 类名/地址取不到写「未取得」，**严禁编造**。
- 指令地址用 0x 前缀；entry 用 8 位大写十六进制不带 0x。
- 逐条理由**必须互异**。
- 结尾必须写一行：「本草为 §1057 草稿，由 Lead 逐字追加；书记员未自行改动台账。」

## 三、要读的目录（只读）
- lead\next_re_20261117_r14\R17_R8_RESIDUAL\（REPORT.md / sites.tsv / anchors.txt / residual.md / work.py）
- lead\next_re_20261117_r14\R17_AUDIT_R8\（VERDICT.md / addr_authority.tsv / byte_checks.tsv）
- lead\next_re_20261117_r14\R17_R9_VTABLE_CONSUMER\（REPORT.md / tables.tsv / consumers.tsv / residual.md）
- lead\next_re_20261117_r14\R17_ADJ_RDATA_RUN\（VERDICT.md / run.tsv / neighbors.tsv）
- lead\next_re_20261117_r14\R17_AUDIT_R9\（VERDICT.md / controls.tsv / bounds.tsv）
- lead\next_re_20261117_r14\STATUS_BOARD.md（R17 各段作上下文）、lead\LEAD_LOCK（末尾 P–S 节）

## 四、产物（只写本目录）
lead\next_re_20261117_r14\R17_LEDGER_1057\
- SECTION.md —— 标题行以 «## §1057 · 书记员覆盖 R17 第 4 轮（…）：…» 起
- numbers.tsv —— 你复算的每个数字（名称 / 复算值 / 卡面值或来源）
- SELFCHECK.md —— 12 个事项覆盖情况、哪些写了未取得、哪些数字与卡面不一致
严格 7 分钟预算；先落 numbers.tsv 再写正文。不执行逆向、不启动 gamemd、不写仓库根。