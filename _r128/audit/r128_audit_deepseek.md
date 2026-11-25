# R128 第二张审计卡 · deepseek 家族独立审计

审计员：deepseek（work/cn:deepseek-v4.1-flash），角色 auditor。
只按字节复算，不引用他人结论。产物仅本文件与 _r128/audit/ 下的复算脚本/原始输出。

## 0. 环境核验

目标文件 sha256（自算）：

    73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476  ra2bench/gamemd.exe

与卡面要求一致。段表（pefile 读取，ImageBase 0x400000）：

    .text     VA 0x401000  VSize 0x3df38d  raw 0x1000   SizeOfRawData 0x3e0000
    .rdata    VA 0x7e1000  VSize 0x30074   raw 0x3e1000 SizeOfRawData 0x31000
    .data     VA 0x812000  VSize 0x367be4  raw 0x412000 SizeOfRawData 0x6c000
    .rsrc     VA 0xb7a000  VSize 0x18128   raw 0x47e000
    .detour   VA 0xb93000  VSize 0x2718    raw 0x497000

.data 原始字节覆盖 VA 0x812000..0x87e000（0x812000 + 0x6c000），虚拟尺寸延到 0x812000 + 0x367be4 = 0xb79be4，即 0x87e000 之后确为 BSS。与卡面段表描述一致。

内存红线执行情况：全文扫描只用 cs_disasm_lite（md.disasm_lite），未使用 md.detail=True，未对整段调用 md.disasm()；所有脚本按 va 片段流式取字节，单次进程 RSS 未超数百 MB；全部在 timeout 下运行，跑完已确认无本审计残留 python 进程（ps 只剩系统自带 t628_stats / nas-hub / harness / ddl 常驻进程）。

---

## A. 0x87f7e8 的全局单例类型

### A.1 实测原始数字

一、存在性核查（三种独立手段，结论一致）

原始字节模式（全文件，非仅 .text）：

    模式 c7 05 e8 f7 87 00  ->  命中 1 处
      file_off 0xd1b2  VA 0x40d1b2  后续 immediate 字段 = 0x7e1964
      指令字节：c7 05 e8 f7 87 00 64 19 7e 00
      16 进制文本：c705e8f7870064197e00

即 mov dword ptr [0x87f7e8], imm32 形态：仅 1 处，地址 0x40d1b2，立即数 0x7e1964。

排除其它写法的穷举（针对紧跟的 4 字节 imm32 e8 f7 87 00，统计其前一字节）：

    prev 0xb9 (mov ecx, imm32)  3693 处
    prev 0x68 (push imm32)         3 处
    prev 0x15 (mov edx, [abs])     2 处
    prev 0x05 (mov [abs], imm32)   1 处   <- 即 0x40d1b2
    prev 0x02 (c7 02 ...)          1 处   <- 即 0x4293b2
    a3 形式(mov moffs32,eax)        0 处
    89 05 / 89 0d / 89 15 / 891d / 8935 / 893d / ff 05 / ff 0d 形式   0 处

对 .text 做重同步线性扫描（capstone 解码失败则进 1 字节，共 66 个重同步点，解码 1394120 条指令），操作数含 0x87f7e8 的全部指令 3700 条，按形态分类：

    3693  mov ecx, 0x87f7e8
       3  push 0x87f7e8                    （0x429339, 0x429346, 0x6bd940）
       2  mov edx, dword ptr [0x87f7e8]    （0x429331, 0x6933a4）
       1  mov dword ptr [0x87f7e8], 0x7e1964   （0x40d1b2）
       1  mov dword ptr [edx], 0x87f7e8     （0x4293b2，写的是外部 out 指针，不是写该全局本身）

所以对该全局的写入型引用只有 0x40d1b2 一条。

二、BSS 归属

    rd(0x87f7e8, 4) 返回空字节串（off 0x1f7e8 >= SizeOfRawData 0x6c000）
    所在段：.data

三、该写入点的上下文（0x40d190..0x40d1d6，正向反汇编）

    40d190  mov ecx, 0x87f7e8
    40d195  call 0x5bda40
    40d19a  push 0x40d1b0
    40d19f  call 0x7c978a
    40d1a4  pop ecx
    40d1a5  ret
    40d1b0  push esi
    40d1b1  push edi
    40d1b2  mov dword ptr [0x87f7e8], 0x7e1964
    40d1bc  mov dword ptr [0x884d00], 0x7e195c
    40d1c6  mov esi, 0x884b84
    40d1cb  mov edi, 4
    40d1d0  sub esi, 0xf94
    40d1d6  push 0x40d260

四、以 0x7e1964 为 vtable 地址解 MSVC x86 32 位 RTTI

vtable 处原始字节（0x7e1964 起 32 字节）：

    40 42 4f 00 30 d2 40 00 40 d2 40 00 d0 56 56 00
    90 d2 40 00 30 df 5b 00 b0 42 4f 00 50 df 5b 00

vfptr 前 4 字节（0x7e1960）= 0x7fab38，即 CompleteObjectLocator。

    0x7fab38 (COL) 原始字节：00 00 00 00  00 00 00 00  00 00 00 00  90 6c 81 00  28 ab 7f 00
      +0  signature      = 0
      +4  offset         = 0
      +8  cdOffset       = 0
      +12 pTypeDescriptor = 0x816c90
      +16 pClassDescriptor= 0x7fab28

    0x816c90 (TypeDescriptor) 原始字节：94 95 7f 00 | 00 00 00 00 | 2e 3f 41 56 4d 6f 75 73 65 43 6c 61 73 73 40 40 00
      vftable ptr = 0x7f9594
      spare       = 0
      name        = 2e 3f 41 56 4d 6f 75 73 65 43 6c 61 73 73 40 40 -> ".?AVMouseClass@@"

    0x7fab28 (ClassHierarchyDescriptor) 原始字节：00 00 00 00 01 00 00 00 0c 00 00 00 f0 aa 7f 00
      +4  attributes = 0x1（CHD_MULTINHERITANCE）
      +8  numBaseClasses = 12
      +12 pBaseClassArray = 0x7faaf0

BaseClassArray（0x7faaf0，12 项，每项为 dword 指针指向 BaseClassDescriptor）：

    d8 aa 7f 00 | c0 aa 7f 00 | a8 aa 7f 00 | 90 aa 7f 00 | 78 aa 7f 00 | 60 aa 7f 00
    48 aa 7f 00 | 30 aa 7f 00 | 18 aa 7f 00 | 00 aa 7f 00 | e8 a9 7f 00 | d0 a9 7f 00

逐项 BCD 解码（BCD 布局 +0 pTD, +4 ncb, +8 mdisp, +12 pdisp, +16 vdisp, +20 attributes）：

    idx  BCD        TD         类名                   ncb  mdisp   pdisp  vdisp  attr
     0   0x7faad8   0x816c90   .?AVMouseClass@@        11     0      -1      0     0x0
     1   0x7faac0   0x816c70   .?AVScrollClass@@       10     0      -1      0     0x0
     2   0x7faaa8   0x816c58   .?AVTabClass@@           9     0      -1      0     0x0
     3   0x7faa90   0x816c38   .?AVSidebarClass@@       7     0      -1      0     0x0
     4   0x7faa78   0x816c18   .?AVPowerClass@@         6     0      -1      0     0x0
     5   0x7faa60   0x816bf8   .?AVRadarClass@@         5     0      -1      0     0x0
     6   0x7faa48   0x816bd8   .?AVDisplayClass@@       4     0      -1      0     0x0
     7   0x7faa30   0x816bc0   .?AVMapClass@@           3     0      -1      0     0x0
     8   0x7faa18   0x816ba0   .?AVGScreenClass@@       2     0      -1      0     0x0
     9   0x7faa00   0x816b88   .?AUIGameMap@@           1     0      -1      0     0x0
    10   0x7fa9e8   0x816b70   .?AUIUnknown@@           0     0      -1      0     0x0
    11   0x7fa9d0   0x816b50   .?AVINoticeSink@@        0  21784(0x5518)  -1  0  0x9

第 11 项 attr=0x9 且 mdisp=0x5518 非零，是虚基类项（BCD_IVB|BCD_MI），对应第二个 COL 0x7fa9b8 的 offset 字段 = 0x5518（该 COL 指向同一 TD 0x816c90，其 vtable 为 0x7e195c）。

类名（demangle）：.?AVMouseClass@@ -> MouseClass。

五、slot0

    0x7e1964 dword = 0x4f4240
    （后续 slot1=0x40d230, slot2=0x40d240, slot3=0x5656d0, slot4=0x40d290, slot5=0x5bdf30, slot6=0x4f42b0, slot7=0x5bdf50）

### A.2 与卡面主张是否一致

一致。

- 卡面「地址 0x87f7e8 在 .data 的 BSS 区」：成立，VA 0x87f7e8 > 0x87e000（raw 末端），静态读回空。
- 卡面「mov dword ptr [0x87f7e8], imm32」：存在，唯一 1 处，0x40d1b2，imm=0x7e1964。
- 卡面 RTTI 解析路径（COL 前 4 字节、COL+12 是 TD、TD+8 是类名、COL+16 是 CHD、CHD+8 基类数、CHD+12 BCA）在此二进制上逐字段成立，偏移全部对上。
- 卡面「一个全局单例」定性成立：写点位于 0x40d190 的构造函数 + atexit 注册序列（call 0x5bda40 构造、push 0x40d1b0 / call 0x7c978a 注册析构）内，且 0x42933e 处与 0x6933b1 处（call dword ptr [edx+0x48]）都按 vfptr 调用，都是以 0x87f7e8 为对象地址、[0x87f7e8] 为 vtable 指针。

### A.3 判定

PASS

---

## B. 0x7ea6e8 的 IID 格式化

### B.1 实测原始数字

    0x7ea6e8  bytes: c7 2e f0 96 e8 6f d1 11 b6 fd 00 a0 24 dd af d1
              Data1(LE u32)=0x96F02EC7  Data2(LE u16)=0x6FE8  Data3(LE u16)=0x11D1
              Data4 = B6 FD 00 A0 24 DD AF D1
              -> {96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}

    0x7e36c0  bytes: c3 2e f0 96 e8 6f d1 11 b6 fd 00 a0 24 dd af d1
              Data1=0x96F02EC3  Data2=0x6FE8  Data3=0x11D1
              -> {96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}

    0x7f7c90  bytes: 00 00 00 00 00 00 00 00 c0 00 00 00 00 00 00 46
              Data1=0x00000000  Data2=0x0000  Data3=0x0000
              -> {00000000-0000-0000-C000-000000000046}

Data1 比较：

    0x7ea6e8  0x96F02EC7
    0x7e36c0  0x96F02EC3
    0x7f7c90  0x00000000

三者 Data1 互不相同。0x7ea6e8 与 0x7e36c0 仅 Data1 低字节差 4（C7 vs C3），Data2/Data3/Data4 12 字节完全相同。

### B.2 与卡面主张是否一致

一致。卡面按 Data1(4B LE)-Data2(2B LE)-Data3(2B LE)-Data4[0..1]-Data4[2..7] 的格式要求可无歧义执行；三者 Data1 不同。

附带记录（不作主张）：0x7f7c90 的取值即标准 IID_IUnknown {00000000-0000-0000-C000-000000000046}。

### B.3 判定

PASS

---

## C. 0x7ea6e8 的全部比较点

### C.1 实测原始数字

全文件原始字节穷举（模式 e8 a6 7e 00，即 LE 立即数 0x7ea6e8）——全文件仅 3 处，全部落在 .text，且全部是 bf 形式（mov edi, imm32）：

    file_off 0x29310   VA 0x42930f   bf e8 a6 7e 00
    file_off 0x293a6   VA 0x4293a5   bf e8 a6 7e 00
    file_off 0xf4274   VA 0x4f4273   bf e8 a6 7e 00

.data / .rdata / .rsrc / .detour 中无同模式命中，即无任何数据区指针指向 0x7ea6e8。

重同步线性扫描（66 个重同步点，解码 1394120 条指令）确认操作数文本含 0x7ea6e8 的指令共 3 条，与原始字节穷举一一对应。

逐条 32 字节窗口（从该指令起，含指令自身）：

站点一 0x42930f

    窗口 32B：bf e8 a6 7e 00 8b f5 33 d2 f3 a7 75 37 b9 e8 f7 87 00 85 c9 75 0c 5f 5e 5d b8 0e 00 07 80 5b c2
    0x42930f  bf e8a67e00   mov edi, 0x7ea6e8
    0x429314  8b f5         mov esi, ebp
    0x429316  33 d2         xor edx, edx
    0x429318  f3 a7         repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x42931a  75 37         jne 0x429353
    f3 a7 在该指令之后第 9 字节（绝对地址 0x429318），窗口内成立，中间隔 2 条指令（不是紧邻的下一条）。

站点二 0x4293a5

    窗口 32B：bf e8 a6 7e 00 33 c0 f3 a7 75 0c 5f 5e c7 02 e8 f7 87 00 5b c2 0c 00 5f 5e b8 02 40 00 80 5b c2
    0x4293a5  bf e8a67e00   mov edi, 0x7ea6e8
    0x4293aa  33 c0         xor eax, eax
    0x4293ac  f3 a7         repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4293ae  75 0c         jne 0x4293bc
    f3 a7 在之后第 7 字节（0x4293ac），窗口内成立，中间隔 1 条指令。

站点三 0x4f4273

    窗口 32B：bf e8 a6 7e 00 33 c0 f3 a7 74 0a 5f b8 02 40 00 80 5e c2 0c 00 8b 44 24 0c 89 02 50 8b 08 ff 51
    0x4f4273  bf e8a67e00   mov edi, 0x7ea6e8
    0x4f4278  33 c0         xor eax, eax
    0x4f427a  f3 a7         repe cmpsd dword ptr [esi], dword ptr es:[edi]
    0x4f427c  74 0a         je 0x4f4288
    f3 a7 在之后第 7 字节（0x4f427a），窗口内成立，中间隔 1 条指令。

补充上下文（站点三所在函数，从函数头 0x4f4240 正向解码是干净的，非错位产物）：

    4f4240  mov edx, dword ptr [esp + 0xc]
    4f4244  push esi
    4f4245  test edx, edx
    4f4247  push edi
    4f4248  jne 0x4f4254
    4f4254  mov eax, dword ptr [esp + 0x10]
    4f4259  mov ecx, 4
    4f425e  mov edi, 0x7f7c90
    4f4267  repe cmpsd dword ptr [esi], dword ptr es:[edi]
    4f4273  mov edi, 0x7ea6e8
    4f427a  repe cmpsd dword ptr [esi], dword ptr es:[edi]

### C.2 与卡面主张是否一致

（1）「全部比较点」= 3 处：0x42930f、0x4293a5、0x4f4273。前两处在卡面 D/E 覆盖的 0x429270 / 0x429360 体内，第三处 0x4f4273 在 0x4f4240 起的一个独立的 12 字节栈参数 QI 体内（ret 0xc），且 0x4f4240 正是主张 A 里 MouseClass vtable 的 slot0 —— 与主张 A 的 slot0 数字互相印证。

（2）每条「后面是否紧接着 repe cmpsd」：三条都成立（f3 a7 分别在 +9 / +7 / +7 字节，都在 32 字节窗口内）；但若把「紧接着」理解为「紧邻的下一条指令」，则三条都不成立（中间各有 2 / 1 / 1 条指令）。两种读法我都给出原始字节，按卡面「从该指令起正向反汇编 32 字节」的判定口径，三条均成立。

（3）方法学差异（重要，见第 6 节分歧一节）：本仓若按最省事的写法 md.disasm(text, 0x401000) 迭代 Capstone，单遍扫描会在 0x46f59d 停住（只解码 155215 条，覆盖不到 .text 后半），此时只能找到 2 处，会漏掉 0x4f4273。必须对解码失败点重同步（进 1 字节继续）才能得到完整 3 处。

### C.3 判定

PASS（3 处全部列出，逐条 f3 a7 成立；但「全部」这一结论只在重同步扫描口径下成立，单遍 disasm_lite 会漏 1 处）

---

## D. 函数 0x429270 的转交点

### D.1 实测原始数字

从 0x429270 起正向反汇编 0xf0 字节（0x429270..0x42935f，函数尾 c2 10 00 at 0x429359，其后 4 字节 90 填充）：

call dword ptr [reg] 形态：共 2 条

    编号  地址       指令文本               reg   该 reg 之前最后一次赋值
    1     0x4292f1   call dword ptr [edx]   edx   0x4292e4  mov edx, dword ptr [0x89a29c]
                                                  -> 绝对地址 0x89a29c
    2     0x42933e   call dword ptr [edx]   edx   0x429331  mov edx, dword ptr [0x87f7e8]
                                                  -> 绝对地址 0x87f7e8

两处的指令字节：ff 12（两条都是 ff 12）。

reg 赋值轨迹核对（证明「最后一次」判定正确）：

    edx 的写入点（窗口内全部）：
      0x4292b2  xor edx, edx
      0x4292c9  xor edx, edx
      0x4292e4  mov edx, dword ptr [0x89a29c]   <- 先于 0x4292f1
      0x429316  xor edx, edx
      0x429331  mov edx, dword ptr [0x87f7e8]   <- 先于 0x42933e
    0x4292f1 与 0x42933e 之间无其它 edx 写入落在其前，判定成立。

该函数中所有 push 立即数形态的指令（共 4 条，push reg 形态另 8 条不计）：

    0x4292ec  68 9c a2 89 00   push 0x89a29c
    0x4292f9  68 9c a2 89 00   push 0x89a29c
    0x429339  68 e8 f7 87 00   push 0x87f7e8
    0x429346  68 e8 f7 87 00   push 0x87f7e8

（另有非间接 call：0x4292fe call 0x7c8b3d、0x42934b call 0x7c8b3d，属 release/辅助调用，不计入 call dword ptr [reg]。）

函数内两条 QI 分支的完整形态（原始字节，供复算）：

    分支一（对 0x89a29c 单例）
      4292cf  b9 9c a2 89 00        mov ecx, 0x89a29c
      4292d4  85 c9                 test ecx, ecx
      4292d6  75 0c                 jne 0x4292e4
      4292d8  5f 5e 5d b8 0e000780 5b c21000   （返回 0x8007000e）
      4292e4  8b 15 9c a2 89 00     mov edx, dword ptr [0x89a29c]
      4292ea  50                    push eax
      4292eb  55                    push ebp
      4292ec  68 9c a2 89 00        push 0x89a29c
      4292f1  ff 12                 call dword ptr [edx]
    分支二（对 0x87f7e8 单例）
      42931c  b9 e8 f7 87 00        mov ecx, 0x87f7e8
      429321  85 c9                 test ecx, ecx
      429323  75 0c                 jne 0x429331
      429331  8b 15 e8 f7 87 00     mov edx, dword ptr [0x87f7e8]
      429337  50                    push eax
      429338  55                    push ebp
      429339  68 e8 f7 87 00        push 0x87f7e8
      42933e  ff 12                 call dword ptr [edx]

旁证：0x89a29c 在 0x429200 被写入 0x7e36d4；以 0x7e36d4 为 vtable 解 RTTI：COL=0x7fbc18，TD=0x8186c8，类名 ".?AVApplicationClass@@"，CHD numBaseClasses=3，slot0=0x429360（即卡面主张 E 的函数）。0x429360 与 0x429270 因此是同一批 QI 家族里两个相邻单例的分派体。

### D.2 与卡面主张是否一致

一致。call dword ptr [reg] 共 2 条，reg 都是 edx，都来自 mov edx, dword ptr [绝对地址] 形态，绝对地址分别是 0x89a29c 与 0x87f7e8。push 立即数共 4 条，立即数为 0x89a29c（两次）与 0x87f7e8（两次）。卡面问「若来自 mov reg, dword ptr [绝对地址] 则报该绝对地址」，两处都命中该情形，已给出。

### D.3 判定

PASS

---

## E. 0x429360 的 QI 体比较常量

### E.1 实测原始数字

从 0x429360 起正向反汇编 0x90 字节（0x429360..0x4293ef）：

mov edi, 绝对地址 指令，按出现顺序：

    序  地址      指令文本            指令字节
    1   0x42937f  mov edi, 0x7e36c0   bf c0 36 7e 00
    2   0x429391  mov edi, 0x7f7c90   bf 90 7c 7f 00
    3   0x4293a5  mov edi, 0x7ea6e8   bf e8 a6 7e 00

函数体内对 dword ptr [edx] 的写指令（窗口内把 [edx] 作为目的操作数的全部指令，共 2 条；另有 0x429369 test edx,edx、0x429398 等为读，不计）：

    地址      指令                              源操作数            指令字节
    0x4293b2  mov dword ptr [edx], 0x87f7e8     立即数 0x87f7e8     c7 02 e8 f7 87 00
    0x4293cb  mov dword ptr [edx], eax          寄存器 eax         89 02

（说明：0x4293cb 的 eax 在 0x4293c7 由 mov eax, dword ptr [esp + 0x10] 装入，即第 2 个栈参数传入的接口指针；0x4293b2 写入的是 0x87f7e8 这个地址常量本身，即把全局单例的地址作为接口指针交给调用方。）

函数内 edx 的来源与三条比较的分派结构（原始字节）：

    429360  8b 54 24 0c      mov edx, dword ptr [esp + 0xc]     <- 第 1 个栈参数 = 承接接口的 out 指针
    429367  85 d2            test edx, edx
    429369  75 0b            jne 0x429376
    42936d  b8 03 40 00 80   mov eax, 0x80004003                 <- E_POINTER
    42937a  b9 04 00 00 00   mov ecx, 4
    42937f  bf c0 36 7e 00   mov edi, 0x7e36c0
    429384  8b f0            mov esi, eax
    429386  33 db            xor ebx, ebx
    429388  f3 a7            repe cmpsd
    42938a  74 3b            je 0x4293c7
    42938c  b9 04 00 00 00   mov ecx, 4
    429391  bf 90 7c 7f 00   mov edi, 0x7f7c90
    429396  8b f0            mov esi, eax
    42939a  f3 a7            repe cmpsd
    42939c  74 29            je 0x4293c7
    42939e  8b f0            mov esi, eax
    4293a0  b9 04 00 00 00   mov ecx, 4
    4293a5  bf e8 a6 7e 00   mov edi, 0x7ea6e8
    4293aa  33 c0            xor eax, eax
    4293ac  f3 a7            repe cmpsd
    4293ae  75 0c            jne 0x4293bc
    4293b0  5f 5e            pop edi / pop esi
    4293b2  c7 02 e8 f7 87 00  mov dword ptr [edx], 0x87f7e8
    4293b8  5b               pop ebx
    4293b9  c2 0c 00         ret 0xc
    4293bc  5f 5e            pop edi / pop esi
    4293be  b8 02 40 00 80   mov eax, 0x80004002                 <- E_NOINTERFACE
    4293c3  5b               pop ebx
    4293c4  c2 0c 00         ret 0xc
    4293c7  8b 44 24 10      mov eax, dword ptr [esp + 0x10]
    4293cb  89 02            mov dword ptr [edx], eax
    4293cd  50               push eax
    4293ce  8b 08            mov ecx, dword ptr [eax]
    4293d0  ff 51 04         call dword ptr [ecx + 4]
    4293d8  c2 0c 00         ret 0xc

### E.2 与卡面主张是否一致

一致。mov edi 绝对地址共 3 条，顺序与卡面要求一致输出为 0x7e36c0 -> 0x7f7c90 -> 0x7ea6e8；对 [edx] 的写指令 2 条，源操作数分别为立即数 0x87f7e8（0x4293b2）与寄存器 eax（0x4293cb）。

### E.3 判定

PASS

---

## 6. 分歧与需要主会话裁决的方法学问题

### 6.1 单遍 disasm_lite 会静默截断 .text（影响主张 C 的「全部」）

实测：list(md.disasm_lite(T, 0x401000)) 单遍迭代在本二进制上于 VA 0x46f59d 停住，解码 155215 条，覆盖到 0x46f59d 为止，未抛出异常、不报错。截断点附近字节为编译器内联数据（大量 04 04 … 与一张 dword 跳转/查表），Capstone 在那里把后续字节解成 add ecx, dword ptr [ebp - 0x1b3affb7]，长度跨过若干表项后与后续指令流对不齐，此后 disasm_lite 返回空即终止。

后果：只做单遍扫描时，0x7ea6e8 只能报出 2 处（0x42930f、0x4293a5），漏掉 0x4f4273；0x87f7e8 只能报出 498 条引用，而非完整 3700 条。本审计改用「解码失败进 1 字节重同步」的扫描（66 个重同步点，1394120 条指令），并用全文件原始字节模式穷举交叉校验（0x7ea6e8 全文件仅 3 处，0x87f7e8 的写入型编码全文件仅 1 处），两条路径结论一致。

建议：后续卡面写「全 .text 扫描」时，明确要求重同步扫描或原始字节模式穷举做交叉校验，否则「全部」类结论会系统性少报。此点不是卡面主张被推翻，而是卡面所述手段与被核目标之间有缺口。

### 6.2 主张 C「紧接着」的口径

字面「紧接着」= 紧邻下一条指令，则三处都不成立（中间各有 2/1/1 条）。按卡面「从该指令起正向反汇编 32 字节」的窗口口径，三处都成立。我按窗口口径判 PASS，同时给出精确偏移（+9 / +7 / +7）供裁决。若主会话的口径是「紧邻」，则主张 C 应改判为不成立。

### 6.3 声明本审计的边界

- 全部结论来自静态字节与 RTTI 结构，未运行 gamemd.exe，未验证运行期对象布局（例如 MouseClass 实例大小、0x87f7e8 单例的实际初始化时机）。
- 主张 A 的「基类数 12」是 CHD numBaseClasses 字段值；其中第 0 项就是自身（. ?AVMouseClass@@），严格说「全部基类」含自身重复项，我按 CHD 原样报出，未去重。
- 0x7f7c90 被 0x7ea6e8 的比较体一同引用（0x429243、0x4292c2、0x429391、0x41027d、0x773a50、0x6cf463 等 147 处），本审计只按卡面要求报格式与 Data1 异同，未对其使用面展开定论。

---

## 7. 复算产物（可重跑）

    _r128/audit/deepseek_scan.py          重同步 disasm_lite 扫描器（参数为要搜的绝对地址）
    _r128/audit/deepseek_ab.py            主张 A / B 的 RTTI 与 GUID 复算
    _r128/audit/deepseek_verify.py        五条主张的统一复算脚本
    _r128/audit/deepseek_quick.py         主张 C / D 的定点核验
    _r128/audit/_deepseek_ab.txt          A / B 原始输出
    _r128/audit/_deepseek_scan_87f7e8.txt 0x87f7e8 的 3700 条引用清单
    _r128/audit/_deepseek_refs.txt        引用形态分类

五条主张的判定汇总（只列判定，不写评语）：

    A  PASS
    B  PASS
    C  PASS（口径敏感，见 6.2；单遍扫描口径下会漏 1 处，见 6.1）
    D  PASS
    E  PASS
