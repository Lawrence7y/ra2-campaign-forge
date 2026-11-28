# R215-EX1 — 虚槽 +0x48（slot18）27 个落点的函数族归因（只读取证）

## 背景与边界

R214 已实测：视图 1214 张、槽 14044 个；槽数 > 18 的视图 137 张（主 125 / 次 12），slot18 目标 distinct 27。R214 **只给了落点分布与复用度，未做函数族归属**。本卡就补这一块。

只读。禁止修改任何业务文件（R14_COMMON.md / 台账 / STATUS_BOARD.md / FACT_INDEX* / check_disc.py / *_cards 以外的任何文件）。只允许写 _r215/ex1.json 与 _r215/ex1_out.txt。

## 输入（只读）

- 二进制：/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe（ImageBase 0x400000）
- PE 映射助手（可直接 import）：/home/t628/projects/ra2-campaign-forge/_r185/pe185.py
  - 提供 P.RAW（全文件字节）、P.B[段名]（含 lo / rawptr / rawsize / hi_file）、P.dw(va)、P.where(va)、P.r2o(va)、P.cstr(va,n)
- 视图表重建口径（照抄 R214 已验证口径，必须复现出同样数字再往下做）：
  1. COL（class object locator）候选：在 .rdata/.data 里逐 dword 扫描，条件为
     w[k] <= 2 且 w[k+2] == 0 且 P.where(w[k+3]) == '.data' 且 P.where(w[k+4]) == '.rdata' 且 P.cstr(w[k+3]+8, 512) 以 . ?A 开头（无空格）、以 @@ 结尾。
     记录 COLA[coladdr] = (mdisp=有符号 w[k+1], ptd=w[k+3], pchd=w[k+4], name)。
  2. 视图起点：对每个 coladdr，收集所有满足 w[j] == coladdr 且 P.where(w[j+1]) == '.text' 的位点地址（前驱位点）；**只有唯一前驱位点**的 COL 才算视图，视图起点 = 前驱位点 + 4。
  3. 槽序列：从起点按 dword 前进，直到（a）下一个视图起点，或（b）P.where(dword) != '.text'，最后一个视图的 end 用 .rdata 段的 hi_file。
  4. 类名去掉名字首字符的点。
- 必须先用上面口径算出并断言：视图 1214、主视图(mdisp==0) 954、次视图 260、槽总数 14044、distinct 槽目标 6692、槽数>18 的视图 137（主 125 / 次 12）、slot18 distinct 27。**任一条对不上就停下写 FAIL，不要继续推断。**

## 要测的 5 组（全量输出，不许抽样）

### G1 · 27 个落点的目标准入性
对每个 slot18 目标地址 T（27 个），用 capstone 反汇编**从 T 起最多 12 条指令**，输出：
- 首 3 条指令的 地址/字节hex/助记符/操作数
- 该地址是否"函数入口"证据三选一并给原始字节：
  - prev_ret：T-1 字节是 0xc3 或 0xc2
  - prev_pad：T-1 起往前连续 0x90 或 0xcc ≥1 字节
  - none：以上都不是（给 T-8..T-1 的 hex）
- .text 内以 e8 rel32 直接 call 到 T 的位点数量。**必须用逐字节扫 e8 + 手工算 rel32 的方式统计（不要用 capstone 全段线性反汇编）**，并且对最多 5 个命中位点用 capstone 单条 disasm(count=1) 复核确实是 call 到 T。
- 该地址作为 vftable 槽值出现的总次数、出现在哪些槽号（全部列出，不要只给前几个）。

### G2 · 类族归因
对每个 T：列出**全部**把它放在 slot18 的类名（去首点，原样输出完整修饰名），并给出：
- 类名个数
- 这些类名的**公共 token**：把类名里 ?AV / @@ 之外的标识符按大写字母边界与下划线切分，统计这些类共有的 token（出现在 ≥2 个类名里才算），按出现次数排序取前 8。**没有公共 token 就写 none，不许编造语义。**
- 这些类**是否还共享别的槽**：对每个 T，检查它的这组类的主视图，除 slot18 外还有哪些槽号是"这组类全同值"的；给槽号列表（最多 10 个）和各槽的同值目标。

### G3 · slot18 复用是否独立于视图整体复用
- 统计：137 张有 slot18 的视图，按 (slot0, slot1, slot2) 三元组聚簇，有多少个不同三元组、最大簇多大。
- 在同一 (slot0,slot1,slot2) 簇内的视图，slot18 是否相同？给出：簇数、簇内 slot18 一致 / 不一致的簇数。
- 反控：把判据换成 (slot0, slot1) 二元组、slot0 单元组各重算一次，看"一致性"比例如何随前缀长度变化。**如果单元组和三元组的一致性一样高，说明 slot18 一致性不是独立信息，必须如实写出来。**

### G4 · 纯桩 0x4c9150 的定位
0x4c9150 在 R214 里被判为纯桩（xor eax,eax ; ret）。对它输出：
- 作为槽值出现的全部位点：视图（起点 + 类名 + mdisp）与槽号，共多少条
- 槽号分布直方图
- 它在 slot18 上出现的 9 张视图分别是谁（类名 + mdisp + 视图起点）
- 用 capstone 确认它的字节确实是 33 c0 c3（给 hex）

### G5 · 反控（正反双向）
- 正控：把同一套统计跑在 slot17 与 slot19 上（视图数 141 / 137）。输出它们的目标 distinct 数、以及"目标出现在 slot 号仅此一个 vs 也出现在别处"的比例。
- 反控：随机取 20 个**不**在 slot18 出现、但在别处出现过的 .text 地址，做同样的"类族归因"，看是否也常出现"多类共享"现象。**这是为了判断『多类共享同一 slot18 目标』是否稀有。**
- 断言：本卡所有数字都要能从脚本一次跑出，脚本里每个数字都 print 出来。

## 输出格式

_r215/ex1.json，顶层结构：

{
  "assert_views": 1214, "assert_main": 954, "assert_sec": 260,
  "assert_slots": 14044, "assert_distinct": 6692,
  "assert_has18": 137, "assert_d18": 27,
  "G1": [{"t": "0x004104c0", "ins": [...], "entry": "...", "prev_hex": "...", "callers": 0, "caller_ok": 0, "slot_occ": 56, "slot_positions": [18]}],
  "G2": [{"t": "...", "classes": [...], "nclass": 0, "common_tokens": [...], "shared_other_slots": [{"slot": 0, "target": "0x...", "n": 0}]}],
  "G3": {"clusters_3": 0, "max_cluster": 0, "same18_3": 0, "diff18_3": 0, "clusters_2": 0, "same18_2": 0, "clusters_1": 0, "same18_1": 0},
  "G4": {"stub": "0x4c9150", "bytes": "33c0c3", "total_occ": 0, "pos_hist": {"0": 5}, "as_slot18_views": [...]},
  "G5": {"c17": {...}, "c19": {...}, "rand20_multi_class_share": N}
}

_r215/ex1_out.txt：把上面每个数字逐行 print（含断言行 PASS/FAIL）。

## 纪律

- **防 OOM 硬红线**：严禁对整段 .text 开 md.detail=True 做 md.disasm()。全段扫描只用逐字节 e8 匹配 + 手工算 rel32，或者 md.disasm_lite()；只对命中的个别地址用 md.disasm(..., count<=12)。脚本外层加 timeout 600。
- 一条命令跑完全部证据（脚本一次跑出，不要拆成多次单点命令）。
- 数字先实测再填，**禁止预估、禁止四舍五入到好看**。
- 所有"解释"必须与数字分栏写：先列数字，再给一句解释；解释里出现"因为/说明"的，必须指明是哪一条数字支撑。
- 若某项做不出来，写 "status": "unsupported" 并说明卡在哪一步，**不许编造**。
- 卡面与输出文件里不要用反引号包裹命令；命令用普通缩进代码块。
