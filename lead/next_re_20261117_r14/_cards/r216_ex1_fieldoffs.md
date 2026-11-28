# R216-EX1 取证卡：AbstractClass 字段偏移 +0x10 / +0x20 的写入者与消费者全量扫描

## 背景（已实测，勿重复）
- 目标文件 ra2bench/gamemd.exe，已构建 pe185 辅助模块：sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185'); import pe185 as P
  P.RAW 为整文件 bytes；P.where(va) 返回段名；P.r2o(va) 返回文件偏移；P.dw(va) 读 dword；P.B['.text'] 有 lo/hi_file/rawptr/rawsize。
- 已解出 ?AVAbstractClass@@ 主视图 0x7e1f50 的 24 槽，其中两条给了字段证据：
  - slot4 = 0x410450：mov dl,[ecx+0x20]; test dl,dl; sete al; ret 4  （+0x20 是 byte 标志）
  - slot13 = 0x410410：mov eax,[esi+0x10]; push eax; call 0x4a1d50 ；mov cl,[esi+0x20]; push ecx; call 0x4a1ca0
  - slot8 = 0x4105a0：写 [esi]=0x7e1f50 [esi+4]=0x7e1f34 [esi+8]=0x7e1f2c [esi+0xc]=0x7e1f24，再 call 0x7c8b3d

## 要求（一条命令一次性输出全部证据，禁止拆成多次单点命令磨预算）
把全部脚本写在 /home/t628/projects/ra2-campaign-forge/_r216/ex1_field.py，产物写 _r216/ex1.json 与 _r216/ex1_out.txt。

防 OOM 硬红线：严禁对整个 .text(约 4MB) 一次性 capstone md.detail=True 的 md.disasm()。只允许：
  (a) 用 md.disasm_lite()（detail=False）做全段线性扫描；或
  (b) 按 <=64KB 分块迭代并及时 del 释放；
仅对最终命中的少数地址单独开 detail=True。任何后台命令都带 timeout。

要做的事：
1. 解码 0x4a1d50 与 0x4a1ca0 两个函数的完整函数体（逐指令打印 mnemonic+op_str），给出：
   - 各自参数个数（看 ret imm 与读的 [esp+X]）
   - 是否写 [ecx+0x10] / [ecx+0x20]，写入宽度（byte/dword）
   - 体内是否有其它全局或字段访问
2. 定位 0x4a1d50 与 0x4a1ca0 的前缀（函数起始边界可用 .text 内最近的 0xCC/0xC3 之后，或直接以给定地址为起点最多扫 200 字节并在 ret/jmp 处停止；如实说明使用的边界规则）。
3. 全 .text 扫描 call 0x4a1d50 与 call 0x4a1ca0 的站点数（字节口径：E8 rel32 目标等于该地址），列出站点地址与所属函数近似起点（用「<= 位点的最近 vftable 槽目标」或最近的 0xCC 填充边界，二选一，写明规则）。
4. 全 .text 扫描 mov/xor/and/or byte ptr [reg+0x20] 与 dword ptr [reg+0x10] 的命中数（分两类计数）：
   - 0x20 byte 读/写：分别统计 mnemonic 是 movzx/mov/test/cmp（读）与 mov（写）
   - 0x10 dword：统计 mov reg,[reg+0x10] 与 mov [reg+0x10],reg
   给出前三类 top10 站点地址清单（地址+mnemonic+op_str）。
5. 正反控自测（必须写进脚本并打印 PASS/FAIL）：
   - 正控：已知 mov dl,byte ptr [ecx+0x20] 存在于 0x410456 → 扫描必须命中该地址。
   - 正控：已知 call 0x4a1d50 存在于 0x41041e、call 0x4a1ca0 存在于 0x410429 → 扫描必须命中。
   - 反控：把 0x20 改成 0x24 或把 0x10 改成 0x14 再扫，命中集合必须与 0x20/0x10 不同（打印两个基数即可证明判据不是恒真）。
   - 反控：把 call 目标改成 0x4a1d51 再扫，命中数必须为 0。

## 输出格式（最终回答）
一段 markdown，含：函数体逐指令清单、ret imm、写入宽度结论、三个扫描的基数与 top10、正反控 PASS/FAIL 行。所有数字必须是脚本实测值，不得估算或留空。
