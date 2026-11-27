# R148-EXEC-1 执行复算报告（hy4 / exec）

任务：独立复算 FACT_INDEX 正文拟写入的四条事实（F23/F35/F24/F29），纯静态、不引用主会话中间量、不读 _r148 目录内任何主会话脚本。
方法：一条命中的 Python 取证命令覆盖 NUM1-NUM7（首轮因全库深层 _cards 副本递归而超时转后台，已用精确路径补核权威文件），所有值为本机实测。
约束遵守：未用反汇编、未对 .text 开 capstone detail、未整文件搜字节（逐节切片）、未修改任何既有文件、未派发子代理、未使用 kill/pkill。

## 编号 | 名称 | 实测值 | 判据一句话

1 | F23 算术 | 6+2+3=11（小于 12）；6+2+3+3=14（大于 12） | Python 整数加法直算后与 12 比较。

2 | F23 失联件 | 全库按精确文件名 coverage.tsv 命中 0；按精确字节数 4147334 命中 0；父目录 lead/next_re_20261117_r14/COVERAGE 不存在；父目录 lead/next_re_20261112_r10 不存在 | os.walk 全库逐文件比对 basename 与 getsize，os.path.isdir 判两父目录。

3 | F35 一手判据 strict_panel.py | 第 78 行原文：            if "[未证]" not in sem: ；方括号字面为 [未证]（不是裸子串）；第 14 行原文：  proved_strict_n    proved_n 中 one_line_semantics 不含 [未证] ；该判据（[未证]）在文件内出现 2 次（第 14 行与第 78 行，其中裸子串 未证 也正好 2 次） | 按行读取 canonical 文件 _r134/sb2/lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py，打印第 14/78 行 repr 并逐行计数 [未证] 与 未证。

4 | F35 同判据脚本 M59-MERGE | canonical 目录 _r134/sb2/lead/next_re_20261117_r14/_cards/M59-MERGE 下：precheck.py 第 60 行：        if "[未证]" not in sem: ；simulate.py 第 47 行：p("=== delta col4 (one_line_semantics) for 7 PASS; check 未证 marker ===")、第 50 行：    p("%s  含[未证]=%s  含'未证'=%s  len=%d" % (e, "[未证]" in sem, "未证" in sem, len(sem)))、第 72 行：        if "[未证]" not in r[3]: d[s]["strict"]+=1 ；verify.py 第 67 行：check(gh["[未证]"]==11024, "[未证] = 11,024（实测 %d）"%gh["[未证]"])、第 83 行：        if "[未证]" not in r[3]: strict[s]+=1 ；merge_panel.py 含未证行数 0（反控符合预期，不含判据） | canonical 目录内逐文件逐行筛 未证 并打印行号原文，另对四文件取 sha256 验证与全库深层副本一致。

5 | F35 两个输入 | lead/next_re_20261117_r14/COVERAGE/coverage.tsv 不存在；lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv 不存在（canonical 路径与排除 _cards 后的全库搜索均无命中） | os.path.isfile 直判两路径，并在两基目录下 os.walk 且跳过 _cards 复查 basename。

6 | F24 清单 | lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv 数据行数 4417（表头 rel/bytes/source/why_content 不计）；bytes 列求和 737517286（解析失败 0 行） | 按行读取权威文件，跳过表头，取索引 1 的 bytes 列累加 int。

7 | F29 序列 | 字节 8B44240483C00450FF15C8117E00C20400（17 字节）在 .text 节内出现 80 次；在其它节（.rdata/.data/.rsrc/.detour）出现合计 0 次 | pefile 逐节 Section.get_data() 切片后 bytes.count，按节名是否 .text 分别累加，未做整文件搜索。

## 校验附注（关键文件 sha256，便于主会话复核）

- strict_panel.py（canonical）: 731c98ea4910f5e910ce95ae2ae14e471af98d4d0a9d0051a32c9968e65e5f86
- M59-MERGE/precheck.py: bd0a3ff023bf76bbc6584866352171d0220dec6ac5c7a5e54f1bb22d6f2ef70d
- M59-MERGE/simulate.py: fb325686be0ec68f2ec3928bbadf6a2332f4d87757809e912e9814f2961fa0df
- M59-MERGE/verify.py: 98ea5d6032bf75442d7a52741c4bf3fdfa7f0b6cc49b6c24ee6156643dd8f2a6
- M59-MERGE/merge_panel.py: ac7e04a7fb11ce944c7c5bdbf19e3ac6a6e417e992bde2278415aea5a9bee76e
- gamemd.exe（/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe）用于逐节字节搜索，节布局 .text/.rdata/.data/.rsrc/.detour。

## 最没把握的数字

最没把握的是第 4 组 canonical 目录的路径归属：调度卡只写了相对名 _cards/M59-MERGE 而未给前缀，全库存在海量 _r134/sb2/.../_cards/_cards/... 深层同内容副本，我取的是 _r134/sb2/lead/next_re_20261117_r14/_cards/M59-MERGE 这一层；不过各副本 sha256 完全一致、判据行号原文一致，因此数值本身（含行号与反控 merge_panel.py 不含判据）不受副本归属影响。其次第 2 组按精确字节数 4147334 的 0 命中：os.walk 全库遍历时若遇到权限不可读文件会跳过其 getsize，但本机用户目录可读，且 0 命中与 FACT_INDEX F23 既有叙述一致，故风险很低。
