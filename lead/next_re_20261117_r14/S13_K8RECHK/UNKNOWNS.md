# S13-K8RECHK UNKNOWNS

诚实登记的未决/不确定项（不影响 11/7 主结论）：

1. **absolute vptr 写点枚举的完整度**：本卡用 C7 05 `[abs],imm` 指令边界扫描（capstone 线性反汇编 .text）捕获 global vptr 写点；对 `mov [reg],imm` 的寄存器写（实例/栈对象）另行登记。理论上若某 global 经 `mov reg,OFFSET g; mov [reg],vt` 两段式装入，则绝对写扫描会漏。本批 18 行的 global 写点全部命中 C7 05 形态（与 S10/S13-K12 已入账实证一致），未发现两段式；但未能证明全 exe 范围内绝无两段式。

2. **DamageGroup 两行无 global 写**：0048AFD0/0048B020 的 vt（7E5144/7E5170）在当前 .text 内只有栈局部/self 写（`[esp+0x38]` / `[esi]`），未发现任何 global 绝对写或 atexit 注册。本卡按「未触发 ㉓ ⇒ 可辩护」处理；若 Lead 采更严格口径「活 vptr 必须是某个 global 的终态值」，则这两行应转不可辩护（可辩护数 11→9、delta 9 行）。此口径分歧记入 DISAGREE.md。

3. **atexit push 配对窗口**：s3 的 atexit 注册配对用 14 条指令回看窗，捕获 0x438552 push 0x438590→0x438586 call 0x7C978A 等全部 7 对。理论上极远 push/call 间隔会漏配，但本批 7 对均在窗内且有独立反汇编佐证。

4. **随机基线 424242 seed 的 1/600 命中**：该 1 次命中是 0x5AD610 = DynamicVectorClass\<double\> 真 deleting dtor（审计 VERDICT §4 A 已点名），是真阳性非误报；本卡 baseline 用 full4 复算得同一结论（seed 424242 1/150）。
