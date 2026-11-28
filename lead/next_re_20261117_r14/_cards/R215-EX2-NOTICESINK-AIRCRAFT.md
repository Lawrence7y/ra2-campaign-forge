# R215-EX2 — INoticeSink 8/21784 双偏移选择规则 + AircraftClass mdisp=1728 三条 adjustor 对应（只读取证）

## 背景与边界

两个 R214 遗留问题，都要求"地址 + 字节 + 交叉引用"的可复算证据：

- 问题 A：?AVINoticeSink@@ 被以 mdisp=8 与 mdisp=21784 两个偏移引用。是什么规则选择了其中一个？（21784 这个数在 R214 里也出现过：MouseClass / TabClass / ScrollClass 的次视图 mdisp 也是 21784）
- 问题 B：?AVIAircraftClass@@ 有 3 条 8 字节 sub dword ptr [esp+4], 0x6c0 adjustor（槽位 0x7e2250 / 0x7e2254 / 0x7e2258），目标是 0x7e2250 系列。要确认它们与哪个目标视图的哪个槽号对应。

只读。禁止修改任何业务文件。只允许写 _r215/ex2.json 与 _r215/ex2_out.txt。

## 输入（只读）

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe（ImageBase 0x400000）
- PE 映射助手：/home/t628/projects/ra2-campaign-forge/_r185/pe185.py（P.RAW / P.B[段名] / P.dw / P.where / P.r2o / P.cstr）
- 视图表重建口径：与 R214 相同（COL 候选 = 五个 dword 满足 w[k]<=2、w[k+2]==0、where(w[k+3])=='.data'、where(w[k+4])=='.rdata'、名字 . ?A...@@（无空格）；只有"唯一前驱位点"的 COL 才是视图，视图起点 = 前驱位点 + 4；槽 = 连续 .text 指针直到下一视图起点；nom 去首点）。
- 必须复现并断言：视图 1214 / 主 954 / 次 260 / 槽 14044 / distinct 6692。对不上就写 FAIL 停下。

## 问题 A · INoticeSink 双偏移

1. 输出 ?AVINoticeSink@@ 的**全部视图**：视图起点、COL 地址、mdisp、槽数、slot0 值、以及完整槽列表的 hex。
2. 找出所有**指向** ?AVINoticeSink@@ 任一视图里的**某个槽**的 adjustor 桩（形如 sub dword ptr [esp+4], IMM 后紧跟 jmp rel32）。对每一条输出：
   - 桩地址、完整字节 hex（前 16 字节）、IMM、jmp 目标地址
   - jmp 目标落在哪个类哪张视图的哪个槽号（用槽表反查，**必须给出命中的视图起点 + 类名 + mdisp + 槽号**；命中多张/多槽就全列）
   - 该桩本身是不是某个视图的槽值？若是，是哪张视图的哪个槽号
3. 明确回答：mdisp=8 与 mdisp=21784 这两个数分别出现在**哪些位置**（是 COL 里的 mdisp 字段、还是某条 adjustor 的 IMM、还是某处 vftable 的偏移常量的立即数）。给出每一处的 地址 + 字节 hex。
4. 给出**选择规则的可检验表述**：比如"某类的某槽只有 IMM 等于『目标视图 mdisp − 本视图 mdisp』时才成立"。用全体数据检验：把 T628 已定稿的律 X（IMM == mdisp_self − mdisp_target）套到 INoticeSink 相关的每一条 adjustor 上，逐条给 是否成立（成立/不成立 + 两边数字）。**不成立的要单列，不许藏。**

## 问题 B · AircraftClass 三条 8 字节 adjustor

1. 输出 ?AVIAircraftClass@@ 的**全部视图**：视图起点、COL、mdisp、槽数。
2. 输出 0x7e2250 / 0x7e2254 / 0x7e2258 这三个地址的**完整字节 hex（各 16 字节）**与 capstone 反汇编（count=3）。
3. 判定这三个地址分别是什么：是 vftable 里的普通函数指针槽？是 adjustor 桩本体？还是别的？依据必须是字节（例如桩体应是 83 6c 24 04 c0 06 00 00 + e9 rel32 共 13 字节 —— 请实测给出真实字节，别照抄我这个猜测）。
4. 用槽表反查：0x7e2250 / 54 / 58 是否出现在任何视图的槽序列里？若出现，给视图起点 + 类名 + mdisp + 槽号；若不出现在任何槽序列里，说明它们在视图起点之前还是之后的哪个空隙，并给该空隙的边界（前一个视图起点的槽数、下一个视图起点）。
5. 那 3 条 adjustor 的 jmp 目标分别落在哪张视图的哪个槽号（同 A.2 的反查方式），并检验律 X：IMM(=0x6c0=1728) == mdisp_self − mdisp_target 是否成立。

## 输出格式

_r215/ex2.json：

{
  "assert_views": 1214, "assert_main": 954, "assert_sec": 260, "assert_slots": 14044, "assert_distinct": 6692,
  "A": {"views": [{"start":"0x..","col":"0x..","mdisp":8,"nslots":0,"slot0":"0x..","slots":["0x.."]}],
        "adjustors": [{"stub":"0x..","bytes":"..","imm":0,"jmp":"0x..","landing":[{"view":"0x..","class":"...","mdisp":0,"slot":0}],"as_slot_of":[{"view":"0x..","class":"...","slot":0}]}],
        "mdisp8_sites": [...], "mdisp21784_sites": [...],
        "lawX": [{"stub":"0x..","imm":0,"self":0,"target":0,"ok":true}]},
  "B": {"views": [...], "addr": [{"a":"0x7e2250","bytes":"..","ins":[...],"kind":"..."}],
        "in_slot_table": [...], "adjustors": [...], "lawX": [...]}
}

_r215/ex2_out.txt：逐行 print 全部数字与断言 PASS/FAIL。

## 纪律

- **防 OOM**：不许对整段 .text 开 detail 做全量 disasm；只对命中地址用 md.disasm(..., count<=3)。脚本外层 timeout 600。
- 一条命令跑完全部证据。
- 数字先实测再填，禁止预估。
- 问题 A.4 与问题 B.5 是**判决性**结论：只能写"在 N/N 条上成立 / 有 M 条不成立"，不许写"基本成立"。
- 卡面与输出里不要用反引号包裹命令，命令用普通缩进代码块。
