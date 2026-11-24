# S10-K8 DISAGREE
| # | 对象 | 本卡处置 | 依据 |
|---|---|---|---|
| D1 | K6 原判“零字段写 004DFA70 入选、有字段写三行被弃” | 不同意原判；按统一判据抓回 004DFB70/004DFCB0/004DFE00。 | 三行均有单 id、自带字段写、[v+0x1E8]、[v+0x480]、ret 1；同族反向剔除自相矛盾。 |
| D2 | K7 称 006B6FA0“未映射/无 RTTI 类名” | 不同意该语义；改为 [已证] ctor。 | 写完整 4-vptr 组→COL 00809AE8→TD 00840120 `.?AVSpawnManagerClass@@`；call 004101C0、成员初始化同 006B6EA0、ret 4。 |
| D3 | K7 把 006B6FA0 仅因无 caller 拒绝 | 不同意；接受为死代码 ctor。 | 类锚 + 角色锚已独立闭合；caller 是增益通道，不是 ctor 必要条件。 |
| D4 | K7 U1 中 006B7F10 排除 | 同意，不触碰。 | 007F3664=slot5；构造 arg1(ebx) 而非 ecx=this，角色锚失败。 |
| D5 | K7 U5 把 006B8140 名说成盘上现状 | 不同意其措辞。 | 盘上仍 slot/静态名；scalar_deleting_destructor 只在 K5 delta，本卡不重交。 |
| D6 | 004E0E80 归属 | 不裁决；暂留 S10，conflict=1，delta 明写归属待 D-37。 | Lead-2；命名与归属分开处理，不因 D-37 未决删掉 RTTI/ctor 命名证据。 |
| D7 | K6 原 U7 双计风险 | 同意审计从严口径；004DFA70/00521760 退 [静态推断]。 | Lead-1；环②与环④同源，不进入本卡 delta。 |
| D8 | K6 命名把字段偏移写进名字 | 不同意保留为规范名；改名并标 behavioral。 | Lead-3；字段偏移只留在语义栏，名字不声称真方法名。 |

## 纪律自检
- 未写 COVERAGE/、未 git commit、未用 Ghidra、未触碰目标 exe。
- 只写 lead/next_re_20261117_r14/S10_K8/；delta 10 行/9 列，证据路径存在且 entry 唯一。
