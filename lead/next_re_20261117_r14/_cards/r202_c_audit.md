# R202 卡 C（审计员 deepseek，只读，<=35 回合）：独立复算「真函数入口口径」并复核 R201 三条结论

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge。共享模块 _r185/pe185.py（P.RAW、P.B 段表、P.r2o、P.where、P.dw、P.cstr）。capstone 可用的 python3 环境（CS_ARCH_X86 / CS_MODE_32）。参考脚本 _r201/m12_final.py 里有 R201 的完整口径（COL 重建、VT 重建、全 .text 反汇编、ret/int3 区间、装表 store 提取）。你是只读审计员：不得修改任何既有文件，只把自己的脚本写到 _r202/audit_c.py 并运行，输出落 _r202/audit_c.json 与 _r202/audit_c.log。禁止反引号。

## 待复核主张（逐条给 CONFIRM / REFUTE / UNDETERMINED + 你的实测数字 + 一句话判据）

A1. 全 .text 线性反汇编，ret/int3 指令结束边界共 31,967 条，据此切出的连续代码区间共 31,968 个。请独立复算这两个数（注意：不同迭代终止条件会造成个位数差异，若有差异请给出你得到的具体数与差异原因）。

A2. 装表 store 定义 = .text 内 C7 /0（mod 为 1 或 2，disp8 或 disp32）且 imm32 落在虚表集合 VT 内的指令。其中「小位移」子集（1<=disp<=9）应为 697 条。请独立复算 697。

A3. 上述 697 条中，disp8 等于其 imm 对应 COL 记录 mdisp 的为 686 条（其中 mdisp==4 有 345 条、mdisp==8 有 341 条），不等 11 条且这 11 条的 mdisp 全为 0。请独立复算。

A4. 按区间归属（每条 store 归到它所在的 ret/int3 区间）：同区间既有 mdisp==0 装表又有 mdisp!=0 装表的 689 条；只有 mdisp!=0 的 0 条；区间内无任何 mdisp!=0 装表的 8 条；无归属 0 条。请独立复算这四个数。

## 本轮新增任务（主会话尚未取得，请你自己算，不要抄任何数）

B1. 真函数入口过滤：把 31,968 个区间收紧为「真函数体」。可用判据任选其一或组合，但请在脚本里明确写出你用的判据：
   (i) 区间起点属于 CALLAT 目标集合（call rel32 的 target 且落在 .text）；
   (ii) 区间起点处有典型序言（push ebp; mov ebp,esp 或 push 后跟 sub esp,imm 或 mov edi,edi;push ebp;mov ebp,esp 这类 MSVC 序言）；
   (iii) 区间起点前一条指令是 ret/int3 且区间长度 >= 某阈值，或区间内至少有一条 ret（而非以 int3 结束）。
   请给出：(a) 满足 (i) 的区间数；(b) 满足 (ii) 的区间数；(c) 满足 (i) 或 (ii) 的区间数；(d) 既非 (i) 也非 (ii) 的区间数，并给这些区间的长度分布（p50/p90/max）与 12 个例子地址。

B2. 在「真函数体」子集上重算 A4 的三分类（both / only_sub / none，分母仍是 697 条小位移 store，未落入真函数体的 store 单列一类 nonfunc）。请给四个数。

B3. 反控：把判据 (i) 换成一个错误版本（例如区间起点属于任意含 0xC3 字节的地址附近 3 字节内），三分类必然变化，用来证明过滤不是恒等变换。请给错误版本下的四数。

B4. 统计：697 条小位移 store 中，有多少条同时满足「区间内另有一次对同一基址寄存器、同一 imm 的重复装表」（重装），地址列表给前 10 个。

B5. 统计：这 697 条里，imm 对应的 VT 地址在 .rdata 与 .data 的分布；以及 VT 地址到 COL 记录的距离是否为常数（若非常数给分布）。

## 输出纪律
- 每条给 CONFIRM / REFUTE / UNDETERMINED + 实测数字 + 判据。
- 末尾给「主会话可能夸大或表述不准的地方」清单，若无可写「无」。
- 全部断言 PASS/FAIL，末尾 SUMMARY asserts=N fails=M。
- 数字全部实测，禁止预估；拿不到写 UNDETERMINED 并说缺哪一环。
- 单条命令 timeout 900 秒；禁止对整段 .text 开 detail=True 一次性 disasm（用 disasm_lite 或 <=64KB 分块）。
