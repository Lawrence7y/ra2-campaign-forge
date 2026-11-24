R91 执行卡 · gamemd.exe 对象模型安装侧普查（只读，禁写 live 树）

目标：为 vt == [esi] 补「安装侧」独立证据，回答一个问题：
      偏移 0 处的 dword 是否确为 vtable 指针（而非普通数据）。

必须做的机械统计（全部只读 ra2bench/gamemd.exe 字节）：
1) 全库统计 mov 形式把某 vtable 地址写入内存偏移 0 的站点数，
   指令形态为 mov $0x<vtable>,0(%reg) 或 movl $0x<vtable>,0x0(%reg)。
   同时统计写入偏移 4 / 0x14 / 0x30 的同类站点数作对照。
2) 对第 1 步得到的每个目标 vtable 地址，检查它是否属于 vtable 全集。
   vtable 判据（必须原样使用，不得自创）：
   - 该地址 V 在 .rdata 内
   - dword[V-4] 是 COL：COL 在 .rdata 内且 dword[COL+0]==0 且
     dword[COL+0xC] 指向 TD（TD 在 .data 内且 dword[TD]==0x7F9594 且 TD+8 起以 .?A 开头）
   - dword[V] 是 .text 内的地址
3) 统计同时被写入偏移 0（vtable）与偏移 0x30、偏移 0x14 的对象站点，
   给出交集数目。这是判断「同一结构既有 vptr 又有 +0x30 链与 +0x14 标志」的依据。

工具：可用 python3 + capstone + pefile，也可用 i686-w64-mingw32-objdump。
注意 objdump 默认输出 AT&T 语法（mov 0x4(%esi),%eax 形态），不要按 Intel 语法解析。
反汇编起始集用 objdump 的地址行，不要用 capstone 从头线性扫
（本库已实测 capstone 线性扫只解出 155215 条，objdump 有 1392516 条，差 9 倍）。

产物目录：_r91/_exec/  （只允许写这个目录）
禁止：复制 live 树任何目录、禁止写 _r91/_exec 之外任何路径、禁止修改 gamemd.exe。
产出上限 20 MB。

自测要求：至少 8 项断言，必须带正控与反控各一条，打印每项 PASS/FAIL。
最终把结论写 _r91/_exec/REPORT.md，逐条给数字，不写形容词。
