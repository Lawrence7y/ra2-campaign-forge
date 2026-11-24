# S03-ADJ - BufferIOFileClass +0x29 裁决

> 目标 ra2youli/gamemd.exe，SHA-256 前缀 73201CC0、后缀 F67476；只读。写域仅 S03-ADJ。工具 Python 3.12 + capstone 5.0.7(skipdata=True) + pefile；未用 Ghidra。

## 一句话回答

**不是 15W/9R，也不是 19W/10R；第三个数是 23W/12R（35 个站点）。**

## 结论表

| # | 结论 | 级 | 证据路径 |
|---|---|---|---|
| 1 | 字段宽度：所有计入站点均为 byte(1)；dword 候选均非本类/栈，未计入 | [已证] | SITES.tsv, EVIDENCE/SUMMARY.txt |
| 2 | BufferIO vtable 0x7E3A2C 的 RTTI 链 COL 0x7FBEF8 -> TD+8 .?AVBufferIOFileClass@@；槽12=0x432050 | [已证] | EVIDENCE/RTTI_VTABLES.txt |
| 3 | 0x432050 体内 5 个 +0x29 站点成立：0x432090 R、0x432107/0x43212A/0x432202/0x432225 W | [已证] | SITES.tsv, DIFF_VS_AUDITS.md |
| 4 | 第二 vptr writer 0x431A30 与 3 个 helper 0x431BC0/0x431D90/0x431DD0 属 BufferIO 对象族，贡献 4W/2R | [已证](站点+布局+虚拟调用) / [静态推断](函数名) | SITES.tsv, EVIDENCE/ALL_DISP29_SITES.tsv |
| 5 | 0x65CBC1/0x65CB26 是 RawFileClass 的 +0x14/+0x20 写，不是 BufferIO +0x29 | [已证] | EVIDENCE/CROSSCHECK_AUDIT_CLAIMS.txt |
| 6 | 精确 disp=0x29 的 call/jmp [reg+disp] 虚派发为 0；A 绝对形式亦为 0，且 A 在 0x00-0x60 上 97/97 恒 0，故形式分解不作判据 | [已证] | EVIDENCE/VIRTUAL_DISPATCH_EXCLUSIONS.txt, EVIDENCE/FORM_BASELINE.tsv |
| 7 | 两种独立定界（全 .text linear ret/padding 分区；call/jmp 目标+vtable+vptr CFG 区间）差异 28 站点，逐行已列 | [已证] | EVIDENCE/FUNCTION_BOUNDARIES.tsv, EVIDENCE/BOUNDARY_DIFF_SITES.txt |
| 8 | 纳入站点按类分列：BufferIO 35；其余 62 个 disp29 候选为栈/其他类/未知，fail-closed 排除 | [已证] | SITES.tsv |

## 核心数字与复算

- 23W/12R = 15W/9R 基线 + 槽12 4W/1R + 0x431A30 1W/1R + helpers 3W/1R。
- 35 = 24(基线站点数) + 5(槽12) + 6(第二 writer/helpers)。
- 脚本：work/recompute.py；最细站点表：SITES.tsv；未截断证据：EVIDENCE/。

## 纪律状态

绝对形式恒零基线已测；不据其下结论。站点归属用函数区间包含，不用 entry_at_or_before。未写台账、未改游戏文件、未 git commit。
