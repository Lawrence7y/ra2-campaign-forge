# 卡 R192 执行（独立脚本实测，hy4）

## 角色与边界
执行类。只读二进制，只写你自己的产物目录 _r192/exec/。
禁止碰 R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / FACT_INDEX* / R17_LEAD_BASELINE / _r185 之外的既有脚本。
不得复制主会话脚本代码形状，判据自己写。
项目根 /home/t628/projects/ra2-campaign-forge，二进制 ra2bench/gamemd.exe 只读。
可用 _r185/pe185.py 作 PE 映射（RAW / B / dw / where / r2o / cstr）。
OOM 红线：禁止对整段 .text 开 detail=True 的 md.disasm；最多对命中地址单独 disasm 少量字节。

## 前置枚举口径（可整段使用，已多轮复核）
T1 .rdata 与 .data 两段全 dword 扫描。一条 COL 记录是连续 5 个 dword 满足：
   d0 in {0,1}；d2 == 0；d3 落 .data 段；d4 落 .rdata 段；且 d3+8 处是以 .?A 开头、
   以 @@ 结尾的 NUL 结尾修饰名。记录地址 = 该 5 dword 的首地址。全镜像应得 1214 条。
   COL 字段：COL[0]=mdisp、COL[1]=pTD、COL[2]=pCHD、COL[3]=修饰名。
T2 vtable 枚举：两段里任一 dword 落 .text，且它前 4 字节是一条 COL 地址，则该位置是 vtable 头，
   该 dword 是槽 0。全镜像应得 1214 张表。
T3 槽数 nslot = 从表头起连续读 dword 直到取值不落 .text 为止的前缀长度。合计应得 14044。
T4 按 COL 名称分组应得 954 组，其中多表组 94 组。
T5 非主表 = COL.mdisp != 0 的表。它们的槽共 1318 个，其中
   「调整器」= 起始 4 字节形态为 83 6C 24 04 或 81 6C 24 04（sub dword [esp+4], imm），
   其余为「直接槽」，应得 1013 个。

## 你要做的事（一条命令一次跑完并输出 JSON）
Q1 对 1013 个直接槽 (vt, k, v) 逐个找同组兄弟表（同 COL 名称、不同 vt、且 k < nslot(兄弟)），
   归五类并给出计数：
   NOSIB（无任何兄弟表有该槽号）、SAME（兄弟同槽号值 == v）、
   THUNK_SAME（兄弟同槽号是调整器且其 jmp 目标是 v）、
   THUNK_OTHER（兄弟同槽号是调整器但 jmp 目标是别的地址）、
   DIRECT_OTHER（兄弟同槽号是直接指针且值 != v）。
   若兄弟表多于一张，按表地址升序取第一张有该槽号的兄弟并记录它的地址。
Q2 对每个 DIRECT_OTHER 对 (v, w) 做「跳板归并」：写函数 canon(addr)，反复跟随
   无条件跳转（E9 rel32 跳转；FF 25 绝对间址也可选跟）最多 8 跳，直到不再是无条件跳转。
   统计：canon(v) == canon(w) 的对数（叫 COLLAPSE）、canon 不同的对数（DISTINCT），
   以及 v 与 w 本身各自是否跳板的计数。请同时给出「只看 1 跳」与「最多 8 跳」两个口径的数。
Q3 给出 5 个具体槽的逐字节证据：表地址、槽号、两边的目标地址、两边目标起始 16 字节十六进制、
   两边 canon 结果、该槽所在两张表的 COL 名称与 mdisp。挑 COLLAPSE 与 DISTINCT 各至少 2 个。
Q4 对 0x410450 / 0x410580 / 0x410590 / 0x4C9150 四个地址各给：起始 32 字节十六进制、
   是否跳板（E9/FF25）、反汇编前 12 条指令文本（capstone，仅对这 4 个地址开 disasm）。
   另外统计这四个地址各自被多少个槽引用（全表全槽计数，含主表）。

## 输出与自检
- 产物写 _r192/exec/exec_r192.json，并在 stdout 打印每项计数。
- 每条计数必须来自实测；若与你预期不符，保留实测并在 JSON 里写明差异，不要调参凑数。
- 脚本必须带正反控：任选一个自造输入（例如把某 DIRECT_OTHER 的 w 换成 v）验证分类函数会改判。
- 预算内回合上限 20 回合；一次命令输出全部结果，不要拆成多次单点命令。
- 结束时报告：脚本路径、JSON 路径、各计数、正反控结果、以及你认为最可能出错的一处。
