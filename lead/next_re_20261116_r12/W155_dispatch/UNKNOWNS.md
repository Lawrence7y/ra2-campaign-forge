# W155 UNKNOWNS.md

| # | 未知项 | 等级 | 为什么未知 / 下一条最有区分力的证据 |
|---|---|---|---|
| U1 | 11 路阶梯 `0x55B8F0` 是否在运行时通过自修改代码/外部注入到达 | [未证] | 静态双通道（E8 扫描 + dword 指针 + Ghidra refs）均 0；本卡禁止真机/活进程验证。区分证据：活进程在 `0x55B8F0` 下断点 + 查调用栈（但本轮未授权）。 |
| U2 | 候选 B 中两个未命名数组 `0x8B40CC/0x8B40D8` 与 `0xA83E00/0xA83E04/0xA83E10` 的元素类型 | [未证] | `instance_arrays.tsv` 49 行未收录；只从代码布局确认是 DynamicVector（items+0xC=count）。区分证据：查 RTTI/COL 或 `vtables_canonical.json` 中对应 vtable，或读写这些 Count 的构造器。 |
| U3 | `BulletClass::AI` 第 2 个回边（0x467879..0x4678F6）是否算"真循环" | [静态推断] | 字节/Ghidra 都确认它存在；语义是 `call [edx+0x1C8]` 后与 `[0x89DE70]*2` 比较的小回环，不是数组遍历。区分证据：Ghidra 反编译该段看是否 while/状态机（本卡未单独反编译这段）。 |
| U4 | W151 所称 0.65 ms/发 的真实成本来源（绘制/blit？） | [未证] | 本卡只复核更新代码结构；未查 `Draw`/blit 路径。区分证据：对 `0x468090`(`BulletClass::Draw`) 做同样的 callee/循环分析，并和真机帧时间对照。 |
| U5 | 深度≤4 闭包里 15 个引用数组 Count 的函数是否全为内联 Add/Remove（无遍历） | [静态推断] | 只抽查了 depth=1 的 `0x421EA0`（回边=0）；其余 14 个未逐个语义审。区分证据：对 15 个函数逐个跑 `W155Branches` 回边 + 反编译。 |
| U6 | `0x55AFB0` 在 Ghidra 的符号名 / 所属类 | [未证] | Ghidra 显示 `FUN_0055afb0`（无名）；二进制无 RTTI 符号。区分证据：查 `vtables_canonical.json` 是否有槽指向它（dword 扫描 0 命中 ⇒ 大概率非虚函数）。 |
