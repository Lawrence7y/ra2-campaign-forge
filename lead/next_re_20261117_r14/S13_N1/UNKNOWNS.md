# S13-N1 UNKNOWNS

- 剩余 24 条残行均只有单源弱证据或缺类/源契约，按纪律不命名；逐行理由见 PROGRESS.md 与 EVIDENCE/function_bodies.txt。
- 标量删除析构：有界扫描 0 真阳性；首轮无界扫描曾把 00487E88/0077321A 的尾段误归 00487C70/00487C80/00773030，已按入口到首个 ret/jmp 闭合后剔除。未列入 delta。
- 镜像内 INI/EVA 键串：26 条残行的有界函数体内 0 条；见 EVIDENCE/residual_strings.tsv（表头后无行）。
- 工具错误原文：`capstone.CsError: Information irrelevant for 'data' instruction in SKIPDATA mode (CS_ERR_SKIPDATA)`；在 work/re_lib.py 中 try/except i.operands 跳过 skipdata 伪指令后消失。
- 0065B1E0 的既有别名 `RadSiteClass::noinit_t` 与本次 `RadSiteClass::RadSiteClass()` 同案，按地址检索未发现不同语义冲突。
