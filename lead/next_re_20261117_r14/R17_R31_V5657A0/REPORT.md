D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe	73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R31-V5657A0 - 0x5657A0 定性报告

范围：纯静态只读；只读取上述镜像，不创建/调试/启动 gamemd 目标进程。入口与尾界均由可信入口集（.text 起点 + 全部 E8 目标 + 长填充后继）+ Capstone 严格解码得出；全文未用 C3/C2 字节扫定界。声明扫描：.text 4063232 B（4063228 个 E8 窗口），.rdata 200704 B，.data 442368 B，#73 查询区 1120 B；Q2 host 边界另严格解码 394123 B。可信入口数 17583。

## Q1 - 身份（vtable 定名）

不在任何 vtable 槽内。按 vtable[-4] -> COL -> +12 pTD -> +8 内联名 链重建：TypeDescriptor 988 个、COL 1214 个、可识别 vtable 1214 张，连续 .text 槽值共 14044 个；槽值等于 0x5657A0 的命中 0。.rdata 中 4 字节小端等于 0x5657A0 的裸命中也为 0。因此没有可逐字抄录的类名；未取得类名，结论仅为不是这张 RTTI 可识别 vtable 集合中的槽值。

## Q2 - 谁调用它

.text 内 raw E8 rel32 候选 1439 条；逐 host 严格解码后指令边界通过 1439 条，拒绝 0 条。完整 site/host 表见 callers.tsv，反汇编证据见 disasm.txt D 节。每个 host 由可信入口集定界，并断言 host <= site < host_anchor_end。

### 明确回答 #73（0x43F180）

[0x43F180,0x43F5E0) 内有 call 0x5657A0：该 1120 B 窗口 raw 命中 8 条，边界验证通过 8 条（不是假设；逐条见下表与 TSV）：

- 0x0043F210 - case1/3@0x43F1E9; [[this+0x520]+0xE58]!=0; result -> call [esi+0x1AC] (#107)
- 0x0043F2A7 - case1/3; #107 virtual call returned 0; placement loops active; result -> 0x47C620
- 0x0043F2C5 - case1/3; 0x47C620 returned nonzero; immediate cell re-lookup
- 0x0043F2EF - case1/3; 0x47C620 true and [cell+0x38] != [owner+0xE58]+0x294
- 0x0043F30B - case1/3; previous compare passed and [cell+0xEC] != 1
- 0x0043F39C - case1/3; [cell+0x48] != -1; coordinate loop, first lookup per coordinate
- 0x0043F3BF - same coordinate loop; second lookup after writing [cell+0x48]=-1
- 0x0043F587 - second expansion loop from 0x43F526; residual-coordinate lookup -> 0x486E70

所在路径（按控制流条件）：
- 0x43F19F: 0x6F4A70 returns 0 -> 0x43F5E0; no target call in queried range.
- switch case 0 -> 0x43F1CA: only 0x5687F0 then return; no target call.
- switch case 2 -> 0x43F9A6 and case >3 -> 0x43FAFC: outside queried range; no target call inside [0x43F180,0x43F5E0).
- case 1/3 with [[this+0x520]+0xE58]==0 -> 0x43F5EF; no target call in queried range.
- case 1/3 after call [esi+0x1AC] returns nonzero -> 0x43F5D8; no later target call in queried range.
- placement-loop zero counts skip nested 0x43F2A7..0x43F3BF group; gate/compare equalities skip deeper site(s) for that iteration.

因此不能说 #73 不调 0x5657A0；但也不能说 #73 只有 A 路径调它：上表 8 个 site 分属不同分支/循环，只有 0x43F2A7 的直接返回值被送入闸函数 0x47C620。

## Q3 - 函数体（只报字节可证）

- 入口：是。0x5657A0 本身是可信入口（存在直接 E8 目标）；前一可信入口 0x565730 严格解码至 0x565795 C2 04 00 ret 4，随后 0x565798..0x56579F 为 8 个 90，再进入 0x5657A0。没有按字节扫 C3/C2。
- 精确尾界：0x5657D8。唯一 ret 是 0x5657D5 C2 04 00 ret 4（3 B）；0x5657D8..0x5657DF 为 8 个 90，下一可信入口 0x5657E0。
- 函数长度：0x5657D8 - 0x5657A0 = 0x38 = 56 B；共 18 条指令，1 条 ret 出口。
- ret 形态：ret 4（C2 04 00），callee 弹回 1 个 dword 栈参数；同时 ECX 作为接收者使用，符合 thiscall 成员函数的字节形态。
- 读：[esp+4]（入参坐标结构指针）、[coord+0]、[coord+2] 两个 signed word；[ecx+0x13C]（表指针）；[table + index*4]；fallback 分支读 [coord] 的合成 dword。
- 写：仅全局 [0xABDC74]（fallback 分支写入合成坐标 dword）。未写接收者字段、未写坐标结构、未装 vtable。
- 字符串：无。常量/地址：0x40000（上界）、0xABDC50（返回值/fallback 对象地址）、0xABDC74（写入的全局）；未抄到 ASCII 原文。
- 索引/边界：index = ((signed16)[coord+2] << 9) + (signed16)[coord]；若 index 为负或 >= 0x40000，走 fallback；否则取表项，非 0 即返回该指针，为 0 也走 fallback。
- 全函数 18 行，已在 disasm.txt B 节整段列出（未省略）。

## Q4 - 与闸函数的关系 / 性质判定

判定：取某个对象的指针（具体是坐标到对象指针查找，失败回退到固定对象），不是惰性初始化，也不是单例访问器。强度：字节证据强；cell/tile 语义名为静态推断。

判据：
1. 0x5657BB mov ecx,[ecx+0x13C] -> 0x5657C1 mov eax,[ecx+eax*4] -> 0x5657C4 test eax,eax -> 非零直接 ret 4：返回的是从接收者成员表中取出的对象指针，不是接收者自身。
2. 无 test + new 模式，无 call operator new，无 ctor/vtable 安装；全函数 0 个 call（只有 1 条 ret 与条件跳转），所以不构成惰性初始化。
3. 不返回 [global]；0x87F7E8 只是调用方传入的 ECX 接收者（在 0x449476 / 0x43F2A2 等处装载），函数体只读 ecx+0x13C。全局 0xABDC74 是被写，不是被返回；返回的是固定地址 0xABDC50，属 fallback 对象指针。
4. 与闸函数关系：0x44947B 与 0x43F2A7 均是 mov ecx,0x87F7E8 -> call 0x5657A0 -> mov ecx,eax -> call 0x47C620，即本函数提供 0x47C620 的 this；0x43F210 的返回值则传给 call [esi+0x1AC]（#107）。这条链证明它被当作对象指针供应者，不证明它做初始化或单例创建。
