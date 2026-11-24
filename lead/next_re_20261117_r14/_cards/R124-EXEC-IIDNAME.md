# R124-EXEC-IIDNAME — 独立复算：gamemd.exe 的 IID 到接口名，只用二进制字节

## 目标

对 gamemd.exe 做一处独立测量，产出你自己的数字。主会话已有结论，**不要抄**，只做你自己的实现并报告数字。允许并鼓励你与主会话数字不同 —— 不同才是有效的交叉检验。

## 材料

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  - 期望 sha256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- ImageBase 0x400000。节表自己从 PE 头读，不要硬编码。
- 工具：python3 + pefile + capstone（已装，不许 pip install）
- 只读参考（当线索，不作证据）：
  - out/reverse/symbols.json（988 个类的 RTTI 派生结果，含 vtable_va）
  - _r110/r110a_iidmap.json（172 个 QueryInterface 类的 slot0 与它比较的 IID 指针）

## 要做的事

### A. RTTI 基类数组解码

对 symbols.json 里每个带 vtable 的类：

1. COL = u32(vtable_va - 4) —— MSVC x86 CompleteObjectLocator
2. CHD = u32(COL + 16) —— ClassHierarchyDescriptor
3. NumBaseClasses = u32(CHD + 8)，pBaseClassArray = u32(CHD + 12)
4. 每个 BaseClassDescriptor 是 **24 字节**：pTypeDescriptor(+0) / NumContainedBases(+4) / mdisp(+8) / pdisp(+12) / vdisp(+16) / attributes(+20)
5. 接口/类名 = CString(u32(BCD) + 8)

请注意：**TypeDescriptor 与 BaseClassDescriptor 在 .data 段，不在 .rdata**. COL/CHD/BaseClassArray 在 .rdata. 用错段守卫会让整个解码塌成 0 个。

报告：成功解码多少类、失败多少、（NumContainedBases, mdisp, pdisp, vdisp, attributes）分别的分布。

### B. 用 NumContainedBases 证明继承链

对携带 .?AUIPersistStream@@ 的类，给出这些接口名的 NumContainedBases 值：
IUnknown / IPersist / IPersistStream / IRTTITypeInfo / IClassFactory

报告各自的值与你对「谁继承谁」的结论。

### C. IID 字节与 GUID 文本

对 _r110/r110a_iidmap.json 里出现过的**每一个** IID 指针，读它 16 字节，按 GUID 文本格式化（前 8 字节小端三段，后 8 字节原样）。

报告 IID 指针个数、每个指针的 GUID 文本。

### D. 接口方法的 vtable 槽数（用 COL 组边界）

一个 vtable 的槽数 = 从 vtable_va 起，到**下一个 COL 指针出现在槽位上**为止的槽数。
即：对 k = 0,1,2,...，若 u32(vtable_va + 4*k) 落在 .rdata 且该地址处的 24 字节像 COL（u32(COL+12) 指向一个以 .?A 开头的名字）且 u32(COL+16) 指向 .rdata，则槽位到此结束。

报告：
1. 全部 988 类的槽数分布
2. .?AUIUnknown@@ 的 NumContainedBases=0，那 IUnknown 的方法数（vtable 槽数）实测是多少
3. IClassFactory 相关的 78 个类：它们的 vtable 槽数分布（这些类的基类数组是 [自身, IClassFactory, IUnknown]，所以槽数就是 IClassFactory 的方法数）
4. IRTTITypeInfo 位于 mdisp=4 的独立子对象，它的子 vtable 槽数是多少

### E. 0x7f7c70 与 0x7f7c80 能不能静态区分

这两个 IID 常量（0x7f7c70 = {0000010C-...}、0x7f7c80 = {00000109-...}）谁对应 IPersist、谁对应 IPersistStream？

对下面四种判据**各自**报告能不能区分，并给出数字：

1. **类集合**：比较 0x7f7c70 的类集合与 0x7f7c80 的类集合是否相同
2. **成员偏移**：如果按「类集合包含关系」把 IPersistStream / IPersist 的名字映射过去，两者的 mdisp 各是多少，是否不同
3. **RTTI 基类数组里的先后**：90 个类里，IPersistStream 是否恒定排在 IPersist 前面
4. **QueryInterface 里的比较先后**：对每个类，从 slot0 函数体里按「mov ecx,4 / mov edi,IMM / ... / repe cmpsd」抽取被比较的 IID 立即数**顺序**，然后看 0x7f7c70 与 0x7f7c80 谁先被比。特别注意 HouseClass 与 HouseTypeClass 这两个类。

结论必须写成「能区分」或「不能区分」，并说明是哪一条数据支撑。

## 输出（只写自己的目录）

/home/t628/projects/ra2-campaign-forge/_r124/exec/

- q1.json 到 q5.json，分别对应 A、B、C、D、E 五问
- q.py：可重跑的脚本
- REPORT.md：上面五问的结论与你实测的每个数字

## 纪律

- **不许**修改 lead/ 下任何文件、out/、_r110/；只写 _r124/exec/
- 数字必须实测，**不许预估**。取不到就写「未取得」
- 不许对整段 .text 开 detail=True 一次性 disasm（会 OOM）；用 disasm_lite 或分块
- 所有后台命令带 timeout
