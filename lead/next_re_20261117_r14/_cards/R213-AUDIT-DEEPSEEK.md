R213 跨家族只读复核卡（deepseek-v4.1-flash，role=audit，预算 50 轮，一次到位）

工作目录 /home/t628/projects/ra2-campaign-forge
目标 ra2bench/gamemd.exe（PE32，ImageBase 0x400000）
只读复核，禁止写盘到除 _r213/audit_deepseek.json 以外的任何路径。

本机可用：_r185/pe185.py（PE 映射：P.RAW 原始字节、P.B[段名] 段表、P.dw(va)、P.where(va)、
P.cstr(va)、P.r2o(va)）、python3-capstone。禁止对整段 .text 开 detail=True 全量反汇编。

待复核断言（逐条给 PASS/FAIL + 实测数字，禁止预估；算不出写 UNKNOWN）：

G1  COL 类头记录 1214 条。判据：+0 in {0,1,2}、+4 为 int32 mdisp、+8 == 0、+12 指向 .data 且
    .data+8 处是 .?A 开头 @@ 结尾的名字、+16 指向 .rdata。全部 1214 条的 +8 都为 0，
    +12 == 该记录 pTD、+16 指向的 .rdata 结构 +8 处为 numBaseClasses。
G2  vftable 定位：.rdata 与 .data 中「某 word 等于某 COL 地址、且下一个 word 落在 .text」的位点
    恰 1214 个，每个 COL 恰 1 个；vftable 起点 == 该位点 + 4（**不是** COL+4；COL+4 起连续
    .text 指针数在 1214 条上全部为 0）。
G3  vftable 槽总数 14044。其中 mdisp==0 的 954 条（主视图）合计 12726 槽，mdisp!=0 的 260 条
    （次视图）合计 1318 槽。主视图里 slot>=3 的槽合计 9958。
G4  mdisp 非零取值分布：4:91、8:78、12:78、24:6、36:1、40:1、44:1、1728:1、21784:3，合计 260。
G5  全部 1214 条 COL 记录（覆盖 954 个不同 pTD）的 pTD+0 恒等于同一个值 0x7f9594（distinct=1）。
    该 0x7f9594 处 dword 为 0x7c8ab7；0x7f9594+4 起是 ASCII 字符串 "Access violation - no RTTI data!"。
    即 TD+0 是共享 type_info 占位 vfptr，不能用作类视图判定。
G6  0x7c8ab7 反汇编前 4 条为 push esi / mov esi,ecx / call ... / test byte ptr [esp+8],1
    （scalar deleting destructor 形态）。
G7  0x6d1770 函数体：mov eax,[esp+4] / cmp eax,0x11c7 / jne ... / 索引全局 0xb0cc1c 到 int 数组
    0xb0cb78 / 范围检查 jl 0 与 jge 0x19（即上界 25）/ lea ecx,[eax+eax*2] / shl ecx,5（步长 96）
    / add ecx,0xb0c1c0 / test ecx,ecx / je / mov al,[ecx+0x2d] / test al,al / jne 回 / call 0x723ea0
    / mov al,1 / ret 8；第二分支 cmp eax,0x11c8 结构同构但 test al,al 后是 je（反向）并 call 0x723eb0；
    两分支都 ret 8；末尾 xor al,al / ret 8 为第三出口。
G8  0x723ea0 = mov eax,[ecx] / mov byte [ecx+0x2d],1 / jmp [eax+0x48]；
    0x723eb0 = mov eax,[ecx] / mov byte [ecx+0x2d],0 / jmp [eax+0x48]。
G9  0x11c7 与 0x11c8 在全 .text 的 4 字节字面命中分别为 2 处与 5 处，且 .rdata/.data 内命中 0 处
    （即不是 IID/GUID 常量，而是小整数消息 ID）。
G10 0x11c7 的 2 处命中的反汇编形态：0x6d1775 是 cmp eax,0x11c7；0x6379fb 属 push 0x11c7
    （0x6379fa 处 push 立即数的第 2..5 字节，即字面命中与指令边界错位）。
G11 0x7f9594 自身是否被任何 COL/TD 之外的数据引用、0x7f9598 字符串在 .text 内是否被 lea/push
    直接引用（给出命中数与地址；无则写 0）。
G12 onlysec 口径：TD 全集 988（.?AV 962 + .?AU 26），被 COL 引用的 pTD 954，差集 34（.?AV 10 + .?AU 24），
    34 条全部被 BCA 引用，其中 32 条只被 1 条 BCD 引用。

产出：把每条断言的实测值与 PASS/FAIL 写成 JSON 到
/home/t628/projects/ra2-campaign-forge/_r213/audit_deepseek.json
格式 {"G1":{"pass":bool,"values":{...}},...}。最后在回复正文给一张 PASS/FAIL 表 + 每个 FAIL 的原因。
纪律：一条命令输出一批证据（把能合并的断言合并进同一脚本），不要逐条试探。
