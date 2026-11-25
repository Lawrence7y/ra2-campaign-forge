# R135-DS · F29 数字的独立字节复算（只读）

- 角色：R17 子代理 / exec / 家族 deepseek / model work/cn:deepseek-v4.1-flash
- 卡面：_cards/R135-DS-F29BYTES.md
- 被执行文件：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 文件 sha256：73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（4825360 字节）
- PE 基线（自解析，非 pefile）：ImageBase=0x00400000，5 节，raw 与 RVA 在 .text/.rdata/.data 上相等，故这三节内 file_off == RVA

  .text    VA=0x00401000..0x007E1000  raw=0x001000..0x3E1000
  .rdata   VA=0x007E1000..0x00812000  raw=0x3E1000..0x412000
  .data    VA=0x00812000..0x00B79BE4  raw=0x412000..0x47E000
  .rsrc    VA=0x00B7A000..0x00B93000  raw=0x47E000..0x497000
  .detour  VA=0x00B93000..0x00B96000  raw=0x497000..0x49A000

- 分节判据（显式，避免边界歧义）：RVA 落在 [VA, VA+max(VirtualSize, SizeOfRawData)) 即属该节；恰好落在两节边界时归后一节（例如 RVA 0x3E1000 归 .rdata，不归 .text）。上一轮我自己的脚本曾用闭区间上限，把 ADVAPI32 的 FirstThunk=0x3E1000 误判进 .text，已在最终脚本中修正并留作边界正控。
- 全程只读二进制；我自己写的脚本全部在 _r135/sub_deepseek/ 下，没有 import 也没有抄 _r95 / _r109 的任何脚本。

复现命令（全部在 /home/t628/projects/ra2-campaign-forge 下）：

    python3 _r135/sub_deepseek/r135_ds_f29_final.py        > _r135/sub_deepseek/run_final.log
    python3 _r135/sub_deepseek/r135_ds_f29_d2_stub_refs.py > _r135/sub_deepseek/run_d2_stub_refs.log
    python3 _r135/sub_deepseek/r135_ds_f29_extra_63of77.py > _r135/sub_deepseek/run_extra_63of77.log

run_final.log 的 sha256 = 7db7fd77d3e603ae604bf7f854c8b50da555281ce640976e15db01f6b2a4f41d

D1..D5 全部命中主张值，无一处不一致。第 6 节「分歧」写的是「无硬分歧，但有 3 处措辞需收紧」，逐条给出依据。

---

## D1 · 77 张 TClassFactory 表

- 主张值：77（F29 statement 第 1 句；limitations 定义分母 = 类名形如 .?AV?$TClassFactory@VX@@ 的全部表）
- 我实测：77 个不同 X，且每个 X 只出现 1 次
- 结论：一致

我用的正则原文（Python bytes 正则，来自 r135_ds_f29_final.py 第 D1 段）：

    re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+)@@')

实际输出（run_final.log 第 12-21 行）：

    ########## D1 ##########
    正则原文 (Python bytes 正则): \.\?AV\?\$TClassFactory@V([^@]+)@@
    命中次数            = 77
    不同 X 个数         = 77
    每个 X 的出现次数最大值 = 1
    命中点所在节分布    = {'.data': 77}
    名字串 RVA 区间     = 0x440F70 .. 0x441EE0 (VA 0x00840F70..0x00841EE0)
    77 个串尾部 @ 个数分布 = {2: 77}      <- 这是「主正则只吃掉 2 个 @」的统计，见下方第 2 点
    独立交叉核验 1: 子串 b"TClassFactory" 全文件出现 = 77
    独立交叉核验 2: 正则 rb"?AV?\$TClassFactory@V(.+?)@@" 命中 = 77, 不同 = 77

两点必须写清，否则这条会被误引：

1. 「77」是**不同 X 的个数**，同时也是**命中次数**（因为每个 X 只出现 1 次，无重复）。二者相等是实测结果，不是定义套出来的。
2. 名字串真实的尾部是**四个 @**（.?AV?$TClassFactory@VCStreamClass@@@@），我的正则尾部只写了 @@，因为 X 用 [^@]+ 已在第一个 @ 处截断。为确认这不是我漏读，我另写 r135_ds_f29_d1_tailat.py 独立数「X 之后紧跟的 @ 个数」（run_d1_tailat.log）：

       命中 77 ; 不同 X 77
       X 之后紧跟的 @ 个数分布 = {4: 77}
         样例 RVA=0x440F70 全串=b'.?AV?$TClassFactory@VCStreamClass@@@@'

   77 个串全部是 4 个 @。按任意一种尾部口径（2 个 @@ 或 4 个 @@@@），X 的集合与计数都相同，所以 77 这个数字不依赖尾锚的选择。

77 个 X 全表见 run_final.log 第 22-99 行（字典序），节选首尾：

     1 AITriggerTypeClass
     2 AircraftClass
    ...
    76 WaypointPathClass
    77 WeaponTypeClass

---

## D2 · 8 字节桩 B8 01 00 00 00 C2 04 00 的全镜像计数与节分布

- 主张值：全镜像 40 次、全在 .text、0 次在数据节
- 我实测：40 次，.text 40 次，数据节（.rdata/.data/.rsrc/.detour）0 次；另有 PE 尾部 overlay 272 字节内也 0 次
- 结论：一致

实际输出（run_final.log 第 101-106 行）：

    ########## D2 ##########
    被搜索字节序列 = B8 01 00 00 00 C2 04 00
    全文件出现次数 = 40
    按节分布       = {'.text': 40}
    数据节合计(.rdata/.data/.rsrc/.detour) = 0

40 处 VA 全表见 run_final.log 第 107-146 行，首尾为 0x0040D230 … 0x0076F640。

补充核验（同一脚本末行）：

    变体 b"B801000000C20400CC" 出现 = 0

即没有一处桩被 CC 填充紧接，说明 40 处都是函数体末尾而非数据巧合的中间片段（前 1 字节上下文在 run_d2_stub_refs.log 里逐处打印，例如 0x00410300 前 8 字节为 C2 0C 00 90 90 90 90 90，是标准 ret 后的对齐填充）。

对 F29 limitations 里「槽内 14 / 槽外 26」我也做了一次独立口径复算（r135_ds_f29_d2_stub_refs.py，判据 = 桩的 VA 是否作为 dword 出现在数据节）：

    汇总: 有数据节引用 14 处 / 无引用 26 处（合计 40）

有引用的 14 处为 0x40D230/0x40D240 0x410300/0x410310 0x4293E0/0x4293F0 0x4E8240/0x4E8250 0x50E340/0x50E350 0x512740/0x512750 0x6CF4B0/0x6CF4C0，正好 7 对。数字与 F29 一致（该数字不在本卡 D1..D5 要求内，仅作旁证）。

---

## D3 · 0x6C2AC0 与 0x6C51C0 的 17 字节

- 主张值：两处 slot1 目标 17 字节逐字节相同，序列 8B44240483C00450FF15C8117E00C20400
- 我实测：两处 17 字节完全相同，且都等于主张序列；两处 sha256 也相同
- 结论：一致

VA 到文件偏移的换算：两处都在 .text，该节 raw==RVA，故 file_off == VA-0x400000。0x6C2AC0 → 0x2C2AC0；0x6C51C0 → 0x2C51C0。

实际输出（run_final.log 第 149-161 行）：

    ########## D3 ##########
    VA=0x006C2AC0  RVA=0x2C2AC0  file_off=0x2C2AC0  sec=.text
      bytes  : 8B 44 24 04 83 C0 04 50 FF 15 C8 11 7E 00 C2 04 00
      hex    : 8B44240483C00450FF15C8117E00C20400
      sha256 : 998d39e4762612934918f22404655843e46ffc9af4e771b61bb25ee55fcac83d
      == 主张序列: True
    VA=0x006C51C0  RVA=0x2C51C0  file_off=0x2C51C0  sec=.text
      bytes  : 8B 44 24 04 83 C0 04 50 FF 15 C8 11 7E 00 C2 04 00
      hex    : 8B44240483C00450FF15C8117E00C20400
      sha256 : 998d39e4762612934918f22404655843e46ffc9af4e771b61bb25ee55fcac83d
      == 主张序列: True
    两处 17 字节逐字节相同 = True（差异下标 []）
    主张序列 sha256 = 998d39e4762612934918f22404655843e46ffc9af4e771b61bb25ee55fcac83d

对 F29 里「0x6C2AC0 是 .?AV?$TClassFactory@VAircraftTypeClass@@@@ 的 slot1」与「0x7F3D98 的 slot1 = 0x6C51C0」两句，我也用 vtable[-4]→COL→COL+0xC→TD→TD+8 名串链独立走了（r135_ds_f29_d3_vtable_chain.py，输出）：

    该 VA 被 .rdata off=0x3F3B2C 引用 -> 作为 vtable slot1, vtable VA=0x007F3B28, 名字=.?AV?$TClassFactory@VAircraftTypeClass@@@@
    该 VA 被 .rdata off=0x3F3D9C 引用 -> 作为 vtable slot1, vtable VA=0x007F3D98, 名字=.?AV?$TClassFactory@VFactoryClass@@@@

归属与 F29 一致。但「同一份 AddRef 的两份拷贝」这个措辞要收紧，见第 6 节第 2 条：这 17 字节在全镜像出现 **80** 次，不是 2 次。

旁证（run_final.log 第 162-164 行节选）：

    旁证: 该 17 字节序列全镜像出现 80 次, 节分布 {'.text': 80}
    旁证: 0x6BEEC0+0x180*i 等差数列项数 = 77 (i=0..76), 0x6C2AC0 是第 40 项, 0x6C51C0 是第 66 项

即其中 77 处严格构成 0x6BEEC0 + 0x180*i 的等差格点（与 77 张工厂表一一对应），另 3 处在 0x007AC690 / 0x007AC800 / 0x007AD620，同样被 .rdata 以 dword 引用（分别被 0x3F76B8 / 0x3F7670 / 0x3F78E8 引用），只是不属于这 77 张工厂表。

---

## D4 · 0x7E11C8 这个 IAT 槽

- 主张值：KERNEL32.dll 的 InterlockedIncrement，Hint=432，FirstThunk idx=62
- 我实测：属于 KERNEL32.dll、名字 InterlockedIncrement、Hint=432（0x1B0）、KERNEL32 组内 FirstThunk 相对下标=62
- 结论：四项全部一致

实现方式：没有用 pefile 的高层 get_import_table，手工读 DataDirectory[1] → IMAGE_IMPORT_DESCRIPTOR 数组 → 逐条 OriginalFirstThunk(ILT)/FirstThunk(IAT) → 32 位 entry → 走 IMAGE_IMPORT_BY_NAME（WORD Hint + 名字串）。代码见 r135_ds_f29_final.py 的「导入表手工遍历」段。

实际输出（run_final.log 第 202-216 行）：

    ########## D4 ##########
    目标 VA=0x007E11C8 -> RVA=0x3E11C8 -> file_off=0x3E11C8 -> 所在节 .rdata
    作为 IAT 槽被命中 1 条
      DLL            = KERNEL32.dll
      ILT 槽 RVA     = 0x793248 (所在节 .detour)
      IBN RVA        = 0x7941F0 (所在节 .detour)
      IBN 原始字节   = B0 01 49 6E 74 65 72 6C 6F 63 6B 65 64 49 6E 63 72 65
      Hint           = 432 (0x1B0)
      名字           = InterlockedIncrement
      组内下标       = 62   (0x3E11C8-0x3E10D0)/4 = 62 ; 组内共 162 条
      整个 IAT 数组全局下标 = (0x3E11C8-0x3E1000)/4 = 114
      372 条按描述符顺序的 0-based 全表位置 = 63
      该槽磁盘值     = 0x0040F990
    D4 主张映射: DLL=KERNEL32.dll? True ; 名字=InterlockedIncrement? True ; Hint=432? True ; FirstThunk idx=62? True

IBN 原始字节 B0 01 与主张里的「B0 01 49 6E 74…」逐字节一致（B0 01 是小端 Hint=0x01B0=432，随后是 ASCII "InterlockedInc…"）。

独立第三方交叉（i686-w64-mingw32-objdump -p，只用来看它是否吐出同一行，不作为我的主判据）：

    $ i686-w64-mingw32-objdump -p ra2bench/gamemd.exe | grep InterlockedIncrement
        003e11c8  <none>  01b0  InterlockedIncrement

    $ awk '/DLL Name: KERNEL32/{f=1;next} /DLL Name/{f=0} f && ... if($1=="003e11c8")'
    组内第 63 条 idx=62 hint=01b0 name=InterlockedIncrement

objdump 与我的手写遍历在 DLL、Hint、组内下标三点上完全一致。

「FirstThunk idx=62」的口径必须写死，否则会被两种读法拉开：0x7E11C8 相对 KERNEL32 的 FirstThunk 基址 0x3E10D0 是第 62 号（0-based），这就是「FirstThunk idx=62」；若按整个 IAT 数组起点 0x3E1000 算则是 114；若按 372 条导入按描述符顺序的全局序号算则是 63。F29 的 62 只有在「组内相对下标」口径下成立，这一点应与引用同时声明。

---

## D5 · limitations 里的 6 个导入数字

- 主张值：372 总条 = 339 按名 + 33 按序数；ILT 372 条全在 .detour；IAT 371 条在 .rdata、1 条在 .detour（xyr.dll）；另附 339 条按名 IBN 全在 .detour、33 条序数无名字区
- 我实测：全部命中
- 结论：一致

实际输出（run_final.log 第 189-200 行）：

    ########## D5 ##########
    ① 总条数 = 372 ; 按名 = 339 ; 按序数 = 33   (372/339/33)
    ② ILT 条目节分布 = {'.detour': 372}
       ILT RVA 区间 = 0x793148..0x793750
    ③ IAT 槽节分布   = {'.detour': 1, '.rdata': 371}
       非 .rdata 的 IAT 槽: dll=xyr.dll idx=0 IAT_RVA=0x793758 kind=ord 序数=1
       IAT RVA 区间 = 0x3E1000..0x793758 ; .rdata 数组内 0x3E1000..0x3E1600
    ④ 名字区 IBN 条目 339 条, 节分布 = {'.detour': 339}
    ⑤ IAT 槽磁盘值分类 = {'序数标记 0x8xxxxxxx': 33, '.text': 339}
    ⑥ 序数导入按 DLL = {'xyr.dll': 1, 'OLEAUT32.dll': 11, 'WSOCK32.dll': 19, 'DSOUND.dll': 1, 'COMCTL32.dll': 1} 合计 33
    ⑦ 每组条数: {'xyr.dll': 1, 'KERNEL32.dll': 162, 'USER32.dll': 96, 'GDI32.dll': 22, 'ADVAPI32.dll': 9,
       'SHELL32.dll': 1, 'ole32.dll': 15, 'OLEAUT32.dll': 11, 'WINMM.dll': 5, 'WSOCK32.dll': 19,
       'DDRAW.dll': 1, 'DSOUND.dll': 1, 'VERSION.dll': 3, 'COMCTL32.dll': 7, 'IMM32.dll': 6, 'binkw32.dll': 13}
    ⑧ 边界裁决验证: ADVAPI32 FirstThunk=0x3E1000 (RVA) -> VA=0x007E1000, 归节 = .rdata

第 ⑦ 行 16 组条数求和 = 1+162+96+22+9+1+15+11+5+19+1+1+3+7+6+13 = 372，与 ① 自洽。objdump 对 16 个 DLL 的逐组计数与我完全一致（KERNEL32 162 / USER32 96 / GDI32 22 / ADVAPI32 9 / SHELL32 1 / ole32 15 / OLEAUT32 11 / WINMM 5 / WSOCK32 19 / DDRAW 1 / DSOUND 1 / VERSION 3 / COMCTL32 7 / IMM32 6 / binkw32 13 / xyr 1）。

第 ⑧ 行是我特意留的边界正控：ADVAPI32 的 FirstThunk 恰好等于 .rdata 起点 0x3E1000。第一版脚本用闭区间上限，把它同时匹配到 .text（.text 的 VA+rsize 也正好是 0x7E1000）并优先返回 .text，于是 IAT 出现「1 条在 .text」的假结果；改成「取 va 最大的候选节」后归 .rdata，371/1 的分法才站住。这说明 371 这个数字对边界口径是敏感的，引用时应连带声明判据。

---

## 6. 分歧

硬数字上**零分歧**：D1 77、D2 40/40/0、D3 17 字节相同、D4 四要素全中、D5 六个数全中。下面 3 条不是数字打架，是措辞/口径会让后续引用者多算或错算，按严重度排序。

### 6.1 「FirstThunk idx=62」缺口径限定（口径风险，最高）

同一地址 0x7E11C8 有三种合法下标：组内 62、整个 IAT 数组 114、372 条全表序号 63。F29 与 limitations 都只写「FirstThunk idx=62」不说是哪个数组，后续若有人拿 62 去索引 DataDirectory[12] 指向的整体 IAT 数组，会落到 0x7E10F8 而不是 0x7E11C8。

我更相信：62 是 KERNEL32 组内相对其 FirstThunk 基址 0x3E10D0 的下标（(0x3E11C8-0x3E10D0)/4 = 62），这是唯一让 62 成立的口径，objdump 的「组内第 63 条 / idx=62」也印证同一口径。

建议改法：把「FirstThunk idx=62」写成「KERNEL32 组内 FirstThunk 相对下标 62（= 全表 372 条中第 63 条，整个 IAT 数组 0-based 下标 114）」。

### 6.2 「同一份 AddRef 的两份拷贝」低估了拷贝数（措辞风险）

D3 的 17 字节序列在全镜像出现 **80** 次（80 处全部在 .text），其中 77 处严格落在 0x6BEEC0 + 0x180*i 的等差格点上、并被 77 张工厂表以 slot1 引用；另 3 处在 0x007AC690 / 0x007AC800 / 0x007AD620，也被 .rdata 引用（0x3F76B8 / 0x3F7670 / 0x3F78E8）。

主张句「是同一份 AddRef 的两份拷贝」若按字面读（镜像里只有两份），与实际 80 份不符；若按「这两个地址是同一实现的两个副本」读则成立。

我更相信：这 17 字节是**编译器为同一模板/同一内联体批量生成的 80 份副本**，0x6C2AC0 与 0x6C51C0 只是其中两份。这不影响「两者逐字节相同」这一核心断言（该断言我已逐字节 + sha256 双证），但「两份拷贝」应改成「同一实现的副本之一」。

### 6.3 63/77 与 40 次桩的引用关系容易被读成因果（我在卡外复核时踩到）

F29 同时写「8 字节桩全镜像 40 次」和「63/77 双槽皆桩」。这两个数字不自相矛盾（40 是**桩体地址**个数，126 是**槽引用**个数），但字面上极易被读成「63 表 × 2 槽 = 126 桩，与 40 次冲突」。我按同样的主表规则独立复算了一次 63/77，得 63/77（卡片外的附加复核，见 run_extra_63of77.log），并查明这 126 个槽引用只指向 **6 个不同桩体地址**：0x00410300（61 次）、0x00410310（61 次）、0x0050E340、0x0050E350、0x00512740、0x00512750（各 1 次，分别归 HouseClass 与 HouseTypeClass）。也就是说 61 张表共用 0x410300/0x410310 这一对桩，其余 2 张（HouseClass、HouseTypeClass）各用自己的专属桩对。

我更相信：40（桩体数）与 63（表数）需要在同一句里显式写「桩体 vs 槽引用」的区别，否则 40 这个数字会被当成对 63 的反证。这条不改变任何数字，只是防误读。

复算输出（run_slot_dedup.log）：

    63 张双桩表共 126 个槽引用，去重后 6 个不同桩体地址:
      0x00410300 被引用 61 次  (例: AITriggerTypeClass,AircraftTypeClass,AirstrikeClass,AlphaShapeClass)
      0x00410310 被引用 61 次  (例: AITriggerTypeClass,AircraftTypeClass,AirstrikeClass,AlphaShapeClass)
      0x0050E340 被引用 1 次  (例: HouseClass)
      0x0050E350 被引用 1 次  (例: HouseClass)
      0x00512740 被引用 1 次  (例: HouseTypeClass)
      0x00512750 被引用 1 次  (例: HouseTypeClass)
    对比: 全镜像 8 字节桩体出现 40 次（其中被数据节引用的 14 处、未引用 26 处）

---

## 附录 A · 卡外附加复核（不计入 D1..D5，供裁决参考）

为避免主数字只被「验了一遍」，我对 F29 最承重的 63/77 也写了一遍独立实现（r135_ds_f29_extra_63of77.py）：扫 .rdata 每个 dword，凡 .text 地址即试当 vtable 起点，用 vtable[-4]→COL→COL+0xC→TD→TD+8 取类型名（不依赖任何既有脚本），按名字聚合、主表 = 槽数最多（并列取地址最小），读 slot1(+4)/slot2(+8) 比 8 字节桩。

    .rdata 内形如 .text 地址的 dword 数 = 14966
    解析出的具名 vtable = 1214 ; 不同名字 = 954
    工厂类型名 77 种
    主表(槽数最多/并列最小地址) slot1&slot2 双槽皆 8 字节桩 = 63 / 77   [F29 主张 63/77]
      缺产品类具名 vtable = 0
      slot1桩 且 slot2非桩 / 反之 = 0
      双槽皆非桩          = 14

14 个非双桩恰好是 11 个 Locomotion + AircraftClass + BulletClass + CStreamClass，与 F29 的「Locomotion 11 个全非桩」和「Other 族 3 个例外」完全对上。这条 63/77 是我独立复现的，不是抄的。

另外两个顺手得到的旁证（不属于本卡要求，记录备查）：

1. IAT 槽的磁盘值：339 条按名条目在磁盘上都预填了 .text 地址（互不相同、无重复），33 条序数条目是 0x8xxxxxxx 标记值。我进一步检查 339 个预填地址是否像真函数入口：84 个前 1 字节是 CC/90/00 填充、4 个前 1 字节是 C3(ret)、其余落在任意指令中间，且相邻预填值既不单调、步长也不集中。最直接的个案是 0x7E11C8 这一槽：磁盘值是 0x0040F990，反汇编该处得到

        i686-w64-mingw32-objdump -d --start-address=0x40F990 --stop-address=0x40F9A4 ra2bench/gamemd.exe
        0040f990: dd 05 18 17 7e 00   fldl   0x7e1718
        0040f996: dc 35 88 75 88 00   fdivl  0x887588
        0040f99c: dd 1d 50 75 88 00   fstpl  0x887550
        40f9a2: c3                  ret

   是一段 x87 浮点运算，绝不可能是 InterlockedIncrement。这支持 F29 limitations 第 ③ 条「不得用 IAT 槽值反推真实函数体地址」——磁盘上的 339 个 .text 值不是有效函数指针，导入语义只能从 .detour 的 IBN 读。
2. .rdata 里的 IAT 数组不是连续块：371 个槽分布在 384 dword 的跨度内，有 14 个单 dword 空洞（例如 0x3E1024→0x3E1028、0x3E10CC→0x3E10D0），空洞处是别的数据。引用「IAT 数组 371 条」时不宜假设它是一段紧凑数组。

## 附录 B · 产物清单（全部在 _r135/sub_deepseek/）

    REPORT.md                        本报告
    r135_ds_f29_final.py             D1..D5 主复算脚本（PE 头 + 正则 + 字节搜索 + 手工导入遍历）
    run_final.log                    主复算的原始输出（sha256 7db7fd77...4f41d）
    r135_ds_f29_d1_tailat.py         D1 尾部 @ 个数核查
    run_d1_tailat.log                上者输出
    r135_ds_f29_d2_stub_refs.py      40 处桩的数据节引用统计（槽内 14 / 槽外 26 旁证）
    run_d2_stub_refs.log             上者输出
    r135_ds_f29_d3_vtable_chain.py   D3 两处 VA 的 vtable[-4]→COL→TD→名字链核验
    run_d3_vtable_chain.log          上者输出
    r135_ds_f29_extra_63of77.py      卡外：63/77 产品类双槽桩的独立复算
    run_extra_63of77.log             上者输出
    r135_ds_f29_slot_dedup.py        126 个槽引用 → 6 个桩体的去重分析
    run_slot_dedup.log               上者输出

未改动 ra2bench/ 与 lead/ 下任何路径；没有创建或修改 _r135/sub_deepseek/ 之外的任何文件；/tmp 下临时文件已删除。
