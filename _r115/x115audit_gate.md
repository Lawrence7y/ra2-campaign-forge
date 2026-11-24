# X115-AUDIT-GATE —— 审计「门禁三通道与可静默改写」的实验设计

审计员：hy4（magpie-anthropic / work/cn:hy4flash）
审计对象：_r115/r115b_gate.py、_r115/r115b_gate.json、lead/next_re_20261117_r14/check_disc.py、DISC_RECHECK.tsv、DISC_UNVERIFIABLE.tsv
边界：只读盘，仅新建本报告。所有命令带 timeout。未使用反引号。

## 总览

主会话声称的 8 条断言按“实验设计是否足以支撑该断言”判定，结果如下（判定针对断言本身，不针对脚本内部 ck 是否 PASS）：

- B1 PASS
- B2 FAIL（措辞过强，需降级）
- B3 PASS
- B4 原断言 FAIL（脚本已自我推翻；当前 r115b_gate.json 中的 B4 是修正后的 C12 防线断言，PASS）
- B5 PASS（但“8 条 FAIL”是观察值，脚本断言只检查 >=1，断言强度弱于声称）
- B6 PASS（但需限定语：只证明“改锚 + 同步重算 C14 常量后不被发现”，不等于等价于原判据）
- B6b FAIL（对照方向成立，但理由归因错误：实际只有 C14 抓到，C9 未触发）
- B7 部分 PASS（B6 实测支撑“sha 钉只抬高成本不防伪造”，但不覆盖 C10/C14 drifted 等已同步放松的子项）

下面逐条给出理由与主会话需复算的具体点。

## B1 三通道分区：PASS

脚本按第 7 列是否以“有”开头、是否在 DISC_UNVERIFIABLE.tsv 中分区，得到 real=[3,4,22,27,28]（5）、frozen=[1,2,5,6,7,8,9,10,18,20,24,25]（12）、none=[11,12,13,14,15,16,17,19,21,23,26,31,32,33]（14），合计 31。与 check_disc.py 的 C11 语义一致：C11 只对 col7 以“有”开头的行调用 verify_recheck_line（check_disc.py:294-321），冻结档在 verify 失败时计入 c11_declared 不 FAIL（315-317），col7 非“有”直接 continue（294-296）。分区是静态可从数据直接验算的，断言成立。

复算点：python3 -c 读取 TSV 按第 7 列首字与冻结表求交即可，无需跑门禁。

## B2 “7 个完全无约束”：FAIL（措辞过强）

主会话断言：这 7 个 id（16/19/21/23/31/32/33）“不在 C11_LANDABLE，进不了任何 FAIL 分支”，并进一步在 r115b_gate.py 的注释与 ck 名里写成“完全无约束”。精确核对门禁各检查项后，这个“完全无约束”过强：

- C11/C11b：确实管不到。C11 对 col7 非“有”直接 continue（294-296）；C11b 只检查 C11_LANDABLE 集合内的 gap（252-261），这 7 个不在集合内，故不触发。
- C12：管不到。C12 只遍历 DISC_UNVERIFIABLE.tsv 的冻结行（332-362），这 7 个不在冻结表。
- C9：管得到一部分。C9 对每一行的第 3 列（判据）与第 4 列（锚）调用 is_placeholder（96-101）。“完全无约束”若意味着“改第 3/4 列任何内容都不被看见”，是错的：改成空、改为 GARBAGE/TBD/无 等占位词会触发 C9 FAIL。只有改成非占位的自由文本时 C9 才不管。B6 的实测恰好选了 ANCHOR_SILENTLY_REWRITTEN_R115，place_r87.is_placeholder 对它的判定为 (False,空)，所以不触发 C9，这反证 C9 对“垃圾化”是有牙齿的。
- C13：管得到第 2 列。C13 校验第 2 列的节号必须属于该纪律号在 R14_COMMON 中定义所在的节集合（379-389），这 7 行也有第 2 列，改错会 FAIL。
- C14：管得到第 2/3/4 列整表指纹（401-419）。B6b 实测证明只改锚不重算常量会触发 C14 FAIL，drifted ids 正确列出这 7 个。
- C7：这 7 行都有非空产物路径与校验式，C7 会真跑 exists/grep 等表达式（150-214）。例如 id16 的 grep=grepcount=3、id19/21/23/31/32/33 的 grep= 都会在产物文件缺失时 FAIL。因此“完全无约束”也不成立——删掉或改坏产物会触发 C7。

精确表述应为：这 7 行在“第 7 列 claims-有 路径”上永不可 FAIL，不进 C11b gap 钉、也不受 C12 冻结档防线约束；但 C9/C13/C14/C7 对它们的第 3/4/2 列与产物仍施加约束。主会话应把 B2 从“完全无约束”降级为“在 claims-有/冻结档这两条防线上无约束”。

复算点：
1. 对 7 行各改一次第 3 列为 'GARBAGE'，跑门禁，预期出现 7 条 C9 FAIL。
2. 对 7 行中任一删除其产物路径指向的文件，跑门禁，预期 C7 FAIL。
3. 对 7 行中任一改第 2 列为不存在的节，预期 C13 FAIL。

## B3 claims-有 12 个不在 LANDABLE 但全被 C12 拦住：PASS

脚本先误判后自纠：初始假设这 12 行可静默摘帽，B4 实测 12 条 C12 FAIL 后修正为“12 个全在冻结档、全部被 C12 的 frozen but not claims-有 拦住，真正无人拦的 0 个”。核对 DISC_UNVERIFIABLE.tsv 与 DISC_RECHECK.tsv：frozen 集合恰为 [1,2,5,6,7,8,9,10,18,20,24,25]，与 cand = has 且不在 LANDABLE 的集合完全相同。C12 的防线实现在 check_disc.py:347-349：_claim_ids 来自 col7 以“有”开头的行，若冻结行的 id 不在 _claim_ids 就 FAIL。因此把这 12 行翻成“无”必然触发 12 条 C12 FAIL。断言成立。

复算点：r115b_gate.json 的 B4 记录 rc=1、c12_fails=12、all_fails=12，已构成实测；可独立跑 r115b_gate.py 复现。

## B4 主会话声称“把 12 行翻无，可静默摘帽”：FAIL（已被脚本自身推翻）

调度卡里列出的主会话声称 B4 是“变异实测：把那 12 行第 7 列翻成无，未改动的 check_disc.py 报 12 条 C12 FAIL、exit 1”。这与“可静默摘帽”是矛盾的——12 条 FAIL 不是静默。实际 r115b_gate.py 的 B4（182-187 行）已经把它写成“C12 防线实测（正向结论）”，并在 ck 名里明确写“初稿断言被实测推翻”。脚本产物 r115b_gate.json 中 B4 的记录是 rc=1、12 条 C12 FAIL，与该修正版一致。

判定：若按调度卡字面（“可静默摘帽”），FAIL——实测否证；若按脚本修正后的 B4（C12 拦得住），PASS。主会话应统一措辞，避免把被推翻的初稿结论仍列为当前断言。

复算点：核对 r115b_gate.py:85-99（自错 S-18 注释）与 182-187（修正断言），确认初稿与终稿的区别已被如实保留。

## B5 反向对照翻 7 个 gap 行为有：PASS（但断言强度弱于声称）

实测 rc=1、8 条 FAIL，其中第一条是 C11b loadable gap drifted: [] != pinned [...]，随后 7 条 C11 id 11/12/13/14/15/17/26 claims recheck but has no valid self-description line。方法学上这证明变异确实能改变门禁行为，不是“改了没生效”。但要注意：脚本的 ck 断言（207-210 行）只要求 rc != 0 且 len(fails3) >= 1，并不检查“恰好 8 条”或“7 条 C11 自描述 FAIL + 1 条 C11b drift”。因此“8 条 FAIL”是观察值而非被断言锁定的量。声称“8 条 FAIL”若作为结论，需要在脚本里把断言写成 len(fails3)==8 或分类计数，否则换了环境FAIL 数变化脚本仍 PASS。

复算点：把 ck 条件临时改为 len(fails3)==8 再跑，确认本环境成立；或人工数 r115b_gate.json 中 B5 detail 的 fails 截断列表是否真有 8 条（当前 detail 只保留前 3 条，已丢失另 5 条的落盘证据）。

## B6 改锚 + 同步重算 C14 常量后 exit=0：PASS（需限定语）

我独立复算了 B6 全流程（复制镜像树、改 7 行第 4 列为 ANCHOR_SILENTLY_REWRITTEN_R115、按 _recompute_c14 同算法重算 C14_TEXT_SHA256 与 C14_ROW_SHA、跑未打补丁的 chk），得到 rc=0、0 FAIL，NOTE 显示 C14 free-text table fingerprint ok sha256=b17ad257f94d5b25、C11b gap 仍为 7 个、C12 12 anchors hit。脚本记录与我的复算一致。

但“等价于原判据”不成立，需明确限定语：re-pin 后的门禁与原始门禁在 C11/C11b/C12/C13/C15 上确实行为一致（这些检查项不读被改的列或不受影响），但在 C14 上已被主动重写——这是“改判据本身”，不是“保持判据不变却绕过”。B6 证明的是：C14 的 sha 钉是同一代码库里的常量，有写权限者可以同步改表与常量使门禁全绿，即 C14 注释（399 行）自述的边界“sha 钉只能抬高成本，不能防伪造”。这不等于“改锚等价于原判据”——恰恰相反，是判据被改了。

关于“re-pin 后哪些子项不再可能 FAIL”，精确回答如下（针对攻击点 1）：
- C10（门自检，225-239 行）：完全不受 re-pin 影响，也不能被 re-pin 放松。它检查的是某行 r[4] 以 check_disc.py 结尾时 r[5] 里的 GATE_VER 是否等于脚本常量 GATE_VER。B6 的 re-pin 只替换了 C14_TEXT_SHA256 和 C14_ROW_SHA 两个正则匹配，GATE_VER 常量与 DISC_RECHECK.tsv 的第 5/6 列都未改，故 C10 行为不变。但 C10 本身有结构性弱点：它只检查版本标记字符串相等，不检查脚本字节数（226 行注释明确说不用字节数），所以任何保留 GATE_VER='R103' 的脚本改动都不会触发 C10。re-pin 前如此，re-pin 后也如此——但这不是 re-pin 带来的放松，而是 C10 既有设计。
- C14 的 drifted ids 分支（406-417 行）：re-pin 后确实“不再可能 FAIL”对于被改的那 7 行——因为它们的新哈希已被写入 C14_ROW_SHA，整表哈希也匹配。但任何第 8 行再改动仍会 FAIL。所以不是“C14 永远不可能 FAIL”，而是“被 re-pin 覆盖的改动不再 FAIL”。
- 真正被 re-pin 悄悄放松的是：C14 作为“防自由文本漂移”的约束对象被重新定义为攻击者想要的值。C9/C13/C7 对这 7 行的约束仍在（只要不改成占位/错节/删产物），所以 re-pin 后的空间和原判据不同之处仅限 C14 所钉的那部分自由文本。

复算点：
1. 在 re-pin 后的镜像树上，再改一个未被 re-pin 覆盖的行（例如 id 11）的第 4 列，预期 C14 FAIL 并列出 drifted id。
2. 在 re-pin 后的镜像树上，把 r[5]（校验式列）里的 GATE_VER 改为 'R102'，预期 C10 FAIL，证明 C10 不被 re-pin 放松。

## B6b 只改锚不同步常量：对照方向 PASS，理由归因 FAIL

实测 rc=1、1 条 FAIL，唯一 FAIL 是 C14 col2/col3/col4 free-text table changed，drifted ids=['16','19','21','23','31','32','33']。我的独立复算完全一致。问题在 r115b_gate.py:279-280 的 ck 名把它写成“C9 抓垃圾锚、C14 抓指纹漂移”。事实是：C9 完全没有触发。我直接调用 place_r87.is_placeholder('ANCHOR_SILENTLY_REWRITTEN_R115') 得到 (False, '')，因为 place_r87 的 ASCII 占位词表是 garbage/tbd/xxx/na/none/null/todo/fixme/placeholder/dummy/foo/bar/lorem，ANCHOR_SILENTLY_REWRITTEN_R115 不匹配任何前缀，也不是整格占位词。因此这条断言的“C9 抓垃圾锚”是把注释里写的想象当实测结论（攻击点 4 命中）。对照方向成立（exit 1），但归因错误应更正为“只有 C14 抓到指纹漂移；C9 未触发，因为变异值不是占位符”。

复算点：python3 -c 导入 place_r87，对 ANCHOR_SILENTLY_REWRITTEN_R115 调 is_placeholder，应为 (False,'')。再把它改成 'GARBAGE' 重跑 B6b，预期同时出现 C9 与 C14 FAIL，可用来证明 C9 的边界。

## B7 隐含断言“sha 钉只抬高成本不防伪造得到实测支撑”：部分 PASS

B6 实测确实支撑“对 C14 这种把哈希常量写在同库里的钉法，有写权限者可同步改表与常量绕过”。但主会话若据此推广为“所有 sha 钉都只抬高成本不防伪造”，过强。反例就在同一脚本：FREEZE_SHA256（34 行）钉的是 DISC_UNVERIFIABLE.tsv 的整文件哈希（270-273 行），C12 又把冻结行的锚真跑一遍（353-355 行）。只改冻结表并同步 FREEZE_SHA256 会让 C11 的 sha 检查过，但 C12 仍会真跑锚——除非锚本身也改成能命中的值。这不是“同步 sha 就过”，而是需要同时满足内容级约束。B7 应限定为“C14 式的纯自由文本 sha 钉不防伪造”，不能外推到带内容级复核的 sha 钉。

## 攻击点 3：变异实验对照组与镜像树一致性

B4a 基线断言（156-158 行）只检查“未改动的 check_disc.py 在真树上 exit=0”，没有检查“未改动的 check_disc.py 在镜像树上 exit=0”。这是一个真实的设计缺口：B4/B5/B6 都在镜像树上跑，若镜像树与真树行为本来就不一致（例如 mktree 排除了 R17_LEAD_BASELINE、_cards、D41_SUBST，跳过了所有符号链接，而根级 _r94 用 copytree(symlinks=True) 复制），基线只在真树上过不足以保证镜像树也过。r115b_gate.py 的 mktree docstring（106-117 行）自述了初稿三次因镜像不完整导致假 FAIL 的自错（少排基线 → 5 行全 FAIL；符号链接环 → ELOOP；漏根级 _r94 → 31 号 FAIL），说明这个风险是真实发生过的。终版虽然把这些坑补上了，但 B4a 没有把“镜像树空跑 exit=0”作为显式门禁断言写进 ck。当前 B4/B5/B6 都 PASS，且我独立复算 B6 镜像树 rc=0，间接说明终版镜像可用；但实验设计上仍应补一条 B4a-mirror：mktree() 后不改动任何文件，跑 run_gate(root2)，断言 rc=0 且 C11 行与真树一致。这样才能排除“镜像树与真树行为不一致”作为替代解释。

复算点：调用 r115b_gate.mktree()，对返回的 root 直接 run_gate，预期 rc=0；与 B4a 的真树输出逐行比对 NOTE C11 行。

## 需主会话复算的清单

1. B2 降级措辞：对 7 行分别做 C9 占位化、C13 错节化、C7 删产物三项注入，确认各有 FAIL，从而把“完全无约束”改为“仅 claims-有/冻结档防线无约束”。
2. B5 断言强度：把 ck 条件改为 len(fails3)==8 或在 detail 中保留全部 8 条 FAIL，验证“8 条”不是观察偶然而是被锁定的结论。
3. B6b 归因：确认 is_placeholder('ANCHOR_SILENTLY_REWRITTEN_R115') 为 False；用 GARBAGE 重做 B6b 观察 C9+C14 双 FAIL。
4. B6 限定语：在 re-pin 镜像树上再改一个未 re-pin 的行，确认 C14 仍会 FAIL；改 GATE_VER 注册值确认 C10 仍会 FAIL。
5. B4a-mirror 补充：新增镜像树空跑基线断言，排除镜像与真树不一致风险。
6. B4 措辞统一：把调度卡中“可静默摘帽”的初稿声称与脚本中“C12 拦得住”的终稿结论区分为不同条目，避免并列为同时成立的断言。
7. B7 外推边界：确认 FREEZE_SHA256 + C12 内容级复核的组合不能被“同步 sha 即过”绕过，从而限定 B7 只针对 C14 式纯 sha 钉。

## 结论

实验总体方向可信：脚本有真实的自错记录，B4 从初稿错误中被实测纠正，B5/B6b 反向对照都有牙，B6 与我的独立复算一致。但断言文字有四处需要主会话修正或补强：B2 的“完全无约束”过强（C9/C13/C14/C7 仍管）、B4 的初稿措辞与终稿结论混淆、B6b 把 C9 写成触发者而与实测不符、B7 从 C14 外推到所有 sha 钉。另需补一条镜像树空跑基线，以消除对照组环境噪声的替代解释。
