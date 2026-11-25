# R129 跨家族审计卡 · 对「CLSID -> 类对象 -> 类名」四段链的独立复算

## 你要做什么

对本轮主会话产出的四段链，**自己反汇编、自己算**，逐段判成立与否。不要引用主会话给
出的任何数字当结论，只当线索。凡你认为不成立，写出你自己的数与主会话的差在哪。

## 环境

- 目标：D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe，先自校验 sha256 =
  73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- ImageBase 0x400000，pefile 读段表。capstone 必须 skipdata=True。
- 内存红线：只用 disasm_lite 流式，禁止对整段 .text 开 detail=True 的 disasm。
- 产物只写 lead\next_re_20261117_r14\R17_R129_AUDIT\ 下你自己的文件。
- 卡面与本报告正文一律不得出现反引号字符。

## 待核的四段链

段一：0x6bc42a 起把 4 个实参压栈（&局部、1、1、0xa8e8c8），第五个实参 0x7e9520 由
      0x6bc43a 的 push 压入，随后 mov esi,[0x7e15d8] + call esi。请自行确认 0x7e15d8 在
      本映像导入表里对应哪个函数名，并确认 CoRegisterClassObject 的参数顺序下
      pUnk 是 0xa8e8c8、rclsid 是 0x7e9520。

段二：0xa8e8c8 在 .data 的段内偏移是多少，是否超过 SizeOfRawData；全 .text 里以 imm32
      形式提到 0xa8e8c8 的站点有几处、地址各是哪些；其中哪一处是「写 vptr」形态
      （字节 c7 05 后跟该地址），写进去的立即数是什么。请给出你数出的站点集合。

段三：那个立即数作为 vtable 地址时，COL 在哪个地址、TypeDescriptor 解出的类名是什么、
      基类列表的三项（名字、ncb、mdisp）各是多少。

段四：0x6bd945 的 call ebx 的 ebx 从哪来（给出定义点地址与它的 IAT 槽与函数名）；
      该调用点前四条 push 的立即数各是什么；0x7e9520 作为 imm32 在全库出现几处、
      地址各是哪些；其中哪两处分别是「注册类对象」与「注册活动对象」的 rclsid 实参。

## 必须给的反控

1. 把段一的 rclsid 换成 .rdata 里相邻的另一个 16 字节 GUID 常量，说明该常量是什么、
   与 0x7e9520 差在哪个字节。
2. 段二的「写 vptr」判据若放宽成「任何 mov [abs],imm32」，在全 .text 里命中多少处？
   说明为什么必须按目标地址过滤。
3. 段三若换成另一张你随手挑的真实类 vtable，类名是否不同？给出你挑的地址与类名。

## 输出

一份 Markdown，结构：环境核验 / 段一 / 段二 / 段三 / 段四 / 反控 / 结论（逐段 PASS 或
FAIL 与理由）。所有数字必须是你自己跑出来的，附上你可复现的脚本路径。
