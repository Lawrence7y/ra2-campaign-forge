# 写边界更正（立即生效）

你（WP-B′ 执行方）在复跑探针时把输出**写回了只读的既有目录**，已记录：

- lead/re_loadbench_diff_20261110/_ld_diff_out.txt (+ .json)
- lead/re_map_preset_decode_20261110/_md_parse_out.txt
- lead/re_orphan_owners_20261110/_oo_map_out.txt (8832B)
- lead/re_orphan_owners_20261110/_oo_disasm_out.txt (73,899,177B)
- lead/re_crashwriter_static_20261110/_cw_disasm_out.txt (13117B)
- lead/playerctrl_semantics_20261111/_ps_disasm_out.txt (65202B)
- lead/slot2_fullscan_20261111/_sf_scan_out.txt (158502B)

这违反了「除写域外一律只读」。事实影响：这 7 处被重跑覆盖，但**与原件同尺寸/内容一致**（我已在调度侧比对：5 个同尺寸、1 个仅差末尾空行），因此**原结论未失真**，但「原件 vs 复现件」的对照价值已损失。

## 从现在起

1. **只准写** lead/re_chain_synthesis_20261111/。任何探针重跑，输出必须重定向到该目录（例如 `> 写域/_repro_xxx.txt`），**不得**写回探针原目录。
2. 报告里必须新增一节「越界写入事故登记与影响评估」，如实写清上述 7 处、以及「同尺寸/同内容」的比对结论。
3. 复现门的判据改为：用**写域内**的 _repro_*.txt 与既有 _out 对拍；若既有件已被本轮覆盖，则改为「与我自己上一轮记录的原尺寸/原 sha 对拍」，并明确标注原件已被覆盖这一事实。
4. 仍然禁止：改台账、改 PENDING_DECISIONS、git commit/push、启动游戏。
