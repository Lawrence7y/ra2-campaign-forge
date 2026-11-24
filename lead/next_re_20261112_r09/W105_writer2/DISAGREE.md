# W105 DISAGREE

1. 我预期（脚本首版标签）：0x47EAC4/0x47EACF 的 `head←[this+0x30]` 不比较 this，是无条件整链替换候选。实测：全函数复核发现 `0x47EAB9: cmp eax,esi; jne`（head==this）在前，链中有遍历摘除补丁 ⇒ 该预期错，已按实测修正（WRITE_SITES §3.1）。
2. W99 的清单（esp/ebp 栈偏移 0xE4 当 CellClass 字段）与 Lead 转述一致为假阳性，本次 C 类 229 条计数印证；除此之外与既有结论无冲突。
