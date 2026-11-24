# S10-K9 UNKNOWNS
- 卡面 named_L=511/526 与当前 coverage.tsv name 列复算 513/526 不符（PANEL.md 亦记 M10 后 513）。本卡按“统计 grade 只读第 5 列”的派卡口径，grade 基线 107/526 精确匹配；named 数仅在模拟结算中按当前盘面附记，未用于停机或改账。
- +0x6C4 在本卡称 mission-state dword，不冒充 RTTI/YRpp 官方字段名；其语义来自 0051D6F0 自身写入与多处 27..30 枚举比较，足以闭合行为结论，但不主张确切源码标识符。
- 0051D6F0 的某些状态值（如 0x21、0x27）超出 YRpp Mission 枚举 0..31；本卡不把它们命名为 Mission 成员，只按字节-level state value 描述。
- 0051D0D0、0051AA40 也出现 27..30 分支和自身字段写，但调用者实参链较宽/未逐参闭合，本卡失败关闭，未交付。
- 00522510/00522CB0 是独立的 mission-state 谓词（27..30 与 11..15/20/21/34..36），不在 S10 atlas 可计集合，未作为 delta 行，只作旁证。
- 005F5E80 使用 0xB0C110 运行期段键，文件 raw 不可读；未找到静态 INI 键串，故未升。
- 所有 vftable 槽号只用于定位 entry 和解析被调目标；没有行以 Class::slotN / vslotN / sub_ 作为语义名。
