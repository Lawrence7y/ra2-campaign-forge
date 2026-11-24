# S16-N1 DISAGREE

| # | 项 | 判定 |
|---|---|---|
| D1 | 首轮复算误用逗号分 TSV 得 named=90 | 自检错误，已更正为 tab 分列 → named=73/proved=46，与 CARD/PANEL 一致；记入自检不记为盘上冲突。 |
| D2 | YRpp 名 `PrintMessage` vs 审计认证名 `AnnounceActive` (0053AE00/0053B410) | 按 CARD 强制复用审计名；YRpp 别名仅作通道 B 旁证，未改审计结论。 |
| D3 | YRpp class `Ion` vs coverage 旧名 `LightningStorm::...` | YRpp SuperClass.h 中 `Ion::HasDeferment`/`Ion::Start` 与 `LightningStorm::Start` 混用；按源码逐地址绑定取 `Ion::HasDeferment`(53A0E0)，3 条 reused 不动。 |
| D4 | `TimerStruct::Pause` 无显式地址绑定 | 不声称 [已证]，保持 [静态推断]；若审计要求显式绑定，N5 可退回并本卡实交 7 行（仍高于门槛差 1 的临界）。 |
| D5 | 与 S16-K2/K3 结论差异 | 前卡称 7 条 `Class::sub_` 不可定；本卡用**异源 YRpp 地址绑定**新通道给出 4 条真名 + 1 条契约唯一名，不与前卡通道同源，不构成对前卡审计的否证。 |
