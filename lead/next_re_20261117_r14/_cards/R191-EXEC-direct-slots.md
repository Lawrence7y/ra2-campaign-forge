# 卡 R191 执行（hy4flash，独立脚本实测）

## 角色与边界
只读 + 自建脚本。不得修改任何既有文件（R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md /
FACT_INDEX* / R17_LEAD_BASELINE / _r185 / _r189 / _r190 一律只读）。
你只在 _r191/exec_hy4/ 下写自己的脚本与输出（目录已存在，直接写即可）。
禁止运行 gamemd.exe，禁止任何动态取证。
OOM 红线：禁止对整段 .text 开 capstone detail=True 的 md.disasm；全段线性扫描
只能用 md.disasm_lite 或 64KB 分块流式迭代。单条命令加 timeout 300。

## 环境
项目根 /home/t628/projects/ra2-campaign-forge，目标二进制 ra2bench/gamemd.exe（只读）。
可 import _r185/pe185.py 拿 PE 映射（RAW / B / dw / where / r2o / cstr / sec_of），
也可自己解析 PE 头。可用 python3-capstone、python3-pefile。
判据必须自己写，不要复制 _r190/r190a_groups.py 或 _r190/r190b_thunks.py 的代码形状。

## 已确立的前置事实（R185-R190 实测，直接可用，不要重测）
F1 .rdata/.data 里有 1,214 条 COL 记录、1,214 张 vtable，块紧排
   [COL 指针 4B][槽 4k B]，槽位实例合计 14,044。
   枚举判据：位置 b 的 dword 落 .text 且 b-4 处 dword 是一条 COL 地址；
   COL 判据：5 个 dword 满足 d0 in {0,1}、d2 == 0、d3 落 .data、d4 落 .rdata
   且 d3+8 是 .?A 开头 @@ 结尾的修饰名。
F2 按 COL 里的修饰名分组得 954 组，其中 94 组含多于 1 张表。
F3 非主表（COL 第二字段 mdisp != 0）共 1,318 槽，其中 305 个是
   sub dword ptr [esp+4], K ; jmp target 形式的调整器 thunk；另 1,013 个是
   普通函数指针（直接槽）。
F4 305 个 thunk 的 jmp 目标恒落在同组另一张表的同槽号，且
   K == 本层 mdisp 减目标层 mdisp（305/305）。
F5 1,013 个直接槽里，与「同组基类表同槽号的值相同」的实测为 0 个。

## 本轮要你实测的两件事

### D1 这 1,013 个直接槽到底是什么关系（主问题）
对每一个直接槽（宿主表 T、槽号 k、值 v）测下列四项，逐项给数：
D1a 在同一组内其它表的任意槽号上，值 v 是否出现？给出出现数、
    以及「同组内出现」的直接槽占 1,013 的比例。
D1b 把 v 作为函数入口，看它的前 24 字节与它所在编组的其它直接槽目标是否相同
    （即是否多个类共用同一个实现）。给出「直接槽目标去重后的不同地址数」，
    以及被 2 个以上直接槽共用的目标有多少个、最多的那个被几个槽共用、
    它被哪些类（修饰名）用。
D1c 对被 5 个以上直接槽共用的目标（若有，取前 5 个），各打印 24 字节原值
    与 va，并给出这些目标的功能形态判读（只看字节：ret N 常量、读 this 偏移、
    是否调虚函数 thunk 等），不要猜游戏语义名。
D1d 直接槽的值 v 是否也出现在「主表」（mdisp == 0 的表）的任意槽号上？
    给出现数。这一项用来区分「覆盖实现」与「默认实现复用」。

### D2 四个 mdisp 档为何不生成副表
R190 实测 PMD.mdisp 有 14 个取值 {0,4,8,12,24,36,40,44,172,176,240,248,1728,21784}，
而实际虚表层偏移只有 10 个（多的四档是 172 / 176 / 240 / 248）。
D2a 指名这四档各属于哪些类（修饰名 + COL 地址），每档列出全部条目
    （172 档 8 条 / 176 档 4 条 / 240 档 25 条 / 248 档 25 条）。
D2b 对 StageClass、BounceClass、FlasherClass 三个类，打印它们的 COL 5 个 dword、
    CHD 5 个 dword、以及基类数组中每一条 BCD 的 4 个 dword（原值，十六进制）。
D2c 判定：这四档的条目所指向的 pTD 与 CHD 是否可读、其 attributes 字段是否
    带 non-virtual 标记（MSVC 里 BCD.attributes 的 bit0 = 非虚基类）。
    给出 attributes 的取值分布，并说明「有基类子对象但没有独立副表」
    是否与 non-virtual 基类标记一致。若数据不支持这个解释，如实说不支持。

## 输出要求（一次命令跑完，不要拆成多次试探）
写一个脚本 _r191/exec_hy4/d1d2.py，末尾打印 JSON 汇总，字段自定但要能对上
上面每个小问的编号。断言风格：每个小问至少一条硬断言（数等于实测值），
并在末尾打印 checks 数与 fails 数。全部数字必须是脚本实测，禁止先写期望值再断言。
最终回复请贴：JSON 汇总 + 关键原值行 + checks/fails 计数 + 你判定的结论一句。
