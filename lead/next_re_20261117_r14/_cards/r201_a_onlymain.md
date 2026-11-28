# R201 卡 A（执行员 hy4）：11 个 only_main 宿主的真实装填序列 + only_main 口径订正

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge。已有共享模块 _r185/pe185.py（提供 P.RAW / P.B / P.dw / P.where / P.r2o / P.cstr）。capstone 可用。禁止反引号出现在任何输出文件。

## 背景（R200 已落盘事实，可直接引用）
R200 脚本 _r200/m11_subfill.py 里，宿主三分类的第三支 else 记作 only_main，其代码实为「窗口内 has_main 与 has_sub 皆为 False」——即窗口内一条装表 store 都没检出，而不是「只装主表」。R201 主会话实测：main11 的 10 个宿主与 only_main 的 11 个宿主集合不相等（交集 6）。

## 任务（一条命令内输出全部，禁止拆成多次单点命令）
写脚本 _r201/a_onlymain.py，复用 _r185/pe185.py 与以下既有口径（务必逐字复刻，数字必须与 R200 对上）：
- 装表 store 提取：扫 .text 原始字节，命中 0xC7 且 modrm.reg==0、rm!=4、(rm,mod)!=(5,0)；mod==1 取 disp8/imm32 共 7 字节，mod==2 取 disp32/imm32 共 10 字节。记 (va, regname, disp, imm)。
- COL 构造：扫 .rdata/.data 的 dword 窗口，条件 w[i] in (0,1,2) and w[i+2]==0 and where(w[i+3])=='.data' and where(w[i+4])=='.rdata'，类名 P.cstr(w[i+3]+8,400) 以 b'.?A' 起、b'@@' 止。
- VT 构造：扫 .rdata/.data，in_text(w[i]) 且 dw(base+4*i-4) 在 COL 里。
- CALLAT：单次迭代 disasm_lite，成功则前进，失败按 1 字节重同步；只收 mn=='call' 且 op_str 以 0x 起且目标 in_text。
- 宿主 = 该 store 地址之前最近的 CALLAT 目标（bisect_left-1）。
- 窗口终点 = min(下一个 CALLAT 目标, 宿主+4096)。
- 子表 = disp 在 1..9 且 imm in VT；主表 = imm in VT 且 COL mdisp==0；子表侧 = imm in VT 且 mdisp!=0。

必须输出的实证（全部打印 + 存 _r201/a_onlymain.json）：
1. 复现校验：子表 697 / main11 11 / 宿主 262 / (both,only_sub,only_main)==(251,0,11) / disp8==mdisp 命中 686 不等 11。任一对不上立刻 FAIL 并停止后续。
2. 对 11 个 only_main 宿主逐个给出：宿主地址、前一字节、首 16 字节 hex、窗口 [h, hi) 的全部反汇编指令（地址/字节/mnemonic/op_str）、窗口内所有 imm in VT 的 store（含 disp）、窗口是否含 call/ret、窗口长度。
3. 判定这 11 个窗口「为什么一条装表都没检出」，逐条给机械理由，从下列集合里选并给证据：
   (i) 窗口被截断（hi-h 小于函数实际长度，宿主+4096 或下一 CALLAT 目标提前截断）；
   (ii) store 形状不在 {C7 /0 disp8, C7 /0 disp32} 内（如 mov [reg],reg、push imm、rep stos、memcpy 调用、或 C7 但 modrm.reg!=0）；
   (iii) 装表发生在另一函数体内（本窗口确实不装表）。
4. 对每个 only_main 宿主，用宽松判据复扫：在该宿主之后 4096 字节内、不限 CALLAT 边界，找是否存在任何 imm in VT 的 store（任意形状：含 mov r32,[..] 反例不算，只认 imm 落 VT 的写内存）。给出命中地址与所属真实函数（用 CALLAT 目标回推）。
5. only_main 与 main11 的交集/差集明确列出（哪几个宿主两边都有、哪几个只在一侧）。
6. 反控：(a) 把窗口上限从 4096 改 8192 / 16384，看三分类数字怎么变；(b) 把宿主定义改成「CALLAT 目标 且 前一字节 in {0xC3,0xCC,0x90}」，重算三分类。

## 输出纪律
- 全部断言 PASS/FAIL 打印，末尾 SUMMARY asserts=N fails=M。
- 不写任何反引号字符。
- 单条 timeout 900 内跑完。
