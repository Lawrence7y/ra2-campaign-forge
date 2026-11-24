# P0-ADJ4 · UNKNOWNS（如实披露）

1. **判据式 G1b 前驱解码的边界**：`predecessor_kind()` 在 `[va-15,va)` 内找"恰好以 va 结尾"的指令，优先 sweep 起点、回退 resync；本镜像 `[0x401000,0x7E038D)` 内 100 行均有确定前驱（94 nop / 6 ret）。若 `.text` 边界或不可解码前导导致无解，记 `pred_kind=none`，G1b 失败 → NOT_FUNC（保守，fail-closed）。本批未触发。
2. **C2 `jcc-target` 全 .text 扫描**：`jcc_targets` = 79,345 个地址（0x70-0x7f / 0x0f80-0x0f8f / loop 目标）。真函数也可能被 jcc 引用（"跳入尾块"），此时 C2 失败会把真函数误判 NOT_FUNC——全量历史集复算有 39 例 FN（多为 c2=0 或 C5 遇 .byte），见 `work/validate_full.py`。本批 100 行中 4 行 C2 失败（00402F80/00405AB0/004063A0/0040A600），逐一核对均为内部标签/孤儿尾段，判 NOT_FUNC 正确。
3. **C5 自包含窗口 512B**：若函数体内含跳表/嵌入数据（capstone skipdata 出 `.byte`），C5 失败 → NOT_FUNC（保守）。历史集 39 例 FN 中多数属此类。本批 100 行仅 00402F80 命中（首字节即 E8，另多条失败）。
4. **`data` 子类的假阳性**：历史集 P0_RESIDUAL NOT_FUNC 中 10 个 `data`（0x40F220/0x40F270/0x40F2F0/0x40F990/…/0x410100，浮点常数表被当 fld/xor 代码）被本判据误判 FUNC。它们均在 `0x40F220..0x410100`，**落在本批 100 行地址区间 `[004011B0,0040B3E0)` 之外**，不影响本批判定；但在剩余 5,498 行的推广中可能出现，故推广数为"强判据可裁"估计（≈5,361），非全量保证。
5. **subsystem 归属**：coverage_delta.tsv 全部填 `S22`（未定类桶），与 P0_RESIDUAL_2 既有做法一致；这些是 atlas 之外的新入口，无 RTTI 类属证据，按 P0 只裁入口不裁语义的口径不强归具体 Sxx。S22 按 §9.1 不参与任何百分比排名。
6. **语义未证**：coverage_delta.tsv 的 `one_line_semantics` 仅为字节形态的静态推断（`[静态推断]`），未做语义证明（P0 不强求，见 R14-R8）。真名/真语义留 P1。
7. **>90% FUNC 率的诊断结论**：本批 95% 是**真实分布**，非凑数——(c4a|leaf) 形态过滤器系统性漏掉 FPU 叶（首字节 DD/DB）、mov getter（8B 81 / A1）、xor 清零（33）、常量返回（B8）、push ecx（51）等真实叶函数，P0_RESIDUAL_2 已实证遗漏 2,026 个 FPU 叶 + oracle 0x7775C0（首字节 51）。详见 PROGRESS.md §停机核验。
