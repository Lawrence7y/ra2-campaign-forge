# R202 卡 B（执行员 hy4，只读源码+自写脚本）：反查 8 条 none 装填的宿主类名 + INoticeSink 位移 8 的成因

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge。共享模块 _r185/pe185.py（提供 P.RAW、P.B 段表、P.r2o、P.where、P.dw、P.cstr）。capstone 可用（CS_ARCH_X86 / CS_MODE_32）。参考已有脚本 _r201/m12_final.py（内含 COL 类名表重建、虚表表重建、全 .text 线性反汇编、ret/int3 区间划分、装表 store 提取的完整做法，请直接复用其口径，不要另起一套）。禁止反引号。禁止修改任何既有文件；你的脚本与输出只写到 _r202/ 下，文件名前缀 b_。

## 背景口径（R201 已实测，你不用重复验证，直接沿用）
- 虚表表 VT：地址 -> 所属 COL 记录地址；COL 记录含 mdisp 与类名（.?AV...@@ 形式）。主表 = mdisp==0，次表 = mdisp!=0。
- 装表 store = .text 内 C7 /0 且 disp8 在 1..9、imm32 落在 VT 的指令。全段 697 条「小位移次表类」store。
- 代码区间 = 以 ret/int3 指令结束边界切分的连续区间，全 .text 共 31,968 个。
- 按区间归属后 697 条 = both 689 / only_sub 0 / none 8。

## 任务 T1：反查 8 条 none 装填所属区间的宿主类名（取证，不是猜测）
8 条 store 地址（R201 实测）：0x5d5b80、0x635f34、0x637114、0x638aa4、0x6cf196、0x6cf209、0x7b1b2b、0x7b27fb。
对每一条：
1. 用与 _r201/m12_final.py 相同的区间划分求出它所属区间 [start,end)。
2. 在该区间内列出全部装 VT 的 store（含 mdisp==0 与 mdisp!=0），给（地址、位移、imm、mdisp、类名）。
3. 若区间内有 mdisp==0 的装表：这些就是宿主（或宿主内嵌成员）的主表 -> 给类名。若区间内有多于一个不同的 mdisp==0 类名，全部列出并说明谁先谁后。
4. 若区间内一个 mdisp==0 装表都没有：改为用区间起点向上/向下找宿主对象的另两条线索：(i) 该区间起点在 CALLAT 目标集合内时，找调用它的 call 站点，看调用前 24 字节内是否有 lea ecx,[esp+K] 或 mov ecx,imm/reg（构造函数的典型 this 传递）；(ii) 区间内是否有对同一基址寄存器的其它字段初始化（mov [reg+K],imm/reg）。把你能拿到的证据全部列出，拿不到就明确写 UNDETERMINED。
5. 结论字段：每条给 host_class（若取得）、证据类型（区间内主表 / 调用点 this 传递 / 其它）、以及是否仍 UNDETERMINED。

## 任务 T2：3 条 .?AVINoticeSink@@ 主表装填为何位移是 8 而非 4
3 条 store 地址：0x410174、0x4101c2、0x6e8008。
对每一条：
1. 打印该 store 所属区间的 start..end 与整个区间内所有装 VT 的 store（地址、位移、imm、mdisp、类名），按地址顺序。
2. 打印该 store 前后各 40 字节的完整反汇编（含地址、字节、助记符），标出 this 基址寄存器是哪一个、它是怎么来的（函数首指令 mov edi,ecx / mov [esp+4] 等）。
3. 判定：该 store 装的 c7 位移 8 对应的是对象的哪个子对象；宿主对象首字段（+4 处）装的是哪个类的主表（若区间内有）。给「为什么是 8」的二进制内证据，若证据不足写 UNDETERMINED 并说明缺哪一环。
4. 附加：把这 3 条所属区间里 INoticeSink 的其它次表装填数（R201 记录为 3/3/6）复算出来。

## 必须的正反控（写进脚本，输出 PASS/FAIL）
- 正控：从 VT 里任取 3 个已知类（例如 .?AVAirstrikeClass@@），用你的区间函数求出其主表装填所属区间，与 R201 记录（Airstrike 6 处/6 区间）一致。
- 正控：697 条 store 在你复用的提取器下必须复现 697。
- 反控：把区间划分的错误版本（不切 ret/int3、整段当一个区间）跑一遍，结果的 both 必然等于 697、none 必然等于 0，用来证明区间切分确实起作用。
- 反控：对 8 条 none 中的一条，把它强行归到上游第一个 CALLAT 目标所在区间，看结论是否改变（用于说明归属敏感度）。

## 输出纪律
- 一条命令跑完全部证据（脚本 + 运行），输出既打印到 stdout 也落 _r202/b_nonehost.json 与 _r202/b_nonehost.log。
- 断言逐条 PASS/FAIL，末尾 SUMMARY asserts=N fails=M。
- 所有数字必须实测，禁止预估或从本卡抄。取得不到的一律写 UNDETERMINED 并说明缺哪一环。
- 单条命令 timeout 900 秒；禁止对整段 .text 开 detail=True 一次性 disasm（用 disasm_lite 或 64KB 分块）。
