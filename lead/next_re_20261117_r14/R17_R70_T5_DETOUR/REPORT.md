# R38-T5-DETOUR · REPORT

镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
size = 0x49A110；sha256 = `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与 R17_R68_T1_IAT 报告一致，已实测匹配）
Machine=0x014C(I386)、Magic=0x010B(PE32)、ImageBase=0x400000。

## 口径声明（强制）
- 所有地址（VA / RVA / 节头 VirtualAddress 字段）与文件偏移（offset）一律 `0x` + **大写**十六进制，风格统一；节内相对偏移写作 `+0xNNNNN`，同为大写十六进制。
- 节头 `VirtualAddress` 字段存的是 **RVA**。任务卡与 T1 报告沿用的「VA=0x793000」即该字段值；真实 VA = ImageBase + RVA = 0x400000 + 0x793000 = **0xB93000**。本报告按卡面写 `VA=0x793000` 并在此澄清其为 RVA。
- 「可读 ASCII 串」= 连续可打印 ASCII 字节（0x20..0x7E）的极大游程，长度 ≥6。
- 函数序言 / ret 的字节计数只作**结构画像**，**不作函数入口判据**（未用「按字节扫 E8/C3/C2」判入口）。
- 只列可机械判定的事实；**不对「谁改的 / 为什么改」作任何定性推断**。取不到的写「未取得 / 无法判定」。

## 六行结论（交付格式）

Q1 | .detour: VA=0x793000(节头VirtualAddress字段=RV；真VA=0xB93000) vsize=0x2718 raw=0x497000 rsize=0x3000 ; 非零字节=6980/10008 ; ASCII串(≥6字)=358条：DOS桩串"!This program cannot be run in DOS mode."(+0x8D/off 0x49708D)、MZ/Rich头短串4条、16个导入DLL名(xyr/KERNEL32/USER32/GDI32/ADVAPI32/SHELL32/ole32/OLEAUT32/WINMM/WSOCK32/DDRAW/DSOUND/VERSION/COMCTL32/IMM32/binkw32.dll)、337条导入函数名(含InterlockedIncrement@off 0x4981F2、InterlockedDecrement等)，全表见 detour_ascii_strings.txt ; 函数序言迹象=无(55 8B EC=0、83 EC=0；0xC3=1、0xC2=6 为数据字节、非入口判据)

Q2 | Import dir 0x7955C0 -> 节=.detour ; KERNEL32 FirstThunk 0x3E10D0 -> 节=.rdata ; IBN 0x7941F0 -> 节=.detour

Q3 | 非标准迹象: ①节数=5，比常见标准4节(.text/.rdata/.data/.rsrc)多一个.detour ②.detour的Characteristics=0xC0000040(可读写已初始化数据节、不可执行)却内含MZ头(节内+0x40/off 0x497040: `4D 5A 90 00…`)与DOS桩串"This program cannot be run in DOS mode."(off 0x49708D) ③该MZ的e_lfanew=0x108处字节=`01 00 00 80`、非"PE\0\0"(不完整DOS/PE样板) ④Import Directory(0x7955C0)与全部16个IMAGE_IMPORT_DESCRIPTOR及其OFT(ILT)/NameRVA、全部IBN名字区均落.detour，而FirstThunk(IAT)除xyr.dll外全落.rdata、槽值形如0x0040F990/0x00410xxx(.rdata内绑定伪地址、非真实函数体)——即「导入布局非原版」的机械证据 | 已核查但结果正常(非非标准): 节表按VirtualAddress升序=是；虚拟区间/原始区间重叠对=无；SizeOfImage=0x796000恰等于末节.detour对齐末RVA=0x796000；vsize=0x2718<rsize=0x3000、尾段0x8E8字节实测全零(标准零填充)；TimeDateStamp=0x3BDF544E、CheckSum(header)=0x00000000(原值记录，不据此定性) | 无法判定项: 「.detour」是否为标准MSVC链接产物命名=无法判定(单文件、无链接器参照)；「谁加的/为何加」=不作判定(纪律禁止定性推断)

Q4 | 对 F29 的影响: 不影响 | 理由: F29的关键一步「导入名=InterlockedIncrement」是.detour节内的**明文IBN字符串**，逐字读出off 0x4981F0=`B0 01`+`InterlockedIncrement`+`00`(Hint=0x1B0=432)，字符串内容与所在节名/节属性无关；导入链机械自洽：ImportDir(0x7955C0,.detour)→KERNEL32描述符→ILT idx62(RVA 0x793248/off 0x497248=`F0 41 79 00`)→IBN(0x7941F0,.detour)，正控InterlockedDecrement(idx63)、DefWindowProcA/GetBkColor/RegQueryInfoKeyA同样解出。.detour只改变「ILT/名字区放在哪个节」和「IAT槽绑定值形态」，不改变「按名字导入的是哪个函数」。唯一边界：不可用IAT槽值反推真实函数地址(会得到.rdata内0x0040F9xx伪地址)——与F29断言无关。故0x7E11C8经导入表证实为KERNEL32!InterlockedIncrement这一步不被动摇；但「多出非标准.detour节、导入布局非原版」是独立机械事实，应继续作为限定保留，不因本卡消失，也不升级为「F29不可信」。

Q5 | 正控节 .data 前64字节=00 00 00 00 E0 3C 40 00 10 3D 40 00 30 3D 40 00 50 3D 40 00 70 3D 40 00 90 3D 40 00 B0 3D 40 00 F0 3D 40 00 20 3E 40 00 50 3E 40 00 80 3E 40 00 90 3E 40 00 B0 3E 40 00 20 69 40 00 50 69 40 00 ; 含ASCII=是(≥6字串8321条，与.detour的358条同为合理输出，且对vsize 0x367BE4>rsize 0x6C000的BSS尾段正确回退到文件支撑长度) ⇒ 画像程序可用

OVERALL | .detour是追加的可读写数据节，内含MZ/DOS头样板与整套导入结构(描述符+ILT+IBN名字区)、IAT留在.rdata且为绑定伪地址；这是「导入布局非原版」的机械事实，但导入名是明文、不动摇F29对0x7E11C8=KERNEL32!InterlockedIncrement的判定，故结论为「不影响」——同时建议在F29中继续保留「多出非标准.detour节、导入布局非原版」这条限定(作为独立事实),不据此降低对InterlockedIncrement导入名的采信。

## 复算脚本

`detour_profile.py`（本目录；纯 struct、无第三方依赖；只读 exe，不写 exe、不写任何受保护文件）
- 重跑：`cd D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R70_T5_DETOUR` → `$env:PYTHONIOENCODING='utf-8'; python detour_profile.py > detour_profile_out.txt`
- 产物：`detour_profile_out.txt`（完整机器输出，8767 行）、`detour_ascii_strings.txt`（.detour 全部 358 条 ≥6 字串，由输出抽取）。

### 关键原始字节（手工可核）
- 节头 `.detour`@节表第4项：VirtualSize=0x2718 / VirtualAddress=0x793000 / SizeOfRawData=0x3000 / PointerToRawData=0x497000 / Characteristics=0xC0000040。
- DataDirectory[1] IMPORT: RVA=0x7955C0, Size=0x154 → off 0x4995C0（落 .detour 节内 +0x25C0）。
- 描述符原始 20B @off 0x4995D4(KERNEL32)：`50 31 79 00 | 00 00 00 00 | 00 00 00 00 | 70 3D 79 00 | D0 10 3E 00`（OFT=0x793150、NameRVA=0x793D70、FirstThunk=0x3E10D0）。
- ILT idx62 @off 0x497248 = `F0 41 79 00` → IBN RVA 0x7941F0。
- IBN @off 0x4981F0 = `B0 01 49 6E 74 65 72 6C 6F 63 6B 65 64 49 6E 63 72 65 6D 65 6E 74 00` = Hint 432 + "InterlockedIncrement"。
- .detour 节内 +0x40(off 0x497040)：`4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00`（MZ DOS 头）；+0x8D(off 0x49708D)：DOS 桩字符串；MZ+0x3C=0x108 处 = `01 00 00 80`（非 PE 签名）。

### 纪律声明
- 全程只读 `gamemd.exe`；未修改 `R14_COMMON.md` / `LEAD_LOCK` / `GOAL_THREE_TARGETS_20261018.md` / `STATUS_BOARD.md` / `BOARD_ARCHIVE.md` / 任何 `FACT_INDEX.tsv`。
- 未用「按字节扫 E8/C3/C2」作函数入口判据；序言/ret 字节计数仅为结构画像。
- 产物只写本目录 `lead\next_re_20261117_r14\R17_R70_T5_DETOUR`。
- 未对「谁改的 / 为什么改」作任何定性推断。
