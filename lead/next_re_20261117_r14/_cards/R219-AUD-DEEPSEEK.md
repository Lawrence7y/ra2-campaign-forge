# R219-AUD 只读跨家族复核（deepseek 审计员）

## 角色
只读审计员。**不要修改任何文件**，只做独立复算并给出 PASS/FAIL 与差异。
工作目录 /home/t628/projects/ra2-campaign-forge 。可用 python3 + capstone + _r185/pe185.py。
你自己的脚本请写到 /tmp/ 下，**不要写进项目目录**。

## 环境要点（必须照做，否则口径会错）
- 只读模块：sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge'); import _r185.pe185 as P
  P.B['.text'] 有 lo/rawptr/rawsize；P.RAW 是全文件字节；P.dw(va)；P.where(va)；P.cstr(va)。
- **关键口径**：capstone 必须设 md.skipdata = True，并按「逐字节 resync」推进：
  用一个 while 循环，每步对 raw[pos:pos+16] 调用 md.disasm_lite(...) 取第一条，
  pos += 该指令长度；若一条都解不出则 pos += 1。**不要**按固定 64KB 切块后每块从头重启
  （那样会得到 1150117 条而不是正确的 1394186 条）。
- 防 OOM：不要对整段 .text 开 md.detail=True 一次性 md.disasm()。

## 待复核的 8 项数字（主会话实测值）
1. 逐字节 resync sweep 的指令总数 = 1394186，末指令地址 = 0x7e0fff。
2. 接受集「call/jmp 的 mem 操作数、基址 ∈ {eax,ebx,ecx,edx,esi,edi,ebp}、无索引寄存器」计数 = 18935。
3. 上述接受集里基址是 esp 的计数 = 9（即含 esp 共 18944）。
4. 上述接受集里 disp 为负的位点 = 2 个，地址 0x556519 与 0x7dca83。
5. 含索引寄存器（形如 [reg+reg*scale+disp]）被排除的 call/jmp 计数 = 391。
6. disp//4 >= 256 的位点数 = 931，distinct 值 = 91。
7. 其中 256 <= disp//4 < 344（UnitClass 域）的位点数 = 925；top s 依次 288:309 / 289:85 / 337:73 / 342:58 / 258:44。
8. 把 925 个位点按「调用方函数入口」归并（规则：位点前 256 字节内最近的 >=2 连续 0xCC 填充，
   取填充后第一个字节；否则向前找最近的 0xC3 ret 之后第一个非 0xCC 字节；都找不到记 unresolved），
   得到函数数 = 311，unresolved 位点数 = 528。

## 待复核的 6 项定性结论（给 PASS/FAIL 即可，判据自己写）
C1. 0x7bea07 = call dword ptr [esi + 0x784]；0x7bea0f = [esi + 0x788]；
    0x7c2f17 / 0x7c301c = [esi + 0x77c]；0x7c37c7 = [esi + 0x780]。
C2. 全 .text 里对 +0x77c/+0x780/+0x784 这三个偏移的引用共 31 条，其中
    「mov dword ptr [reg+off], imm32」且 imm32 落在 .text 的写入端共 12 条。
C3. 同一组偏移还被 fmul qword ptr [reg+0x780] 用了 2 次、fstp qword ptr [reg+0x780] 1 次
    （证明这些偏移不是虚表槽而是对象内数据字段）。
C4. 0x7cde2b = call dword ptr [esi + 0x87c488]，其 esi 来源是
    0x7cddac lea esi,[edi+edi*2] 后接 0x7cddb6 shl esi,2，即 esi = edi*12，
    而 0x87c488 起是一张步长 12 字节的静态派发表（首项 0x87c488: 007ce046 007f97d0 0087c370），
    [0x87c488] = 0x7ce046 是 .text 函数。同时 0x7cdd08 cmp edi, 0x87c4c0 给出该表上界。
C5. 1218 张虚表中没有任何一张槽数 >= 480（最大 344）⇒ s=479/480/481/482 这 4 个「槽号」在
    全库不可能对应任何虚表槽。
C6. 0x877000 / 0x877010 / 0x87b17c / 0x87b18c 这 4 个「幻影虚表」地址：
    ① 全文件 .text/.rdata/.data 三段内 dword 引用它们的次数均为 0；
    ② 其前一个 dword（V-4）都是 0x00800040；
    ③ 0x877000 与 0x87b17c 的前 16 字节完全相同，0x877010 与 0x87b18c 的前 16 字节完全相同。

## 输出格式
一条命令产出全部结果（可以分两三条，但不要逐项试探）。
每条：编号 | 你实测值 | 与主会话值是否一致 | 若不一致给出你的值与你认为的差异原因。
最后单列「你发现的任何主会话口径问题」。所有数字必须实跑，禁止预估或照抄卡片数字后声称一致。
