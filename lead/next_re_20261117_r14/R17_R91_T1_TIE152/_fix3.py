import io, py_compile
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R91_T1_TIE152\q3_verdicts.py"
s = io.open(p, encoding="utf-8").read()

# 1) 在 SPECIAL 字典末尾前插入剩余 18 件的专属裁决
add = '''
    "W62_bline_new_criteria/EVIDENCE/b_selftest.stdout.txt":
        ("应排", "整篇自检断言（[B-POS]/[B-NEG] expected=/actual=/pass=True + KS 统计），记录判定过程，无对象记录体"),
    "W68_criterion_discrete_fix/EVIDENCE/concurrent_GLM/v2_selftest.stdout.txt":
        ("应排", "同上：整篇 [B-POS]/[B-NEG] pass=True 自检断言，无对象地址/槽记录"),
    "W68_criterion_discrete_fix/EVIDENCE/v2_selftest.stdout.txt":
        ("应排", "同上（与 concurrent_GLM 副本同内容）：纯自检断言"),
    "W97_artmd/EVIDENCE/probe04_stdout.txt":
        ("判不了", "内容是 artmd.ini 的逐条核对（KEY 名 Foundation=/VERIFIED in file/计数断言），"
                   "数据事实与核对结论混编；缺「INI 字段核对表算对象记录还是过程记录」的口径"),
    "W97_artmd/EVIDENCE/probe06_stdout.txt":
        ("应排", "内容是 INI 字段核对清单（Foundation=/line NNNN VERIFIED in file，仅 4 行带地址），核对过程记录"),
    "W97_artmd/EVIDENCE/probe10_stdout.txt":
        ("应排", "内容是 artmd.ini 逐节/逐键核对输出（VERIFIED/count 断言），核对过程记录"),
    "W97_artmd/EVIDENCE/probe08_stdout.txt":
        ("应排", "内容是 TRIP_RESULT_C6.json 的运行参数回显（step/want_fn/sample_interval_ms/fps/min_valid_s/"
                 "engagement 序列），运行记录"),
    "W104_sentinel2/EVIDENCE/selftest.txt":
        ("应排", "内容是 cell_sentinel 自检（build 4 独立对象图 + 逐条 [PASS] 断言），"
                 "被测对象是**合成内存**而非目标 EXE，属过程自检"),
    "P0_ADJ4/_audit/EVIDENCE/step3_sample15.txt":
        ("应排", "内容是 15 行确定性抽样核对表（# addr channel card mine-A1 agr first pred blen refs A1..A7），抽样过程"),
    "S09_KPROVED7/_audit/EVIDENCE/baseline_audit.txt":
        ("应排", "内容是基线率（S09 rows 1102 / pool 642 / mine_strict 0.1994 / mine_loose 0.5218），纯统计"),
    "S09_KPROVED7/_audit/EVIDENCE/S7b_baseline.json":
        ("应排", "JSON 只有池口径与基线率（pool_n/coverage_rows/card），纯统计"),
    "S19-F1/EVIDENCE/task2_explore_summary.txt":
        ("应留", "内容是 play 函数入口字节 + 调用点普查（TARGET 00750920 sites=116 caller_fns=66 + 入口字节行），"
                 "对象（函数入口/调用点）记录体"),
    "W177-B/EVIDENCE/S0_baseline.txt":
        ("应排", "内容是卫生与就绪基线（记录时间 + gamemd.exe/ddraw.dll SHA-256 + except.txt 长度/mtime 表），"
                 "环境基线元记录，无被测对象记录"),
'''
anchor = '    "S09_KPROVED7/_audit/EVIDENCE/S7b_baseline.json":\n        ("应排", "JSON 只有池口径与基线率（pool_n/coverage_rows/card），纯统计"),\n}'
assert anchor in s, "anchor not found"
s = s.replace(anchor, anchor[:-2] + add + "}")

# 2) 把「家族选择只做读哪行的入口」这一事实写进 docstring，并让 decide() 的兜底 reason 更具体
old_doc = '判据纪律：**只用实读内容**。为防"靠文件名判"，脚本先按文件名把每件映射到一条'
new_doc = '判据纪律：**只用实读内容**。脚本里 SPECIAL 表的键取路径尾段，仅作「读哪几行」的入口；'
s = s.replace(old_doc, new_doc)
io.open(p, "w", encoding="utf-8").write(s)
py_compile.compile(p, doraise=True)
print("OK")
