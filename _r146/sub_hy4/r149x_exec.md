七项结论: 清单54行/5列/F01..F54连续/分号178项; 失联16条唯一路径/43项; 零存活仅F23; 台账§数字节661个, §1062/1063/1064/1065存在而§1063R不存在; 21个锚点全部逐字命中; 反控通过(假串未命中、旧值108/82/4/33与不得引用同现); coverage.tsv全库0命中(FACT_INDEX.tsv 11目录), 台账458=102次/291=69次/1,196=24次。

## 1. 清单事实
命令: python3 读 FACT_INDEX.tsv, splitlines, 逐行 split(tab), hashlib.sha256(二进制流)
原始终输出摘录:
  data_rows: 54
  header: ['fact_id','statement','grade','evidence_paths','limitations']
  col_counts: [5]
  fids_F01_F54_contiguous: True
  fid_first_last: F01 F54
  semicolon_items_total: 178
  sha256: fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a
  bytes: 88786
事实: 第4列 evidence_paths 按分号切得178项; 54行且F01..F54连续; 列数恒为5。

## 2. 失联路径
命令: 对每行第4列按分号切项, 每项按第一个左圆括号切掉锚点, 反斜杠换正斜杠, 分别以仓库根和以 lead/ 为基准 os.path.exists 判存在; 取两者都不存在者为失联。
原始输出摘录:
  total_evidence_items: 178
  missing_items: 43
  unique_missing_paths: 16
  全部16条失联路径(字面清单, 均相对仓库根):
  MP01 lead/next_re_20261117_r14/COVERAGE/PANEL.md
  MP02 lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md
  MP03 lead/next_re_20261117_r14/HANDOFF_R14_R3.md
  MP04 lead/next_re_20261117_r14/HANDOFF_R16.md
  MP05 lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md
  MP06 lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md
  MP07 lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md
  MP08 lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md
  MP09 lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md
  MP10 lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md
  MP11 lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md
  MP12 lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md
  MP13 lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md
  MP14 lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md
  MP15 lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md
  MP16 lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md
注: 失联项43条 > 唯一路径16条, 因同一路径被多行重复引用; 其中五个 R17_LEDGER_* SECTION.md 的引用次数分别为 1062=5, 1063=4, 1063R=1, 1064=5, 1065=2。

## 3. 零存活证据的 fact
命令: 逐行统计 evidence_paths 项数与失联项数, 存活=项数-失联数, 筛存活=0。
原始输出:
  F23 [已证] items=2
  zero_live_count: 1
事实: 唯一零存活行是 F23(grade 已证), 其2个证据项全部失联。

## 4. 台账合并
命令: 读 lead/GOAL_THREE_TARGETS_20261018.md, re.findall(r'^## (§\d+)', text, re.M) 计数; 再按 ^## (§[^\s]+) 逐节取 body(切到下一 ## 行)。
原始输出摘录:
  section_total (regex ^## (§\d+)): 661
  §1062 EXISTS sections=1 total_chars=5653
  §1063 EXISTS sections=1 total_chars=4984
  §1063R ABSENT
  §1064 EXISTS sections=1 total_chars=4838
  §1065 EXISTS sections=1 total_chars=3611
  all headers starting with §106 (原文):
    ## §1060 · 书记员覆盖 R17 第 7–8 轮（vtable 定名 + slot73 全映射 + 两审 + GLM 两卡）：九事项草稿
    ## §1061 · 书记员覆盖 R17 第 9 轮（槽73 语义闭环 + RTTI 交叉核对）：身份与覆写升为字节证实、语义仍缺，RTTI 对账仅判「不矛盾」
    ## §1062 · 书记员覆盖 R17 第 10 轮（首次拿到 0x43F180 调用方 + 对账第三版定谳 + 三审）：事项 1–7 全落、三根红线全写
    ## §1063 · 书记员覆盖 R17 第 11 轮（一条结论作废 + 一处方法学缺陷 + 交付件同步）：两条负面记录与五项配套证据
    ## §1064 · 书记员覆盖 R17 第 12 轮（0x449440 函数体定性 + 一条限制被精度化）：跨家族审计证明新增的是限制、不是支持
    ## §1065 · 书记员覆盖 R17 第 13 轮（三条负面结果同时收口）：事实边界与假设证伪台账草稿
    ## §1066 · 书记员起草台账（R17 第 14 轮：事实底座索引 + 0x5657A0 表基址 + 一次假冲突被澄清）
    ## §1067 · 书记员起草台账（R17 第 15 轮：交付件被审计并升级 + 一处高危误引被堵）
    ## §1068
    ## §1069
特别确认: §1063R 这一节不存在。台账只有 §1063, 其后直接是 §1064; FACT_INDEX 中那条 R17_LEDGER_1063R/SECTION.md 证据路径在台账里无任何同编号节支撑。⚠ 修正说明: 首轮脚本误用 r'^## (§\d+)\s*$' 要求行尾即编号, 得56节且节内容全空, 这是本人脚本 bug; 已按调度卡原口径 r'^## (§\d+)' 重测, 得661节与上述字符数, 废弃首轮数据。

## 5. 事项级锚点
命令: 对给定 fid 取对应节 body, 对每个字面锚点做 Python in 判定。
原始输出(全部21项):
  F04 -> §1062 (5653 chars)
    0x43F180 HIT
    0x5A66D4 HIT
    0x5A6860 HIT
    0x5A6510 HIT
  F06 -> §1064 (4838 chars)
    117 HIT
    0x4494B5 HIT
    C2 14 00 HIT
  F07 -> §1064 (4838 chars)
    0x449493 HIT
    0x47C620 HIT
    [edx+0xA8] HIT
  F08 -> §1064 (4838 chars)
    0x449440 HIT
    a′ HIT
  F10 -> §1065 (3611 chars)
    1439 HIT
    0x5A5020 HIT
  F15 -> §1063 (4984 chars)
    129 HIT
    125 HIT
    84+35+1+5+4 HIT
  F16 -> §1063 (4984 chars)
    0x5A6510 HIT
    0x5A531E HIT
    slot73 HIT
事实: 7个fid共21个锚点, 逐字全部命中对应台账节。(第4项中已说明首轮全MISS为脚本正则缺陷, 此处为修正后结果。)

## 6. 反控
命令: 在 §1063 body 上查假串与各旧值、不得引用。
原始输出:
  ZZZ_NOT_IN_LEDGER_QQQ in §1063: False
  old_value 108 in §1063: True
  old_value 82 in §1063: True
  old_value 4 in §1063: True
  old_value 33 in §1063: True
  不得引用 in §1063: True
  §1063 chars: 4984
证据行(原文摘录):
  - 红线一：R25 的结论不得引用（该结论不得引用）。
  - 口径说明：R17_R28_R12_REPAIR/stats.tsv 记录的是早期中间态（108/82/4/33），已被 R17_R28_R12_REPAIR/REPORT.md 取代，不得引用；REPORT.md 才是权威。
  - 复算：卡面当时引的是 stats.tsv 的 108/82/4/33，本次修订按 host_fix.tsv 与 REPORT.md 更正为 129/125/5/19；这是 Lead 派发卡引用过期中间态造成的，不是执行方错。
结论: 假串未命中, 证明第5项HIT非恒真; §1063 同时含被作废旧值108/82/4/33与不得引用, 且旧值语境明确标注为作废、权威值为129/125/5/19。

## 7. F23 底层可重数性
命令: os.walk(ROOT) 排除 .git 与 __pycache__, 按 basename 精确匹配 coverage.tsv 与 FACT_INDEX.tsv 统计目录数; 台账全文 text.count 三个串。
原始输出:
  coverage.tsv_hits: 0
  FACT_INDEX.tsv_hits: 11
    lead/next_re_20261117_r14/R17_R102_FACTINDEX_V530
    lead/next_re_20261117_r14/R17_R103_FACTINDEX_V531
    lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532
    lead/next_re_20261117_r14/R17_R105_FACTINDEX_V533
    lead/next_re_20261117_r14/R17_R106_FACTINDEX_V534
    lead/next_re_20261117_r14/R17_R107_FACTINDEX_V535
    lead/next_re_20261117_r14/R17_R108_FACTINDEX_V536
    lead/next_re_20261117_r14/R17_R109_FACTINDEX_V537
    lead/next_re_20261117_r14/R17_R110_FACTINDEX_V538
    lead/next_re_20261117_r14/R17_R111_FACTINDEX_V539
    lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540
  ledger_count '458': 102
  ledger_count '291': 69
  ledger_count '1,196': 24
事实: coverage.tsv 全库0目录命中; 正控 FACT_INDEX.tsv 命中11目录(>=10满足); 台账中458出现102次、291出现69次、1,196出现24次。

## 我没能测到的项
无。七项均已取得实测值。需要说明的两点局限: (a) 失联判定是在现盘用存在性检查做的, 未追查这些路径是否在历史版本存在过或被移动到别处; (b) FACT_INDEX 第4列各路径的字面锚点(括号内文字)未逐一与台账节核对, 仅按调度卡要求核对了第5项列出的锚点。
