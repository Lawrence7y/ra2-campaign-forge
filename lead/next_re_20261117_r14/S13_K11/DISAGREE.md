# S13-K11 DISAGREE

1. 卡面 grade 口径 vs D-39：卡面要求“照实给 [已证]”，同时要求首行注明“Lead 未裁前不得并入 grade，只并入名字与语义”。本卡执行为：delta 第 5 列照实填 [已证]，并在 PROGRESS 首行/每行缺环说明标注 D-39 约束；若合并员按 D-39 把本批全部压回 [静态推断]，本卡无异议（这不是本卡证据不足，而是 policy 裁决）。
2. 0048AE90 的 ④ 形式：卡面举例为 C7 05 <global>,<vt>，但该行只有栈/this 级 vptr 写（无全局 C7 05，raw-masked 全 .text 0 命中）。本卡按“活 vptr 安装点”的广义形式报（与 a-S13-K10 VERDICT §5 对 5 行 DamageGroup 的处理一致），不谎称有全局安装；如审计坚持字面形式，该行 ④ 可判缺环。
3. 内部纠错（⑨）：初稿 CORE_NUMBERS.md ①表 COL 列误把 vt-4 这个地址当成 COL 结构地址（例：0040B820 写 0x7E17E8，真值 dword[vt-4]=0x7FA708），已在交付前复核改正；COL 列现为 dword[vt-4] 的实际值。其余数字（类名/名串 VA/vt/slot/安装点/direct call/冲突）自洽。
4. 类名 PAU 处理：0048AE90 RTTI .?AV?$VectorClass@PAUDamageGroup@@@@、0054EA10 .?AV?$VectorClass@PAUKamikazeControl@@@@，按硬约束 1 解为 DamageGroup / KamikazeControl（无 U 前缀）；若审计认为应写 struct 标签，可写 DamageGroup/KamikazeControl，但不得写 UDamageGroup / UKamikazeControl。
