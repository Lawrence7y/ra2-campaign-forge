# R106 跨家族审计卡（deepseek）

## 被测对象
文件 ra2bench/gamemd.exe，sha256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
ImageBase 0x400000，.text VA [0x401000, 0x7e038d) VirtualSize 0x3df38d = 4060045。

## 背景（以下是我方 R104/R105/R106 已落盘的结论，你要做的不是重做，而是判它们真假）
gamemd.exe 的 .text 里有 360 张「跳转指针表」，判定法：找 jmp dword ptr [reg*4 + ABS] 持有指令，
其 ABS 落在 .text 内，然后从 ABS 起逐 DWORD 读项值，只要项值仍是 .text 内地址就继续，上限 512，
n>=2 才算一张表。360 张表合计 2702 项。
其中 R101 分类为 B1 的 41 行宿主（去重 31 个不同宿主地址）落在 19 张表内，这 19 张表合计 292 项。
292 项里去重后 276 个不同项值，即重复组共 8 组、多出 16 项，重复分布在 5 张表。

## 请审计的 3 项（全部只需静态读 exe，不需要运行 exe）

A1. 独立重算 360 / 2702 / 19 / 292 / 276 / 8 / 16 这七个数。
    允许你用任何解码器（capstone 5.0.7 / iced-x86 / objdump 皆可）。若你的数与上面不同，
    必须逐项说明差在哪张表哪个地址，不要只报一个不同的总数。

A2. 判「8 组重复里有几组的多个 case 真的等价」。
    已落盘结论是：6 组判为 IDX_DEAD_HERE（目标块在读到索引寄存器旧值之前就把它整个覆盖了，
    所以多个 case 是同一段代码），2 组判为 CALL_CLOBBER（在索引寄存器被定义前就遇到 call，
    cdecl 可毁寄存器，本层不可判），0 组判为 DEPENDS_ON_IDX。
    8 组的目标地址是：0x4c6cde / 0x4c71ca / 0x4c8109 / 0x58bd95 / 0x69af45 / 0x69b08c /
    0x6dfddb / 0x728de0。
    请对每一组独立判定它属于三类中的哪一类，并列出你的判据。特别注意两点：
    一，xor eax,eax 与 sbb eax,eax 与 or eax,-1 是「全写、不读旧值」，不能因为操作数是 eax
    就判成依赖；二，cmp eax,imm 是只读不写，也不能判成覆盖。
    0x69af45 与 0x69b08c 两组是 xor 的实例，最容易被判错。

A3. 审计下面对 0x728e08 这张表的描述是否字面成立。
    该表 7 项，项值序列为 0x728de0 / 0x728dd9 / 0x728dd0 / 0x728c1e / 0x728de0 / 0x728de0 / 0x728de0。
    已落盘描述：下标 2 的目标 0x728dd0 先写常量 5 到 [edi+0x14] 然后 jmp 0x728de0；
    下标 1 的目标 0x728dd9 写常量 7 到 [edi+0x14] 然后自然落穿进 0x728de0（不需要 jmp）；
    下标 0/4/5/6 四项都直接跳到 0x728de0 同一地址，故这 4 个 case 完全等价；
    下标 3 的 0x728c1e 走完全不同的路径。
    请逐条核字面真假。

## 硬性要求
1. 只做静态读字节与反汇编，禁止运行 gamemd.exe，禁止联网，禁止 GUI。
2. 内存红线：严禁对整段 4 MB 的 .text 开 detail=True 后一次性调用 md.disasm()，
   会在堆上暴涨超过 1.5 GB 被 OOM Killer 杀掉。全段扫描必须用 disasm_lite()
   或按不超过 64 KB 分块流式迭代并及时释放，只对命中的少数地址单独开 detail=True。
3. 你的脚本与产物写到 /home/t628/projects/ra2-campaign-forge/_r106/_audit/ 下，
   文件名以 audit106 开头。不要覆盖该目录里已有的 audit106.py 与 audit106.json。
4. 输出一份 AUDIT106.md，逐项写 A1/A2/A3 的裁定：CONFIRMED / REFUTED / UNDECIDABLE，
   每条附你实测到的数字或地址作为依据。若你认为我方的判据本身有缺陷，直接说，不要迁就。
5. 时间预算 8 分钟，请优先保证 A1 与 A2 有结论；A3 做不完可标 UNDECIDABLE。
