# D-17 独立事实核证

日期：2026-11-05。仅静态读取原文和原始 PE；未运行游戏、未读写活进程、未修改被核证文件。

结论：三项不可判边界确实写在 §4.2；测量窗禁截图原文和计数器只读调用链成立。生成戳是搜索入口的工作区代际标记，但须处理回绕、初始化及“尝试次数不等于实际展开次数”的口径。`0x887308/0x88730C` 是 DSurface 对象指针，原报告将其称为视口坐标有误。

## 逐项结果

```json
[
  {
    "supportsOption": "D17-1：三项不可判声明存在；声明存在不等于全部经验性断言已复核",
    "detail": "亲读 lead/re_line_20261105/W2_FRAMETIME_ATTRIB/W2_FRAMETIME_ATTRIB.md:298 的 §4.2 及紧邻正文：302-312 列视口位置/可见单位数不可判，理由是未采坐标、裁剪计数、可见池且测量窗禁截图；314-320 列寻路不可判，理由是未采 GenerationStamp/单位移动状态，CurrentFrame 墙钟帧沿不能分解帧内成本；322-326 列索敌不可判，理由是未采索敌计时器/执行频次，且与寻路在宏观数据中共线。这里的“永远”明确限定于现有产物，不限制新增观测。3831-3841、3986-4001 的实际字段产出仅含帧计数、全局容器计数和进程内存指标，支持这些字段没有微观分解能力。本次没有普查全部 87 窗或 shots 时间线，不能把报告 311 行的“全部 87 窗零 PNG”写成亲验通过；305 行地址定性被第 5 项反证。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D17-2：测量窗禁截图的源码禁令成立",
    "detail": "lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3826-3828 原文：# ★★ 观测扰动禁令（§3.1-②/§4.1）：测量窗内**零键鼠、零 PrintWindow**\n#   （`capture_frame` 属观测扰动，测量窗内禁用）；本节**不向目标进程\n#   注入任何模块/线程** ⇒ S-4 模块面零变化（§5.2）。紧邻 3819-3825 注释规定 RPM 只读扩项、非注入、S-4 后开句柄及默认 measure=0 零执行。此项核实的是源码禁令，不单凭注释证明所有历史运行均遵守。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D17-3：_rpm_counters 的目标进程零写入机制成立",
    "detail": "lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3979-4001 已逐行读：3986-3993 八次 _rpm_u32，3994 一次 _rpm_mem_kb，3995-4001 仅组装本地字典。已进被调函数体核实：3928-3944 的 _rpm_u32 在 3940-3941 调 ReadProcessMemory，将读数写到采样器本地 ctypes buf，核 got 字节数；3960-3976 的 _rpm_mem_kb 在 3972 调 GetProcessMemoryInfo，将结果写到本地 _PMC。3905-3919 的 _rpm_open 仅申请 0x1000|0x0010 = PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ，无 VM_WRITE/VM_OPERATION。3984 的零写入注释与函数实现一致。该结论限定于此函数及这条调用链，不声称整个 harness 无其他行为。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D17-4：每次搜索入口推进代际戳成立；无条件 Δ=实际 Dijkstra 次数不成立",
    "detail": "亲自反汇编 ra2youli/gamemd.exe。0x004CBC2C B9 B8 E8 87 00 将 ECX 设为单例 0x0087E8B8，0x004CBC31 E8 CA 0C F6 FF 调 0x0042C900；其入口 0x0042C90D E8 9E DC FF FF 无条件调用 0x0042A5B0。另一个搜索入口 0x0042D170 在 0x0042D17D E8 2E D4 FF FF 也先调该函数。已进 0x0042A5B0 全函数体：0x0042A5FB 8B 41 28 读 [ecx+0x28]，0x0042A5FE 40 inc eax，0x0042A5FF 89 41 28 写回，故单例字段 VA=0x0087E8E0。0x0042A602 0F 85 80 00 00 00 非零即退出；回绕为零则清访问戳数组，再在 0x0042A683 40、0x0042A685 89 41 28 再增至 1，跳过 0。因此不是无界单调数，也不是每次严格加 1。0x0042D17D 的递增在后续检查之前，0x0042D222 E8 69 F0 FF FF 调检查函数后 0x0042D229 0F 84 23 02 00 00 可分支去失败收口；故计数口径为进入这些搜索/工作区代际初始化的尝试，不能直接等同实际完成的 Dijkstra 展开次数或 CPU 时间。未声称已穷尽所有间接调用与字段写点，采样设计仍须排查初始化/重置与回绕。",
    "provenance": "我亲验"
  },
  {
    "supportsOption": "D17-5：反对把 0x887308/0x88730C 当作视口 X/Y；二者为 DSurface 指针槽",
    "detail": "亲验 ra2youli/gamemd.exe 的读写点及构造体。读：0x004328DE A1 0C 73 88 00 取 [0x88730C]，0x004328E3 8B C8、0x004328E8 8B 11、0x004328EA FF 52 7C 将读数作为 this 指针解引用虚表并调方法；0x00432A35 A1 08 73 88 00 取 [0x887308]，0x00432A3A 8B 40 1C 再读对象 +0x1C。写：0x00534104 E8 97 64 F8 FF 调构造体 0x004BA5A0，0x0053410D A3 0C 73 88 00 将构造结果写入 [0x88730C]，紧接 0x00534112 8B 10、0x00534117 FF 52 18 解引用虚表；0x00560D2D E8 3E 9A F5 FF 调 0x004BA770，0x00560D32 A3 08 73 88 00 写入 [0x887308]。已进两个构造体：0x004BA5D0 C7 06 D4 85 7E 00 与 0x004BA814 C7 06 D4 85 7E 00 均赋 vtable 0x007E85D4；亲读 RTTI：vtable-4 的 COL=0x00800260，TypeDescriptor=0x008205D8，名字字节 '.?AVDSurface@@'。所以不能通过读取这两个 u32 获取视口左上角坐标，W2 报告 305 行及相关转述应更正。实际视口坐标 VA 本次未定位，不能拿表面指针替代。",
    "provenance": "我亲验"
  }
]
```

## 亲跑复核命令与结果

目标：`D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe`，ImageBase=`0x400000`，SHA256=`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。使用 pefile 按 PE RVA 映射取字节，再以 capstone X86/32 反汇编，未执行目标文件。

以下为本次实际执行且成功完成的最后一条集中复核命令（Shell 单引号包装，内部 Python 无外部脚本依赖）：

```bash
python -I -c 'import pefile,capstone,hashlib; p=pefile.PE("D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"); print("SHA256",hashlib.sha256(p.__data__).hexdigest()); m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);
for a,z in [(0x42a5fb,0x42a608),(0x42a67f,0x42a68e),(0x42c909,0x42c912),(0x42d179,0x42d182),(0x4cbc2c,0x4cbc36),(0x4328de,0x432901),(0x432a35,0x432a3d),(0x5340ea,0x53411a),(0x560d2b,0x560d37),(0x6bdca0,0x6bdcb3),(0x4ba7e8,0x4ba850)]:
 for i in m.disasm(p.get_data(a-0x400000,z-a),a): print(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str)
u=lambda va:int.from_bytes(p.get_data(va-0x400000,4),"little"); col=u(0x7e85d0); td=u(col+12); print("VTABLE_RTTI",hex(col),hex(td),p.get_data(td+8-0x400000,100).split(b"\0")[0])'
```

输出关键行（完整相关机器字节亦已列于逐项结果）：

```text
SHA256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
0x42a5fb 8b4128 mov eax, dword ptr [ecx + 0x28]
0x42a5fe 40 inc eax
0x42a5ff 894128 mov dword ptr [ecx + 0x28], eax
0x42a602 0f8580000000 jne 0x42a688
0x42a683 40 inc eax
0x42a685 894128 mov dword ptr [ecx + 0x28], eax
0x42c90d e89edcffff call 0x42a5b0
0x42d17d e82ed4ffff call 0x42a5b0
0x4cbc2c b9b8e88700 mov ecx, 0x87e8b8
0x4cbc31 e8ca0cf6ff call 0x42c900
0x4328de a10c738800 mov eax, dword ptr [0x88730c]
0x4328e8 8b11 mov edx, dword ptr [ecx]
0x4328ea ff527c call dword ptr [edx + 0x7c]
0x432a35 a108738800 mov eax, dword ptr [0x887308]
0x432a3a 8b401c mov eax, dword ptr [eax + 0x1c]
0x534104 e89764f8ff call 0x4ba5a0
0x53410d a30c738800 mov dword ptr [0x88730c], eax
0x560d2d e83e9af5ff call 0x4ba770
0x560d32 a308738800 mov dword ptr [0x887308], eax
0x4ba814 c706d4857e00 mov dword ptr [esi], 0x7e85d4
VTABLE_RTTI 0x800260 0x8205d8 b'.?AVDSurface@@'
```

其他执行情况：读文件与上下文由 Read 完成；初始跨目录 rg 超时，另一次通配路径搜索部分路径不存在；首次 Python 因命令引号错误退出，首次详细交叉引用脚本因 CS_AC_WRITE 导入位置错误退出，修正后的全节 detail 扫描超时后主动停止。上述均未计为通过。随后成功的 PE 定点反汇编、地址字节扫描与最终集中命令提供了本文二进制证据。字节扫描附近未对齐的反汇编行未被用作证据，只采用已对齐的关键指令/函数入口；未声称全体交叉引用已穷尽。未运行 87 窗统计、历史截图全量检查或动态采样测试。
