# R209 X1 · 独立复算：额外视图 vftable 的 IUnknown 三方法 this 调整三元组

你是执行员。**禁止读 /home/t628/projects/ra2-campaign-forge/_r209/ 目录**（本轮主会话产物），
必须从 ra2bench/gamemd.exe 自行重新推导，用你自己的脚本。

## 背景（只给方向，数字全部自己实测）
上一轮结论说「额外视图 vftable 的 slot0 是 this 调整 thunk（83 6C 24 04 imm8 E9 rel32）」，101 条。
本轮怀疑这个结论**口径过窄**：thunk 可能不是只在 slot0，而是占连续三槽（IUnknown 的
QueryInterface / AddRef / Release 三个方法），三个 thunk 的立即数都等于该视图的 mdisp。

## 必须实测并回答的 8 项（每项给数字 + 反控）
1. .text 段全域字节锚点计数：83 6C 24 04（后跟 imm8 再跟 E9 rel32）与
   81 6C 24 04（后跟 imm32 再跟 E9 rel32）各有几处？把每个地址列出来。
   注意 81 编码：E9 在 +8，rel32 在 +9..+12，落点 = va+13+rel32。
2. .rdata / .data / .rsrc 段做同样扫描应为 0 处（反控）。
3. 用如下判据重建 COL 记录集合（RTTI 对象定位器）：在 .rdata/.data 中按 dword 扫描，
   w[0]∈{0,1,2}、w[2]==0、w[3] 落 .data、w[4] 落 .rdata、且 cstr(w[3]+8) 是
   .?A...@@ 形状的名字。应得 1214 条。给每条的 mdisp=w[1]（有符号）。
4. 按 pCHD（w[4]）分组应得 954 组。每组的 vftable：在 .rdata/.data 中找所有等于 COL 地址的
   dword 位置 x，要求 dw(x+4) 落 .text，唯一者取 vt=x+4。应得 1214 张表。
   表长 = 从 vt 起连续、每个 dword 都落 .text 的槽数。给总槽数（应 14044）。
5. 统计：有多少张表的槽值本身是第 1 项里的 thunk 地址？给出这些表的
   (**slot0, slot1, slot2**) 三元组去重后有几个？每个三元组里 mdisp 是否唯一？
   三个槽的 thunk 立即数是否都等于该表 mdisp？给出 303/303 之类的精确分子分母。
6. 全部 thunk（70 个）里，被 vftable 槽引用的有几个？未被引用的有几个？
7. 三个 thunk 的 jmp 落点，分别反汇编首 16 条指令并给出函数末尾的 ret imm16 的立即数。
   统计：所有 slot0 落点的 ret 立即数集合、所有 slot1 落点的、所有 slot2 落点的。
   据此判断这三个槽是否对应 QueryInterface（3 个 dword 参数 ⇒ ret 0xc）/ AddRef（1 个 ⇒ ret 4）/
   Release（1 个 ⇒ ret 4）。若判断不了就说判断不了。
8. 有没有 thunk 出现在 idx>=3 的槽？如果有，列出 COL 地址、类名、mdisp、槽号、thunk 地址、
   以及该表完整槽列表。

## 输出纪律
- 一条命令跑完所有 8 项，输出到 _r209/x1_triple.json 与标准输出摘要。
- 必须带正控（人为构造一个已知 thunk 字节串，检测器要命中）与反控（非 .text 段必须 0）。
- **数字先实测再填，禁止预估、禁止照抄上面背景里出现的任何数字。**
- 报告格式：8 项逐项 PASS/FAIL + 你的实测数字。最后一行写 断言 N 项 / FAIL M 项。
- 严禁在卡面或输出里使用反引号。
- 严禁对整段 .text 开 capstone detail 模式一次性 disasm（会 OOM）；只对命中地址开小窗口。
