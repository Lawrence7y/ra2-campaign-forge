# R136-HY4 · 审计 deepseek 的 F24 存活率复算 + 独立复核「86.19% 无字节对应」

角色 audit / 家族 hy4 / provider magpie-anthropic / model work/cn:hy4flash
执行机 t628，只读；工程根 `/home/t628/projects/ra2-campaign-forge`。所有中间产物仅写 `_r136/sub_hy4/`，临时反汇编写 `/tmp/hy4_objd.txt` 并在末尾清理。

审计脚本（本目录）：`hy4_a.py`（A1–A5）、`hy4_b.py`（B1–B5）；机读输出 `hy4_a.json`、`hy4_b.json`、`hy4_b.out`；本文件为唯一交付报告。

---

## A · 审 deepseek 回件

口径前置（自己读表头，不抄报告）：

```
$ awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)printf "col%d=%s  ",i,$i; print ""}' lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv
col1=rel  col2=bytes  col3=source  col4=why_content

$ awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)printf "col%d=%s  ",i,$i; print ""}' lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv
col1=rel  col2=ext  col3=bytes  col4=mtime_ns  col5=selfkind
```

### A1 · 清单 4,417 行 / 737,517,286 B

- 被审主张/预期：4,417 数据行 / sum(bytes)=737,517,286 B。
- 我的实测值：**4,417 行 / 737,517,286 B**；NF=4 的行 4,417，无残缺行。`wc -l` 得 4,418 含表头，减 1 得 4,417。
- 命令与输出原文：

```bash
$ python3 _r136/sub_hy4/hy4_a.py > _r136/sub_hy4/hy4_a.json
$ python3 -c "import json;d=json.load(open('_r136/sub_hy4/hy4_a.json'));print(d['A1'])"
{"n": 4417, "sum_bytes": 737517286, "nf_dist": {"4": 4417}}
```

### A2 · 三桶：64 相同 / 1 不同 / 4,352 不存在；rel 根 = `lead/`

- 被审主张/预期：64 / 1 / 4,352；rel 相对 `lead/` 而非工程根。
- 我的实测值：**same=64（清单值 26,846,620 B）、diff=1（a2_sites.json）、enoent=4,352（清单值 709,757,429 B）、other=0**。三桶件数和 4,417，与 A1 相等。根反控：用 5 个清单外已知文件验证，`lead/` 根 **5/5 命中**，工程根 **0/5**，`lead/next_re_20261117_r14/` **0/5** —— 根判断成立。
- 命令与输出原文：

```bash
$ python3 -c "import json;d=json.load(open('_r136/sub_hy4/hy4_a.json'));print(d['A2']);print(d['A2_controls'])"
{"buckets":{"same":64,"enoent":4352,"diff":1},
 "listed_bytes":{"same":26846620,"enoent":709757429},
 "diff_detail":[{"rel":"next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json","listed":913237,"current":17624355}]}
# 清单外 5 件：R14_COMMON.md / COMPACT_STATE.md / DISC_ESTABLISH.tsv / FACT_INDEX.tsv(V530) / CLEANSCALE REPORT.md
in_manifest=false, lead_hit=true(5/5), root_hit=false(0/5), r14_hit=false(0/5)
```

### A3 · 唯一 diff 件：文件被改坏 vs 清单裁剪后的逻辑体量

- 被审主张/预期：清单值 913,237，盘上 17,624,355；判为「清单记剔后逻辑体量、盘上未落地」，非文件损坏。
- 我的实测值：`stat` = **17,624,355 B**，清单 = **913,237 B**，差 **+16,711,118 B**。JSON 顶层键 `calls`(dict, 6,728 项) / `bounds`(list, 1,392,592 条十六进制字符串)。`json.dumps(d["bounds"])` 长度 16,711,104 B；`json.dumps(d["calls"])` 长度 913,228 B。三者强吻合：`913,237 ≈ calls 序列化长 913,228`（差 9 B，疑为外层 `{}`/键名或其他序列化细节），`17,624,355 − 16,711,118 = 913,237` 精确等于清单值。
- 判据（不只给结论）：①差值与 F24 正文「剔 bounds 段 16,711,118 B」数值精确相等；②算术闭合 `17,624,355 − 16,711,118 = 913,237`；③盘上 JSON 仍有 1,392,592 条 bounds，即**未剔原件**仍在，若是「改坏」不会恰好留下与被剔段等长的差；④`calls` 单独序列化长度 913,228 与清单值同量级同数量级吻合。四条一致 → **清单记裁剪后逻辑体量，盘上未落地；不是文件损坏**。我未验证 9 B 残差的具体来源，标「未测」。
- 命令与输出原文：

```bash
$ stat -c '%n %s bytes' lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json
lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json 17624355 bytes
$ python3 -c "import json;d=json.load(open('_r136/sub_hy4/hy4_a.json'));print(d['A3'])"
{"stat":17624355,"keys":{"calls":"dict","bounds":"list"},"bounds_n":1392592,"calls_n":6728,
 "bounds_dumps_len":16711104,"bounds_dumps_compact_len":15318513,"calls_dumps_len":913228,
 "listed":[913237],"delta":16711118}
```

### A4 · 4,352 缺失件在 snap2 中命中（bytes 取第 3 列），随机抽 30 件

- 被审主张/预期：4,352 件 100% 在快照里且 bytes 逐字节相同；快照 bytes 在第 3 列。
- 我的实测值：**抽 30 件（seed=136，从全部 4,352 件中随机、非它列的那 3 件），命中 30/30，bytes 全相同，不同 0，未找到 0**。我自己的表头也确认 bytes 是第 3 列（见上方 A0_snap_header）。
- 命令与输出原文：

```bash
$ python3 -c "import json;d=json.load(open('_r136/sub_hy4/hy4_a.json'))['A4'];print(d['missing_n'],d['sample_n'],d['hits'])"
4352 30 30
```

抽样明细（rel / snap 第 3 列 bytes / 清单 bytes）：

| # | rel | snap bytes | manifest bytes |
|---:|---|---:|---:|
| 1 | `next_re_20261117_r14/W174_dirty80/_audit/out/a6_site_base.tsv` | 13688 | 13688 |
| 2 | `next_re_20261117_r14/SEMFIX_SLOTS3/EVIDENCE/ROW_004F4320.txt` | 2516 | 2516 |
| 3 | `next_re_20261112_r10/W135_ds/T4_textcov/candidates.tsv` | 552016 | 552016 |
| 4 | `next_re_20261117_r14/W176_place81/EVIDENCE/T1_disasm_005F5850.txt` | 2843 | 2843 |
| 5 | `next_re_20261117_r14/NAMED_PUSH_S18_B4/EVIDENCE/ROW_007AA870.txt` | 4053 | 4053 |
| 6 | `next_re_20261117_r14/R16_MERGE_PIVOT32/_staged_coverage.tsv` | 4088277 | 4088277 |
| 7 | `next_re_20261117_r14/TIEBREAK_ENGFAM/EVIDENCE/atexit35.txt` | 9096 | 9096 |
| 8 | `next_re_20261117_r14/NAMED_PUSH_AUDIT4/verdict.tsv` | 6802 | 6802 |
| 9 | `next_re_20261117_r14/NAMED_PUSH_S20_B1/_work/b1_entries.txt` | 553 | 553 |
| 10 | `next_re_20261117_r14/NAMED_PUSH_S20_B3/EVIDENCE/ROW_0075F8B0.txt` | 5163 | 5163 |
| 11 | `next_re_20261112_r10/W110_crash/out/_archive_run5/trip_crash_step2_r1/archived_except.txt` | 26804 | 26804 |
| 12 | `next_re_20261117_r14/NAMED_PUSH_S18_B1/work/dump_sites.txt` | 125382 | 125382 |
| 13 | `next_re_20261112_r10/W135_ds/T3_registry/dumps/BROADCAST_unknown_004DB3C0.txt` | 7641 | 7641 |
| 14 | `next_re_20261112_r10/W110_crash/out/trip_scan_near_r1/baseline_except/except.txt` | 26794 | 26794 |
| 15 | `next_re_20261117_r14/R16_MERGE_D1_WIDE_B2/_pin_coverage.tsv` | 4108800 | 4108800 |
| 16 | `next_re_20261117_r14/R16_F1_B1/delta.tsv` | 26221 | 26221 |
| 17 | `next_re_20261117_r14/S09_KPROVED5/EVIDENCE/DISASM_004E1A40.txt` | 251 | 251 |
| 18 | `next_re_20261117_r14/S15-K2/EVIDENCE/T1_S15_coverage_dump.tsv` | 30831 | 30831 |
| 19 | `next_re_20261117_r14/SEMFIX_ENGFAM_B2/_audit/ev/ROW_00680870.txt` | 8887 | 8887 |
| 20 | `next_re_20261117_r14/NAMED_PUSH_S14_B1/EVIDENCE/ROW_00512290.txt` | 3515 | 3515 |
| 21 | `next_re_20261112_r06/W91_approach/out/trip_P1/archived_except.txt` | 26579 | 26579 |
| 22 | `next_re_20261116_r12/W163_dirtyrect/EVIDENCE/add_disasm.stdout.txt` | 11784 | 11784 |
| 23 | `next_re_20261117_r14/S09_KPROVED/EVIDENCE/dis_0063FEA0.txt` | 20245 | 20245 |
| 24 | `next_re_20261112_r06/W92_crash_triage/work/W88_C1_except.txt` | 26515 | 26515 |
| 25 | `next_re_20261112_r10/W110_crash/out/_archive_prev2/trip_speed99_r1/baseline_except/except.txt` | 26794 | 26794 |
| 26 | `next_re_20261117_r14/P0_GATE_B/_audit/a2_47c3d0_full.txt` | 5520 | 5520 |
| 27 | `next_re_20261117_r14/S11-K2/_audit/a3_run.log` | 13960 | 13960 |
| 28 | `next_re_20261117_r14/S09_KPROVED/_audit/EVIDENCE/dis_004AAE90.txt` | 47241 | 47241 |
| 29 | `next_re_20261117_r14/S10_K4/_audit/EVIDENCE/a8_frame_writers.txt` | 7409 | 7409 |
| 30 | `next_re_20261117_r14/R16_SIEVE_D1_WIDE/debug_17.txt` | 705 | 705 |

### A5 · 「627 件 / 29,944,200 B」与实际 13,233,082 B 的差

- 被审主张/预期：F24 正文 627 件 29,944,200 B；清单实际 13,233,082 B；差 16,711,118 B = 被剔 bounds 段。
- 我的实测值：清单 `rejudge_R53_对象抄本` 桶 **627 件 / 13,233,082 B**；F24 正文 **29,944,200 B**；差 **16,711,118 B**，与 A3 的 bounds 差值 **精确相等**。`29,944,200 − 16,711,118 = 13,233,082` 闭合。
- 命令与输出原文：

```bash
$ python3 -c "import json;d=json.load(open('_r136/sub_hy4/hy4_a.json'));print(d['A5'])"
{"manifest_627_n":627,"manifest_627_bytes":13233082,"f24_claimed_627_bytes":29944200,
 "claimed_minus_manifest":16711118,"bounds_delta":16711118,
 "f4413_rows":4413,"f4413_sum":744172839}
```

### A6 · deepseek 未测项，及是否有未测项能翻掉其主结论

- 被审主张/预期：找出声明未跑项；判断能否翻主结论。
- 我的实测值：deepseek 在「分歧 5」显式声明 3 项未跑：①删除动作的发生时刻与执行者（未定位具体删除事件）；②`mesh_imm32.json` 等大件去向未追查；③未对 4,352 件逐条人工 `ls`（只人工 3 件，程序化 `os.stat` 全量覆盖）。
  - ①只影响归因（谁删、何时删），**不影响**「现盘 65 件存活 / 4,352 件 ENOENT / 1 件 diff」这组计数；②只影响去向解释，不影响件数；③程序化 stat 已全量覆盖，抽 30 件由我独立复核 30/30 一致，人工 ls 属冗余。
  - **结论：三项未跑均不能翻掉其主结论（现盘存活 65/4,417）。** 另外我自查发现 deepseek 的 A2「other=0」以外的数值均可复算；它未测 B 类「bound 地址是否真有字节」——这属于本卡 B 部分，且**它会翻掉 F24 的那句 86.19% 依据，但不翻 deepseek 的存活率复算结论**。
- 命令原文：直接读 `_r136/sub_deepseek/REPORT.md` 的「分歧 5」节（只读）。

---

## B · 独立复核「86.19% 盘上无任何字节对应」

### B1 · objdump 指令起始地址全集

- 预期：用 objdump 生成 .text 指令起始地址；70 MB 文本逐行流式解析。
- 我的实测值：**1,392,516 个唯一指令起始地址**（objdump 输出 1,392,528 行，含 12 行文件头/段头等），地址范围 `0x401000`–`0x7e038c`。
- 命令与输出原文：

```bash
$ timeout 180 i686-w64-mingw32-objdump -d --no-show-raw-insn ra2bench/gamemd.exe > /tmp/hy4_objd.txt
$ wc -l /tmp/hy4_objd.txt
1392528 /tmp/hy4_objd.txt
$ python3 _r136/sub_hy4/hy4_b.py | head -1
B1 objdump_lines= 1392528 starts_total= 1392516 min= 0x401000 max= 0x7e038c
# 解析：`^\s*([0-9a-fA-F]{6,8}):\s` 逐行匹配，仅入集合，不驻留全文
```

### B2 · bounds 落在指令起始集合的命中/未命中

- 被审主张：F24 说 86.19%（1,200,251/1,392,592）「盘上无任何字节对应」，即命中应只有 ~13.81%（~192,341）。
- 我的实测值：bounds **1,392,592 条**（全唯一）。**命中 1,392,481 条（99.992029%），未命中 111 条（0.007971%）**。与 F24 方向相反：几乎全部 bounds 地址都是 objdump 的指令起始地址，即盘上有对应字节且是某条指令的起点。
- 命令与输出原文：

```bash
$ python3 _r136/sub_hy4/hy4_b.py | sed -n '2p'
B2 bounds_n= 1392592 bounds_unique= 1392592 hit= 1392481 miss= 111 hit_pct=99.992029 miss_pct=0.007971
```

### B3 · 111 条未命中的逐条分析

- 预期：若 F24 成立，未命中应大批落在指令中间，且距前一指令起点较远。
- 我的实测值：111 条未命中**全部**距紧邻前一指令起始地址 **1–8 字节**（直方图：Δ1=71、Δ2=16、Δ3=3、Δ4=9、Δ5=1、Δ6=6、Δ8=5；无 Δ>8）。例如 `0x46f5a1` 前指令 `0x46f5a0`（Δ1），`0x71f296` 前指令 `0x71f294`（Δ2），`0x792af7` 前指令 `0x792af5`（Δ2）。**这些是更长指令的中间字节（objdump 与另一反汇编器切法不同），不是「盘上无字节」**：它们都在 .text 范围内、紧邻指令起点，且 objdump Same-function 上下文可见其被更长指令覆盖。
- 完整 111 条（`prev_delta` = 地址 − 前一指令起始）：

| # | bounds 地址 | 前一指令起始 | 差值 |
|---:|---|---|---:|
| 1 | `0x46f5a1` | `0x46f5a0` | 1 |
| 2 | `0x48db26` | `0x48db25` | 1 |
| 3 | `0x48db27` | `0x48db25` | 2 |
| 4 | `0x48dd19` | `0x48dd18` | 1 |
| 5 | `0x4c8115` | `0x4c8114` | 1 |
| 6 | `0x5001e5` | `0x5001e4` | 1 |
| 7 | `0x58bda5` | `0x58bda4` | 1 |
| 8 | `0x69b15d` | `0x69b15c` | 1 |
| 9 | `0x69b15f` | `0x69b15c` | 3 |
| 10 | `0x69b166` | `0x69b162` | 4 |
| 11 | `0x69b16c` | `0x69b16a` | 2 |
| 12 | `0x69b16d` | `0x69b16a` | 3 |
| 13 | `0x69b16e` | `0x69b16a` | 4 |
| 14 | `0x69b16f` | `0x69b16a` | 5 |
| 15 | `0x6a92ce` | `0x6a92cd` | 1 |
| 16 | `0x6a92d0` | `0x6a92cd` | 3 |
| 17 | `0x6a92d2` | `0x6a92d1` | 1 |
| 18 | `0x6a92d4` | `0x6a92d3` | 1 |
| 19 | `0x6a92d6` | `0x6a92d5` | 1 |
| 20 | `0x6a92d8` | `0x6a92d7` | 1 |
| 21 | `0x6a92da` | `0x6a92d9` | 1 |
| 22 | `0x6a92dc` | `0x6a92db` | 1 |
| 23 | `0x6a92de` | `0x6a92dd` | 1 |
| 24 | `0x6a92e4` | `0x6a92e3` | 1 |
| 25 | `0x6a92e5` | `0x6a92e3` | 2 |
| 26 | `0x6adbe1` | `0x6adbe0` | 1 |
| 27 | `0x6adbe4` | `0x6adbe3` | 1 |
| 28 | `0x6b0249` | `0x6b0248` | 1 |
| 29 | `0x6dfe1a` | `0x6dfe19` | 1 |
| 30 | `0x6dfe42` | `0x6dfe41` | 1 |
| 31 | `0x6dfee6` | `0x6dfee5` | 1 |
| 32 | `0x6dfee7` | `0x6dfee5` | 2 |
| 33 | `0x6dfee9` | `0x6dfee8` | 1 |
| 34 | `0x6dfef6` | `0x6dfef5` | 1 |
| 35 | `0x6dfef7` | `0x6dfef5` | 2 |
| 36 | `0x6dfefe` | `0x6dfefd` | 1 |
| 37 | `0x6dfeff` | `0x6dfefd` | 2 |
| 38 | `0x6dff59` | `0x6dff58` | 1 |
| 39 | `0x708d56` | `0x708d55` | 1 |
| 40 | `0x708d59` | `0x708d58` | 1 |
| 41 | `0x708d5a` | `0x708d58` | 2 |
| 42 | `0x708d5c` | `0x708d58` | 4 |
| 43 | `0x708d5e` | `0x708d58` | 6 |
| 44 | `0x708d60` | `0x708d5f` | 1 |
| 45 | `0x708d61` | `0x708d5f` | 2 |
| 46 | `0x71f296` | `0x71f294` | 2 |
| 47 | `0x71f298` | `0x71f294` | 4 |
| 48 | `0x71f29a` | `0x71f294` | 6 |
| 49 | `0x71f29c` | `0x71f294` | 8 |
| 50 | `0x71f2c6` | `0x71f2c5` | 1 |
| 51 | `0x71f2ca` | `0x71f2c9` | 1 |
| 52 | `0x71f2e2` | `0x71f2e1` | 1 |
| 53 | `0x71f32a` | `0x71f329` | 1 |
| 54 | `0x71f32e` | `0x71f32d` | 1 |
| 55 | `0x71f33e` | `0x71f33d` | 1 |
| 56 | `0x71f77d` | `0x71f77c` | 1 |
| 57 | `0x71f78c` | `0x71f78a` | 2 |
| 58 | `0x71f78e` | `0x71f78a` | 4 |
| 59 | `0x71f790` | `0x71f78a` | 6 |
| 60 | `0x71f792` | `0x71f78a` | 8 |
| 61 | `0x71f98a` | `0x71f988` | 2 |
| 62 | `0x71f98c` | `0x71f988` | 4 |
| 63 | `0x71f98e` | `0x71f988` | 6 |
| 64 | `0x71f990` | `0x71f988` | 8 |
| 65 | `0x71f9e1` | `0x71f9e0` | 1 |
| 66 | `0x71f9e5` | `0x71f9e4` | 1 |
| 67 | `0x728e0d` | `0x728e0c` | 1 |
| 68 | `0x728e10` | `0x728e0c` | 4 |
| 69 | `0x728e16` | `0x728e15` | 1 |
| 70 | `0x7291b2` | `0x7291b1` | 1 |
| 71 | `0x792af7` | `0x792af5` | 2 |
| 72 | `0x792af9` | `0x792af5` | 4 |
| 73 | `0x792afb` | `0x792af5` | 6 |
| 74 | `0x792afd` | `0x792af5` | 8 |
| 75 | `0x792bcf` | `0x792bcd` | 2 |
| 76 | `0x792bd1` | `0x792bcd` | 4 |
| 77 | `0x792bd3` | `0x792bcd` | 6 |
| 78 | `0x792bd5` | `0x792bcd` | 8 |
| 79 | `0x79f029` | `0x79f028` | 1 |
| 80 | `0x79f02a` | `0x79f028` | 2 |
| 81 | `0x79f02c` | `0x79f02b` | 1 |
| 82 | `0x7b0085` | `0x7b0084` | 1 |
| 83 | `0x7c5eeb` | `0x7c5eea` | 1 |
| 84 | `0x7c5eec` | `0x7c5eea` | 2 |
| 85 | `0x7c8fd6` | `0x7c8fd5` | 1 |
| 86 | `0x7c90e2` | `0x7c90e1` | 1 |
| 87 | `0x7c91ae` | `0x7c91ad` | 1 |
| 88 | `0x7c91c2` | `0x7c91c1` | 1 |
| 89 | `0x7cbef2` | `0x7cbef1` | 1 |
| 90 | `0x7cbf1a` | `0x7cbf19` | 1 |
| 91 | `0x7cefe1` | `0x7cefe0` | 1 |
| 92 | `0x7cf064` | `0x7cf063` | 1 |
| 93 | `0x7cf0bb` | `0x7cf0ba` | 1 |
| 94 | `0x7cf0d2` | `0x7cf0d1` | 1 |
| 95 | `0x7cf0e6` | `0x7cf0e5` | 1 |
| 96 | `0x7cf0f8` | `0x7cf0f7` | 1 |
| 97 | `0x7cf10c` | `0x7cf10b` | 1 |
| 98 | `0x7cf139` | `0x7cf138` | 1 |
| 99 | `0x7cf196` | `0x7cf195` | 1 |
| 100 | `0x7cf1fd` | `0x7cf1fc` | 1 |
| 101 | `0x7cf215` | `0x7cf214` | 1 |
| 102 | `0x7cf44c` | `0x7cf44b` | 1 |
| 103 | `0x7cf4a5` | `0x7cf4a4` | 1 |
| 104 | `0x7cf4e1` | `0x7cf4e0` | 1 |
| 105 | `0x7cf50a` | `0x7cf509` | 1 |
| 106 | `0x7d7fe7` | `0x7d7fe6` | 1 |
| 107 | `0x7dbc5f` | `0x7dbc5e` | 1 |
| 108 | `0x7dbc7c` | `0x7dbc7b` | 1 |
| 109 | `0x7dbcb7` | `0x7dbcb6` | 1 |
| 110 | `0x7dbcc3` | `0x7dbcc2` | 1 |
| 111 | `0x7dbcc4` | `0x7dbcc2` | 2 |

- 命令与输出原文：

```bash
$ python3 _r136/sub_hy4/hy4_b.py | grep 'B3 delta histogram'
B3 delta histogram= {1: 71, 2: 16, 3: 3, 4: 9, 5: 1, 6: 6, 8: 5}
```

### B4 · 支持还是反对 F24 的 86.19%

- **反对**。我的实测命中 99.992%，未命中仅 0.008%，且这 0.008% 全是指令中间字节而非无字节 → 与「86.19% 盘上无任何字节对应」方向相反。
- 该 86.19% 可能怎么来：**机制未定**。我只测到「用 objdump 的指令起始集合，命中 99.992%」这一事实；未测另一种反汇编器（如 Capstone 切法）、未测按字节值读取比对、未测任何 86.19% 的生成脚本。我能实测证实的是：若把 86.19% 解释为「相对某个更稀疏的起始集合的未命中率」，我的 +4 错位反控只能得到 62.99% 未命中（见 B5b），仍不到 86.19%；其他机制（如把某类 `.text` 外地址、或过滤条件后的集合当分母）未测。**我只证方向相反，不编机制。**

### B5 · 反控（两组）

- 预期：①砍掉指令起始集合后半段（只留 <0x600000）后重算命中率应大幅下降；②bounds +4 后命中率应大幅下降。
- 我的实测值：
  - **①按卡面「只保留地址 <0x600000 的」对 bounds 做子集筛选后，命中率未降：bounds<0x600000 共 720,950 条，命中 720,943 条（99.999029%）**。原因：bounds 本身覆盖整个 .text（0x401000–0x7e038c），砍掉集合后半段而只筛 bounds 前半段，前半段仍全在前半指令集合里，**此反控设计在本数据上无判别力，未达「大幅下降」预期，如实报告**。补做等价但有效的反控③：把参照集合整体错位（bounds+k 再查集合），k=+1 命中 26.06%、+2 43.28%、**+4 命中 37.01%（下降 62.98 个百分点）**、+8 38.43%；证明命中确实依赖「地址恰为指令起点」，非任何集合都能命中。
  - **②bounds 整体 +4：命中 515,409/1,392,592（37.010768%），较原 99.992% 大幅下降 62.98 个百分点，符合预期** —— 命中不是因为地址密集。
- 命令与输出原文：

```bash
$ python3 _r136/sub_hy4/hy4_b.py | grep '^B5'
B5a cut<0x600000 n= 720950 hit= 720943 pct=99.999029
B5b +4 n= 1392592 hit= 515409 pct=37.010768
# 补测（错位）：
shift +1 hit=362887 pct=26.058386
shift +2 hit=602722 pct=43.280588
shift +4 hit=515409 pct=37.010768
shift +8 hit=535180 pct=38.430495
```

### B6 · 边界：F24 剔除 bounds 还有没有别的依据

- 读 F24 正文（V532，FACT_INDEX.tsv 第 25 行）除 86.19% 外的措辞，剔除依据还有一条**独立成立的语义判据**：
  - 「按本项口径**『记“地址里是什么字节/值”且可回原址复核』**，`bounds` 不满足该『且』故剔除，`calls` 保留」；
  - 「单列地址且无法回原址（`a2_sites` 的 `bounds`）剔除；两列以上且能回原址复核（`calls`/`imm`/`abs`/`e8`）计入 —— **判据是「有没有可回原址复核的第二列」，不是「含不含地址」**」。
- 我的复核：`bounds` 的元素形态是**单列十六进制地址字符串**（`d["bounds"]` 为 1,392,592 个 8 位 hex 串，如 `'00401000'`），确实不含第二列「该地址的字节/值」；而 `calls` 是 dict 映射（地址↔地址关系，有第二列）。所以「单列地址、记的是『哪里是起始』而非『地址里是什么字节/值』」这一条**不依赖 86.19% 就已成立**。
- **裁定措辞：F24 剔除 bounds 的结论可能仍成立（语义判据独立成立），但「86.19% 盘上无任何字节对应」这一句证据是错的 —— 实测 99.992% 的 bounds 地址恰是 objdump 指令起始，盘上有对应字节。** 不能据此一棍子打死整个剔除决定。

---

## 裁定

### 1. 对 deepseek 回件：**采信**

- 依据：A1（4,417 / 737,517,286 独立复算一致）、A2（64/1/4,352 三桶一致，且 5 件清单外反控证明 rel 相对 `lead/`）、A3（唯一 diff 件四项判据支持「清单裁剪逻辑体量而非损坏」）、A4（30 件随机抽样在 snap2 第 3 列 30/30 命中）、A5（627 件 13,233,082 B、差 16,711,118 B 三项闭合）、A6（三项未跑均不翻其现盘存活率主结论）。
- 保留：A3 中 `calls` 序列化长 913,228 与清单 913,237 的 9 B 残差来源**未测**；deepseek 未覆盖 B 类地址语义复核，但那不属于它回件任务范围。

### 2. 对「86.19% 盘上无任何字节对应」这一条：**驳回**

- 依据：B1（objdump 指令起始 1,392,516 个）、B2（bounds 命中 1,392,481/1,392,592 = 99.992029%，未命中仅 111 条）、B3（111 条未命中全部 Δ≤8 字节，属更长指令中间字节，非无字节）、B5b（+4 错位降至 37.01%，反证原命中非地址密集所致）、B5a（砍半反控在本数据上无判别力，已如实标注）。该句证据方向错误。
- 边界：按 B6，剔除 bounds 的**语义判据（单列地址、无可回原址第二列）独立成立**，故**剔除结论本身可能仍成立，但所引的 86.19% 这句证据是错的**。此句不应继续作为引用的量化依据；若要保留剔除决定，应改写为基于「只记起始地址、不含可复核字节/值」的语义口径。

---

## 临时文件清理

```bash
$ rm -f /tmp/hy4_objd.txt /tmp/hy4_objd.err /tmp/hy4_*.pyc && echo cleaned
cleaned
```
