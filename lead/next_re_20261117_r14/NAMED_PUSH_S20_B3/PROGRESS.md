# NAMED_PUSH_S20_B3 — PROGRESS

批次 S20 B3（S20 named=True 升序第 37..54，池内仅 37、38 两行）。每核完一行即追加。

- [x] 建目录、写 REPORT 骨架、材料自校验（SHA-256 逐字一致）、筛选命令落盘（`_work/filter_b3.py`）。候选 2 行。
- [x] **第 37 行 `0075F8B0 WaveClass::slot54`**：①PASS ②PASS ③FAIL ④PASS ⇒ **不成立**。EVIDENCE 已落盘。
  - ③ 败因：唯一 -1 判定的被调 vt slot30=`0075F890` 恒返 `mov eax,3;ret`（失败路不可达）；其余为 {0,1} 布尔/清零模板，无 ③b。
  - ②④ 均 PASS（② 主虚表槽0=`00410260` RTTI `.?AVWaveClass@@`；④ 锚 `0075EA3F` 构造器 0075E950、非 atexit、行外）。
- [x] **第 38 行 `00763200 WaveClass::slot8`**：①PASS ②PASS ③PASS ④PASS ⇒ **成立 [已证]**。EVIDENCE 已落盘，已进 `delta.tsv`。
  - ③b②：容器 0xA8EC38 FindItemIndex（vt[4]=004EAFD0 `or eax,-1`/`ret 4` 可伪证），`cmp eax,-1`/`je` 真分支 + 计数减一 + 前移压缩数组非栈写 `mov [ecx+eax*4-4],edx` + `jl` 回边。
  - ②：主虚表槽0=`00410260` RTTI `.?AVWaveClass@@`，槽#8=本 entry。
  - ④：锚 `0075EA3F` 构造器 0075E950、非 atexit、行外；本行体内 00763206 自装表落在析构器内按 ㉓ 排除。
- [x] 收尾：`delta.tsv`（1 行）、`base_rate.tsv`（1/2=0.5000）、`REPORT.md` 全表落盘。

**合计**：核 2 行；②成立 2；③b成立 1；④成立 2；四环齐全 1；rate 0.5000。
