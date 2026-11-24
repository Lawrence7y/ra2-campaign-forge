# R114-AUDIT-METHOD — 攻击 R113 的三条新判据逻辑，专门找"看似成立实则不成立"

## 你的身份
跨家族审计员（hy4 家族）。你不是来复算数字的（另有执行员在做），你是来**攻击结论的逻辑**。
出题方（R113 主会话）宣称下面 4 条。逐条判 PASS / FAIL，FAIL 必须给**反例的具体地址与字节**。

## 材料（只读）
- 镜像 /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 出题方产物 /home/t628/projects/ra2-campaign-forge/_r113/*.json 与 _r112/*.json
- 出题方的脚本 /home/t628/projects/ra2-campaign-forge/_r113/*.py、_r112/r112b_qi_offset.py
- 注意：出题方的产物只当线索，**当证据用的必须是你自己反汇编出来的**

## 待攻击的 4 条

### A1「链 F：.rdata 全量 vtable 普查 1214 张，954 与 symbols.json 重合、260 是新增」
判据：某 .rdata 槽的值 v 满足「v−4 处是合法 COL」⇔ v 是 vtable 起点。
合法 COL = COL+0==0、COL+0x0C 的 pTD 名字以 .?A 起头、COL+0x10 的 CHD 里 nbc∈[1,96]、
BCD 每项 pTD 合法。
请验证：
1. 这个判据会不会**漏收**？即存不存在真实 vtable 但 v−4 处不是这个形态的？
   （提示：多重继承下 vtable 前面的 4 字节是什么？piTable 可以为 -1 吗？）
2. 会不会**多收**？即存在满足判据但不是 vtable 的槽（比如某个结构体里恰好放了个指向
   合法 COL 的指针）？给地址。
3. 260 张新增里，12 张 offset==0 出题方说是「12 个 Locomotion 类的主 vtable，symbols.json 口径缺陷」。
   请独立核：这 12 张与 symbols.json 已收的那 12 张是不是同一 TD 的两个 vtable？
   symbols.json 那边记的 offset 真的是 4 吗？

### A2「链 G：QI 闭包认领集修了 R111/R112 的漏抽」
闭包定义：closure(f) = ⋃cmpsd(体(f)) ∪ closure(thunk-jmp 目标) ∪ closure(call 目标, 深 2)。
出题方说闭包不虚增，理由是两处 call 点的成功路径都是"直接返回"形态：
- 0x414290: test eax,eax ; jge 0x4142e9(ret)
- 0x4af720: cmp eax,0x80004002 ; jne 0x4af777(ret)
请验证：
1. **这是最容易出错的地方**：call 返回成功（jge / jne 成立）时直接 ret，
   那么"调用者能 QI 成功到被调者认的 IID"这句话成立吗？
   调用者把 eax（被调者返回值，S_OK）返回给外部，但外部请求的 IID 已经被被调者匹配了，
   **所以外部确实能成功**。但反过来：调用者自己的 cmpsd 在**失败路径**上，
   这条路径上外部请求的是别人的 IID。请判断：闭包把被调者的全套 IID 都算给调用者，
   **是否等价于"调用者对这些 IID 也返回 S_OK"**？如果不是，闭包就是虚增。
2. 出题方报 Q(0x7f7c70) 从 83→90（+7）。你算 +几个？
3. 闭包深度 2 是否有上界依据？深度改成 3 会不会继续增长？（若会增长，深 2 就是任意选的值）

### A3「链 H：接口方法表槽数是接口属性；10 接口违例 0」
出题方用 T 尺（连续落在 .text 的 dword 数）量 COL.offset != 0 的真子对象 vtable，
得 10 个接口各自单值（INoticeSink=1/81类，ILocomotion=50/12类 …）。
请验证：
1. T 尺是"连续落在 .text" —— 这个量的**上界**是什么？会不会把一个返回常量指针的
   "尾巴数据"也算进槽里（即某个槽值恰好是 .text 内的地址但不是方法）？给例子。
2. 出题方这 10 个接口**不含** 0x7f7c70/0x7f7c80（它们的 COL.offset==0）。
   那么 A3 能回答"IPersistStream 有几个方法"吗？明确判：证成了什么、没证成什么。
3. 反控①「按 CHD 组内序号错位索引 ⇒ 3 接口不再恒定」：这个反控**可能失败**吗？
   如果你能构造一种错位方式让 10 个接口仍然全恒定，那这个反控就没牙。

### A4「R113 报 max B=1820，R112 报的 256 是饱和值」
出题方说最后一组 COL 没有「下一个 COL 指针」，所以 B 尺记无上界并排除，
初稿 23287 是人造值。
请验证：
1. .rdata 的最后一个 COL 指针地址是多少？它后面还有多少字节？
   出题方用段尾 0x811074 当边界算出 23287，你算出来是多少？
2. R112 的 r112c_subobj.py 里那个 256 是硬编码上限吗？看源码判定（给行号）。
3. 排除末组后 max B 真的是 1820 吗？

## 输出
- /tmp/r114audit/VERDICT.md：A1..A4 逐条 PASS/FAIL + 反例地址字节
- /tmp/r114audit/verdict.tsv：列为 item / verdict / counterexample_addr / reason
- 判 FAIL 的条目必须能在镜像里指出具体字节，否则改判 PASS 并说明"只是措辞不严谨"

## 纪律
- 不许为了挑错而挑错；也不许因为"看起来合理"就 PASS。
- 每条 PASS 必须写出你自己验证的那一步（命令或脚本路径）。
- 只写 /tmp/r114audit/。不许改 _r113/_r114 下任何文件。
- 反汇编一律 disasm_lite、分块；严禁整段 detail=True；后台脚本带 timeout。
- 单次运行 8 分钟内出核心判定。
