# R208B 执行卡：T 形态 thunk 编码二型普查（独立盲测）

## 角色
执行员（只读取证 + 写一个小脚本），不得读取 _r208 目录下任何既有文件，也不得读 R14_COMMON 的 2.215 节。

## 目标文件
/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
可用辅助：/home/t628/projects/ra2-campaign-forge/_r185/pe185.py（PE 段映射，提供 RAW 全局变量与 dw(va)/where(va)/r2o(va)/cstr(va)）
可用库：python3-capstone、python3-pefile

## 任务（一次命令输出全部证据）
1. 枚举全部 COL 记录（判据：.rdata 与 .data 内 5 连 dword，满足 w0 在 {0,1,2}、w2==0、w3 落 .data 且 w3+8 处是 .?A...@@ 结尾 C 串、w4 落 .rdata）。给出 COL 总数。
2. 对每个 COL，找出 .rdata/.data 内值等于该 COL 地址、且其 +4 落 .text 的 dword 位置；若恰好 1 个，则 vftable 起点 = 该位置+4。
3. 主视图定义：COL 地址 == (pCHD + 16)；其余为额外视图。给出额外视图条数。
4. 对每条额外视图读 vftable slot0 指向的字节，按首字节分类并统计：
   - 形态 A：83 6C 24 04 <imm8> E9 <rel32>（sub dword ptr [esp+4], imm8 ; jmp）
   - 形态 B：81 6C 24 04 <imm32> E9 <rel32>（sub dword ptr [esp+4], imm32 ; jmp）
   - 形态 C：C2 04 00（ret 4）
   - 形态 D：32 C0 C2 08 00（xor al,al ; ret 8）
   - 形态 E：8B 44 24 04 3D ...（mov eax,[esp+4] ; cmp eax, imm32）
   - 形态 F：其它（给出 hex 前 8 字节）
5. 对形态 A 与形态 B 逐条核对：解码出的立即数是否等于该 COL 的 mdisp（BCD 的 +8 字段，signed int32）。给出通过数/总数，并列出任何一个不等的 (COL 地址, 类名, mdisp, 立即数)。
6. 给出形态 B 的全部条目（应很少）：COL 地址、类名、mdisp、vftable 起点、slot0、完整字节序列、jmp 目标地址。
7. 对形态 A 与 B，检查 jmp 目标是否等于本类主视图（pCHD+16 那条 COL）的 slot0。给出通过数/总数。
8. 反控：假设判据只认 83 6C 24 04（不认 81 6C 24 04），会漏掉几条？请直接给出漏掉条数与漏掉条目的类名。

## 交付
- 脚本写到 /home/t628/projects/ra2-campaign-forge/_r208/x1_tform.py，结果 json 到 _r208/x1_tform.json。
- 输出一段"断言 N / FAIL M"的清单，每条断言写明数字。
- 禁止在卡面或报告中写入未来得及实测的数字；所有数字必须来自本次运行输出。

## 内存
禁止对整段 .text 开 detail=True 一次性 disasm；只用 capstone 对个别 slot0 地址做 <=64 字节的小窗口反汇编。脚本整体加 timeout 300。
