# R148-AUDIT-1 对抗性复核（deepseek 家族，只读）

被审对象：R17_R111_FACTINDEX_V539/FACT_INDEX.tsv（83,637 B，sha256 前 32 位 ec0a63a4c7ef9bafde04dad6a52fa58c，55 行 = 表头 + 54 条）
工作目录：/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14

## 复核表

| 主张 | 我的实测 | 结论 | 一句话理由 |
|---|---|---|---|
| C1（F23 分解 6+2+3=11 ≠ 12） | F23 行 limitations 里三处加数逐字命中，各出现 2 次（原句 1 次 + R138 补的复述 1 次）："6 行为否定式（无 direct caller 等）"、"2 行为 callers 计数"、"真正非否定的多计仅 3 行且全为 direct caller"。算术 6+2+3=11；把"其中 3 行本已在 W 内"当第四个加数则 6+2+3+3=14。两式均复算无误 | 成立（算术部分） | 11 与 14 我都独立复算一致；但"该行没有归属"是推断不是结论——文字并未声明三分项互斥，11 也可能意味着某个分项自身不精确或某行被两分项重叠计入，差 1 行不足以唯一定位缺口 | 
| C2（coverage.tsv 与两个父目录均不在盘） | 全盘 find / -name coverage.tsv 命中 0；find -size 4147334c 命中 0；COVERAGE/ 目录不存在；R17_R41_RECOMPUTE/ 不存在。但 F23 引用的两个父目录之一是工作目录本身：next_re_20261117_r14/ 存在且是当前 cwd。另：4,147,334 B 这个字节数在现盘有 42 行 TSV 台账逐字佐证（含 sha256 c2ee063f…，见 _r67/unique_content_4417.tsv:1022），"11-22 快照清单 4 条记录（主份+3 份 _hygiene）"也在 tier_final_4417.tsv 的第 1022 / 3690 / 3705 / 3712 行独立命中 | 部分成立（"两个父目录都不在"为伪） | 文件本体确实不在盘可证；但"两个父目录都不在"字面错误一个都不成立，且把"内容不可重数"放大成"4,147,334 B 不可复核"，实际字节数与哈希都有现盘副本台账 |
| C3（strict_panel.py 78 行是带方括号的一手判据，两输入不在盘） | 直接读字节：第 78 行为 if "[未证]" not in sem:（0x5B 0x672A 0x8BC1 0x5D 四字节确在行内，非裸子串），嵌套在第 76 行 if grade == "[已证]": 之内，即 proved_strict = atlas 内 [已证] 且 sem 不含 [未证]，与 F35 定义逐字一致；第 14 行散文措辞"proved_n 中 one_line_semantics 不含 [未证]"亦在。两输入 COVERAGE/coverage.tsv 与 lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv 均不存在，其父目录 COVERAGE/ 与 next_re_20261112_r10/ 均不存在，全库 find function_atlas.tsv 与 find -type d -name next_re_20261112* 均为 0 | 成立 | 判据原文、方括号字面、嵌套语义、两输入缺失四项全部独立复现，无一处需要打折 |
| C4（另外三个脚本同判据，写法不完全一样） | 逐行数清：_cards/M59-MERGE/precheck.py:60 为 if "[未证]" not in sem:；simulate.py:72 为 if "[未证]" not in r[3]: d[s]["strict"]+=1；verify.py:83 为 if "[未证]" not in r[3]: strict[s]+=1。三者 r[3] 均指向 one_line_semantics（verify.py:50 校验表头 entry,subsystem,name,one_line_semantics,grade,…），precheck.py:57 还显式写 sem = r[3]，故与 strict_panel.py 判据等价 | 成立（"同判据"可接受），但"独立"一词不成立 | 判据串、列下标、语义三重等价，说同判据没问题；但四个脚本共用同一行 PROJ = r"D:\Project\ra2-campaign-forge" 与同一对输入常量，是同一血缘的克隆而非独立实现，不能互相当交叉验证 |
| C5（4,417 行 / 737,517,286 B 可机械复核；现盘 65 件 / 44,470,975 B） | 不用任何现成求和脚本，按字段下标裸解：正文 4,417 行（换行符 4,418，无 CR，表头 rel/bytes/source/why_content 4 列，4417 行全部 4 字段），sum(第 2 列) = 737,517,286，与主张逐位相同。存在性：以 r14 目录或项目根为基准解析相对路径，命中 0 件 / 0 B；只有以 lead/ 为基准才得到 65 件 / 44,470,975 B，与主张逐位相同 | 成立（两个数都与主张逐位一致），附带两处口径缺项 | 4417 与 737,517,286 我用自己的解析路径独立复现；但 65/44,470,975 只在"相对路径以 lead/ 为基准"这一未写明的口径下成立，且"11-22 快照"在文件内容里无任何日期痕迹（20261122/11-22/快照 命中 0），只能从 mtime 2026-11-22 18:41 反推 |

## 逐条的最小可复算命令（均在 lead/next_re_20261117_r14 下执行）

C1：
    awk -F'\t' '$1=="F23"{print $5}' R17_R111_FACTINDEX_V539/FACT_INDEX.tsv | python3 -c 'import sys;t=sys.stdin.read();print([(p,t.count(p)) for p in ("6 行为否定式","2 行为 callers 计数","多计仅 3 行","6+2+3=**11**","6+2+3+3=14")],6+2+3,6+2+3+3)'

C2：
    find /home/t628/projects/ra2-campaign-forge -name coverage.tsv -o -type f -size 4147334c | head; ls -ld COVERAGE R17_R41_RECOMPUTE . 2>&1; grep -c 'COVERAGE/coverage.tsv' R17_R101_TIER_FINAL_4417/tier_final_4417.tsv

C3：
    sed -n '14p;78p' RULING_R15_20261119/work/strict_panel.py; sed -n '20,24p' RULING_R15_20261119/work/strict_panel.py; ls -l COVERAGE/coverage.tsv ../next_re_20261112_r10/W130_atlas/function_atlas.tsv 2>&1

C4：
    grep -n '未证' _cards/M59-MERGE/precheck.py _cards/M59-MERGE/simulate.py _cards/M59-MERGE/verify.py RULING_R15_20261119/work/strict_panel.py

C5：
    awk -F'\t' 'NR>1{n++;s+=$2}END{print n,s}' R17_R101_TIER_FINAL_4417/tier_final_4417.tsv
    python3 -c "import os;b='/home/t628/projects/ra2-campaign-forge/lead';r=[l.split('\t')[0] for l in open('R17_R101_TIER_FINAL_4417/tier_final_4417.tsv',encoding='utf-8').read().split('\n')[1:] if l.strip()];e=[p for p in r if os.path.exists(os.path.join(b,p))];print(len(r),len(e),sum(os.path.getsize(os.path.join(b,p)) for p in e))"

## 追加取证（主张未提、但会改结论的两处）

1. F23 与 F35 各有一项 evidence_paths 整条失联：F23 的 R17_DELIVERY/DELIVERY_SUMMARY.md 与 COVERAGE/PANEL.md 均实测不存在；F35 的 COVERAGE/PANEL.md 同样不存在，而其余三项（strict_panel.py 与 _cards/M59-MERGE 三脚本）在盘。故 F35 现在靠的不再是二手转述，但 F23 仍是整行证据链失联，且其 grade 却写着 [已证]。
2. 4,147,334 B 的可复核性来自副本台账而非原件：_r67/unique_content_4417.tsv 给出该路径的 sha256 c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a，tier_final_4417.tsv 第 1022 行给出同一字节数，三条 _hygiene 备份分别记 3,659,609 / 3,663,149 / 3,683,786 B，大小互不相同，故"4 条记录"是主份 + 3 份不同世代备份，不能当作互校。

## 最可能被误读的一处

C2 的"该文件与它的两个父目录都不在现盘"。这句话被读成"coverage.tsv 及其上层两条路径全部消失"，实际上第二个父目录 next_re_20261117_r14/ 正是当前工作目录，一个字面为伪的判断会让人顺带怀疑整条 lead/ 目录的可信度；更危险的是它把"内容不可重数"顺势读成"F23 一切不可复核"，而 4,147,334 B 这个字节数在现盘有 42 行台账加一个 sha256 钉住，真正不可复核的只有 458/291/293/1,196/1,654 这些计数本身。次一级易误读处是 C5 的 65 件 / 44,470,975 B：该数依赖"相对路径以 lead/ 为基准"，不写这个基准，任何人复算都会得到 0 件 / 0 B 并误判主张为伪。
