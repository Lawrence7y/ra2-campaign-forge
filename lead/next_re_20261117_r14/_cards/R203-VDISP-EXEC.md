# R203-VDISP-EXEC — 独立重算虚拟分派基线（虚表 / 槽位 / 间接调用四分类）

## 背景与你的角色

你是执行员（模型 hy4）。主会话已跑出一份基线，你的任务是**用你自己写的脚本独立重算同一批数字**，不允许读取主会话的 json 直接抄。

主会话产物（可读，但只当线索）：_r203/m1_dispatch.py、_r203/m1_dispatch.json、_r203/m2_prologue.py、_r203/m2_prologue.json

## 材料

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  SHA-256 必须是 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（先自校验）
- ImageBase 0x400000，.text = [0x401000, 0x7e038d)
- 工具：python3 + capstone 5.0.7 + pefile，公共映射模块 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py（内含 RAW / B / dw / where / cstr / r2o），可直接 import
- **防 OOM 硬红线**：禁止对整段 .text 开 detail=True 一次性 disasm；只能用 md.disasm_lite(BUF[p:p+65536], va) 分块线性扫描，且只对命中的少数地址单独 md.disasm()。后台命令必须带 timeout。

## 必须重算的七项（每项给出你的数值）

1. **COL 记录**：RTTI Complete Object Locator 扫描。判据 = 在 .rdata/.data 按 dword 对齐四点组 (signature∈{0,1,2}, mdisp, pdisp==0, ptd: .data 里放 type_info 指针, pcd: .rdata 里放 class 名字符串)。名字必须以 .?A 开头、以 @@ 结尾。给总数。
2. **vtable**：全 .rdata/.data 扫，若某 dword 落在 .text 内且其前一个 dword (va-4) 是本表里的某个 COL 地址，则该 dword 地址是一个 vtable 起始。给总数，并验证 vt-4 全部是 COL。
3. **槽位**：从每个 vtable 起始起，按 4 字节步进读，直到读到的值不再落 .text 内即停。给槽位总数、去重目标数、每 vtable 槽数直方图前三名。
4. **槽位切分正确性**：任取 200 个槽位，检查 vtable+4k 位置是否落在另一个 vtable 起始上（应为 0 次）。
5. **间接调用四分类**：线性扫描全部 call。直接 call（操作数直接是 0x 立即数）与间接 call 分开。间接 call 再分四类：(a) 绝对 [0x......]（IAT 型）；(b) [reg] 或 [reg + disp]（基址型）；(c) 纯寄存器 call reg；(d) 其它（列全部地址与文本）。给总 call 数、直接数、间接数、四类各自数。
6. **位移普查**：基址型里 disp 的取值集合：个数、是否全为 4 的倍数、出现最多的前 10 个 (disp, 次数)。
7. **交叉**：直接 call 的去重目标集（仅统计落 .text 内的）与槽位去重目标集求交、各自差集大小。另外单列「槽位目标里不在线性扫描指令起点集合中」的地址清单（主会话测到 13 条）。

## 输出

- 脚本 _r203/hy4_vdisp.py，结果 _r203/hy4_vdisp.json，日志 _r203/hy4_vdisp.log
- 日志里必须一次性打印：七项数值 + 每个断言 PASS/FAIL + 正反控
- 正反控至少两条：① 把 vtable 判定条件里的「va-4 是 COL」去掉后，vtable 数应显著改变；② 把「读到不落 .text 即停」改成「最多读 3 槽」后，槽位总数应显著减少

## 纪律

- 一次取证：一条命令输出全部证据，禁止把一个事实拆成多次单点命令。
- 只写 _r203/hy4_* 文件；不许改 _r203/m1_*、_r203/m2_*，不许改任何台账、R14_COMMON.md、LEAD_LOCK、STATUS_BOARD.md。
- 数字先实测再填，禁止预估。与你预期不符的地方如实写出来，不要为了让结论好看而调参。
- 每项结论都要能由你自己的脚本复现；引用主会话数字必须标注「引自主会话，未独立复核」。
