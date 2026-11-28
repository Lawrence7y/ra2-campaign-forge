# R214-EX2 · 多继承 adjustor 布局全表 + HouseClass 两处例外成因

## 目标
R213 律 X：260 张次视图里 101 张 slot0 是 this-adjustor thunk（sub dword ptr [esp+4], imm ; jmp rel32），imm 恒 == 该 COL 的 mdisp（101/101）。全体 adjustor 槽 305 个，303 遵式，2 例外 = ?AVHouseClass@@ 的 mdisp=40 次视图的 idx3/idx4（imm=4，jmp 0x4f6e60 / 0x4f6950）。

本轮把「每类的 mdisp 多重集 + 每个 adjustor 的 (idx, imm, mdisp, jmp_target)」全表算出，并重点证明 HouseClass 两处例外的成因（给出字节层面解释：那两个 jmp 目标是否本身就是 adjustor、是否落本类主视图槽、该 slot 指向是否等价于另一条 mdisp 记录）。

## 环境与纪律
- 工作目录 /home/t628/projects/ra2-campaign-forge，二进制 ra2bench/gamemd.exe。
- 复用 _r185/pe185.py（P.RAW / P.B / P.dw / P.where / P.cstr）。capstone 只对小窗口解码（每条 <= 16 字节，count<=8），严禁整段 .text detail=True。
- 一条命令跑完：python3 _r214/ex2.py > _r214/ex2_out.txt 2>&1；外层 timeout 900。结果另存 _r214/ex2.json。
- 全程正反控断言打印 PASS/FAIL 计数。

## 表重建口径（必须与 R213 完全一致）
COL：.rdata/.data 内 word 序列 w[k..k+4]，w[k] in (0,1,2) 且 w[k+2]==0 且 where(w[k+3])=='.data' 且 where(w[k+4])=='.rdata' 且 cstr(w[k+3]+8) 以 .?A 开头以 @@ 结尾。COL 地址 = 段基址+4*k，mdisp = int32(w[k+1])，名字 = TD+8 内联名去掉首个点。
前驱位点：word == COL 地址 且 下一 word 在 .text；vftable 起点 = 位点+4，slot i = 起点+4*i。
ADJUSTOR 判据：对槽地址 A，capstone 解 4 条以内指令，形如 (sub dword ptr [esp+4], imm) 后紧跟 (jmp rel32 或 jmp imm)。imm 取第一条指令立即数，target 取 jmp 目标绝对地址。

## 必答项
F1 规模自检：COL 数、CHD 数、主视图数、次视图数、主视图槽总数、次视图槽总数（应复现 1214 / 954 / 954 / 260 / 12726 / 1318，不一致立即报 FAIL 并停止后续依赖项）。
F2 adjustor 全表：全体 adjustor 槽数（应 305），按 (idx, imm) 聚合的计数表；遵式判定 imm==mdisp 的通过数与例外清单（地址、类名、mdisp、idx、imm、jmp_target）。
F3 每类 mdisp 多重集：把 mdisp 非零记录按类聚合，打印每类 (类名, mdisp 列表升序, adjustor 数) 的前 20 条与完整分布（按 mdisp 元组去重后计数），必须能看出 HouseClass 的 mdisp 元组。
F4 HouseClass 例外成因：给出 HouseClass 全部 COL 记录（地址、mdisp、vftable 起点、槽数），逐条打印两块视图的完整槽表（地址 + 值 + 该值前 3 条反汇编）；对 idx3/idx4 两个 adjustor 打印其 6 条原始字节 hex 与反汇编；说明 imm=4 与自身 mdisp=40 的差异，并核验 jmp_target 是否 (a) 落在本类任一视图槽内 (b) 本身是 adjustor (c) 与 imm=4 条记录的 slot0 同址。
F5 反控三点：① 954 张主视图内 adjustor 槽必须 0；② 全体 adjustor 的 jmp_target 必须全在 .text（不在 .text 的列出）；③ imm==mdisp 的反例只允许出现且仅出现 HouseClass 那 2 条，多一条即 FAIL 并列出。
F6 distinct 说明：打印 adjustor 槽型模板（去掉立即数后的助记符序列）的 distinct 个数与每个模板的计数（R213 报 7 种，若实测不同如实报）。

## 输出
ex2_out.txt 先规模自检，再按 F1..F6 分节，每节 PASS/FAIL + 数字；ex2.json 结构化存 adjustor 全表与 HouseClass 细节（限 200KB 内，长列表只存前 40 条 + 计数）。
