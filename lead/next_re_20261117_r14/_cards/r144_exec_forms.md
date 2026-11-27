# R144 执行卡：多形态装表普查独立复算（exec）

## 角色与边界
- 角色：exec（执行），模型 work/cn:hy4flash-free。
- 只读：允许读 /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe 与 _r143/r143lib.py。
- 禁止：写任何 FACT_INDEX/看板/四件套；禁止修改 _r143 与 _r144 下已有文件；只在 _r144/sub/ 下写自己的脚本与 json。
- 内存纪律：禁止对整段 .text 开 capstone detail=True；只许 disasm_lite 64KB 分块流式；脚本必须带 timeout。

## 目标（一次取证，一条命令输出全部数字）
用你自己独立实现（不要 import r144a/r144b 的结论，只许复用 r143lib 的 va2off/rd 这类地址换算或干脆自己写），复算下列九个数，并与我给的目标值逐项对比：

1. 虚表集合 VTS distinct 数（R143 口径：.data/.rdata 里 dword[vt-4] 属于 COL 的所有 vt）。目标 1218。
2. 形态 F1 = mov dword ptr [rX+0], imm 且 imm in VTS 且 rX 是 eax/ebx/ecx/edx/esi/edi 的**站点数**与**distinct 虚表数**。目标 2741 / 838。
3. 形态 F3 = 同 F1 但位移 != 0 的站点数、distinct 虚表数、位移直方图前三（位移值, 次数）。目标 1305 站点 / 344 distinct；直方图前三 12:345、4:344、8:338。
4. 形态 F4 = mov dword ptr [绝对地址], imm 且 imm in VTS 的站点数与 distinct。目标 341 / 243。
5. F1 未覆盖虚表数（1218-838）。目标 380。
6. 这 380 张里，有多少张存在「同一 RTTI TypeDescriptor（COL+12）下另有一张已被 F1 覆盖的虚表」。目标 229。
7. 对整个 VTS 计算：装表站点 (vt, disp) 对里 COL(vt)+4 == disp 的一致率。目标 0.9231（2697+ 见下）。
8. 同一集合上「把 disp 在所有站点间随机置换（seed=144）」后的一致率。目标 0.9231（我怀疑这是恒等式/退化反控）。
9. 独立假设基线：Sum over d of P(COLoffset=d) * P(disp=d)，其中两个边缘分布都从数据实测。给出数值。

## 附加判别（重要）
对第 8 项，请明确判断：如果置换**只在同 disp 桶内**做，一致率是否必然不变（因为一致率只依赖 disp 的边缘分布，与 vt 无关）？给出你的结论与一句论证。这决定我是否要作废该反控。

## 输出
写到 _r144/sub/r144_exec.json，键名自定但须含上面 9 个数与你的一行判断；终端打印一行 JSON 汇总。全部证据在一条命令里产出（含 sha256、站点数、直方图、两项一致率与独立基线）。
