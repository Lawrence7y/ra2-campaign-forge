# R124-AUDIT-RTTI — 异族复核：R124 的 IID 定名与方法数测量

## 你的角色

你是审计员，不是执行员。**主会话已有结论，你的任务是找它错在哪**。逐条复核下面列出的论断，并给出你自己的独立实测数字。允许你复算后与主会话数字不同 —— 不同正是你要报告的东西。不要重跑主会话的脚本当成复算；写你自己的实现。

## 材料

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  - 期望 sha256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- 主会话产物（只读，当被审对象，**不要改**）：
  - /home/t628/projects/ra2-campaign-forge/_r124/r124a_iid_name.py 与 .json
  - /home/t628/projects/ra2-campaign-forge/_r124/r124b_iface_methods.py 与 .json
  - /home/t628/projects/ra2-campaign-forge/_r124/r124c_iface_boundary.py 与 .json
  - /home/t628/projects/ra2-campaign-forge/_r124/r124d_qi_offset.py 与 .json
  - /home/t628/projects/ra2-campaign-forge/_r124/r124e_method_count.py 与 .json
  - /home/t628/projects/ra2-campaign-forge/_r124/r124f_r110_undercount.py 与 .json
- 参考（当线索，不作证据）：out/reverse/symbols.json、_r110/r110a_iidmap.json

## 要复核的论断（逐条给 成立 / 不成立 / 部分成立）

A1 MSVC x86 BaseClassDescriptor 是 24 字节，字段次序 pTypeDescriptor(+0) / NumContainedBases(+4) / mdisp(+8) / pdisp(+12) / vdisp(+16) / attributes(+20)。用至少 3 个类自己验证字段次序，不要只看偏移断言。

A2 954 个带 vtable 的类，RTTI 基类数组全部可解；且 bases[0] 是该类自身。

A3 NumContainedBases 给出继承链 IUnknown 0 < IPersist 1 < IPersistStream 2。

A4 二进制里 .?AU 开头的名字是 COM 接口，共 26 个。

A5 R110 的 IID 普查漏记：它的窗口判断 a - f < 120 对**每一次** cmpsd 都生效，导致函数体内偏移超过 120 字节的比较被丢掉。HouseClass(slot0=0x4f6830) 实际比较 6 个 GUID（偏移 47/68/99/130/161/182），R110 只记了 3 个。所以 0x7f7c70 与 0x7f7c80 的类集合真值是 77 而不是 R110 的 76。

A6 QueryInterface 模板里，每个被接受的 IID 分支会把 this 指针调整值写入出参（0 或 lea ecx,[reg+OFF] 的 OFF）。这个 OFF 与 RTTI 的 mdisp 是同一布局事实的两次独立记录。用 (类集合包含 + OFF==mdisp) 两条记录，18 个 IID 里能唯一定名 12 个。

A7 定名的 12 个是：0x7e9530=ILinkStream、0x7e9ae0=IRTTITypeInfo、0x7e9b00=IPublicHouse、0x7ea6e8=IUnknown、0x7ea768=IHouse、0x7f7c20=IWOLBrowserEvent、0x7f7c90=IUnknown、0x7f7ca0=IClassFactory、0x7f7cb0=IEnumConnections、0x7f7cc0=IConnectionPoint、0x7f7cd0=IConnectionPointContainer、0x7f7ce0=IEnumConnectionPoints。逐个复算。

A8 剩下 6 个定不了名：0x7e36c0 与 0x7e9b20 的 OFF 解不出；0x7e9b40 / 0x7f7c70 / 0x7f7c80 在两条记录上都与 IPersist/IPersistStream 完全相同（类集合相同、OFF 都是 0、RTTI 顺序恒定）；0x7f7cf0 在 IStream 与 ISequentialStream 之间无法区分。

A9 方法数：接口块占主 vtable 的 slot 0..7（共 8 个），因为 90 个 persist 家族的类里第一个「body 写 vtable 常量」的 slot 恒为 8（49 个类可判，41 个该类短到没有销毁器）。且 slot 0..7 无一写 vtable 常量。

A10 因为 IClassFactory 族（78 个类）vtable 长度恒为 5、且 IClassFactory 的 NumContainedBases=1，所以 IUnknown 方法数 = 5 - 2 = 3。

A11 于是 IPersistStream 方法数 = 8 - 3(IUnknown) - 1(IPersist) = 4。

A12 slot 0 是 QueryInterface、slot 1 与 slot 2 恒 mov eax,1 ; ret 4（AddRef/Release）、slot 7 全族 ret 8。

## 输出（只写自己的目录）

/home/t628/projects/ra2-campaign-forge/_r124/audit/

- AUDIT.md：A1..A12 逐条 成立/不成立/部分成立 + 你的实测数字 + 你判「不成立」时的反例地址
- mine.py：你**自己写**的复核脚本（不许 import 主会话的脚本）
- mine.json：你的数字

## 纪律

- 不许修改 lead/ 下任何文件、out/、_r110/、_r124/ 下主会话的产物；只写 _r124/audit/
- 数字必须实测，不许预估；取不到就写「未取得」
- 不许对整段 .text 开 detail=True 一次性 disasm；用 disasm_lite 或分块
- 所有后台命令带 timeout
- 你若有与主会话不同的数字，**必须**在 AUDIT.md 里单列一节
