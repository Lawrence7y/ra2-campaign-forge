# -*- coding: utf-8 -*-
"""_oc_binding.py : bind the object under review.

Object = the 20 orchestrator claim lines given verbatim in the task's CLAIMS
list. We hardcode those 20 strings (copied from the ask), join with newline,
and hash UTF-8 bytes with hashlib. No path computation, no regex, no I/O
outside stdout. Read-only with respect to all existing artifacts.
"""
import hashlib, json

CLAIMS = [
"1. 「台账三件在 PENDING:92,105,129」→ 实际 **4 行**（:92 d30 / :105 d29 / :117 d28 / :129 d27），我漏了 d28。",
"2. 「四件在两件台账里共 3 行」→ 实际 4 行，且第四件的 PASS 不在台账在交付件 REFSYNC_SCOPE_FIX.md:251/252/253。",
"3. 「indep_wrong_prob = 0.0」→ 口径错置，用 fp_rate 相乘；正确 q_i=fn_i/39 ⇒ q_r10×q_n13 = 3.75%。",
"4. 「3.75% 是三层连乘」→ 实际是两层（q_r10×q_n13）；三层连乘是 3.3632%。",
"5. 「风险放大 2.05 倍是后验口径」→ 2.05 是**似然**口径；后验是 1.8772/2.0727 倍；4.4474 是类别错误。",
"6. 「GP-A1 从 PASS→CATCH」→ 74 版实际 chain=PASS（漏判）；PASS→CATCH 是 DG 内存 Shim 的设计实验。",
"7. 「c07_slot 里 R10 多报的是真断言」→ 实际全是新误报（标题/表头/清单/条件式）。",
"8. 「门禁四条问题」→ 实际 2 条（我串了 n4 域的四条 FAIL）。",
"9. 「三层共用同一套字面词表」→ 模块级常量不共用；共用的是运行时输入契约（55/74 行 tokens 相同）。",
"10. 「r10×n13 高一致」→ 实际一致率 51.35%，φ=0.0293、MI=0.00062 bit。",
"11. 「n4_yi_final 是门禁挑错中稿」→ 该域候选有 startswith 过滤，唯一候选；挑错文件不成立。",
"12. 「十个域仍报问题、5 个域 bindings=0」→ 实际 13 域 / 6 域。",
"13. 「最小硬项 4 件」→ 前提错；严格交集 2 件、全量载体口径 6 件。",
"14. 「:22 同时逐字含两个 needle」→ 只含 N2（pos=172），不含 N1（find=-1）。",
"15. 「SELF_TEST=FAIL 是脚本缺陷」→ 我跑的是非登记口径（单 needle）；登记口径是双 needle，且双 needle PASS 属掩蔽效应。",
"16. 「按生成器式 any() 筛同族」→ 漏 check_d28（`:96-97` 先绑布尔列表再 any(present)）。",
"17. 「h5 的 H5 修好就能插生产门禁」→ 修好后仍有 4 项缺陷，不能插。",
"18. 「18 条增益可归因算法改进」→ 可归因算法 = 0 分；18 分是「实现替换」（in-sample）。",
"19. 「族级/全单元 = 32768 倍」→ 编排方心算成 16384，实际 32768（它是对的）。",
"20. 「ρ̄ < 0.8599」→ 编排方反解错，实际 ρ̄ < 0.14013（它是对的）。",
]

text = "\n".join(CLAIMS)
raw = text.encode("utf-8")
print(json.dumps({
    "object": "20 条编排方数字主张（任务书 CLAIMS 列表逐字）",
    "n_lines": len(CLAIMS),
    "bytes": len(raw),
    "sha256": hashlib.sha256(raw).hexdigest(),
}, ensure_ascii=False, indent=2))
