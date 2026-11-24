# S10-K13 UNKNOWNS
- 外部并发在 06:29:37+08 重写 COVERAGE/coverage.tsv 的表头为逗号、数据行仍为 tab；本卡脚本统一把首行逗号改 tab 后按第 5 列统计，未改共享文件。最终基线以 06:32:17 读盘为准。
- 006FB010 具有 StartReloading 外部已证调用与自身 +0x2FC 写，但 push 2 的枚举语义无本批外证据，故未交付；不是验证为假，是环①不足。
- 004D85D0 中 +0x55C/+0x5E0/+0x6B0/+0x6B2 等只作字节偏移描述，未冒充 YRpp 官方字段名；0x89F688 只称 8 项子格偏移表，未命名字段。
- 004D7330 的 0x32 常量未命名为 DamageState 成员；名字仅覆盖已证的 damage-result 包装与子对象事件缓存。
- 004D85D0 的 0x70F6A0/0x70F670/0x56BC50 等被调在盘面非 [已证]，未计入环④；只用了 TryGetCellAt/RandomRanged。
- 外部已证被调中个别行可能带 conflict 历史；本卡按派卡口径只读第 5 列 grade，不据卡面推断。
