#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 E：V570 -> V571，把本轮两条新事实写进台账。

新增两条（不删不改既有 54 行，只在末尾追加，F01..F54 不动）：
  F55 [已证] vt == [obj] 对象模型的静态调用面实证（重同步口径）。
  F56 [流程] 指令级站点计数必须先声明扫描是否重同步：capstone disasm_lite 遇不可解字节
             是**返回**而非抛异常，分块线性扫描会在每块第一个坏字节处提前终止。

为什么必须新增 F56（否则本轮所有数字都不可复算）：
  R188 前三个中间版本（r188a / r188b / r188c）用的都是「64KB 分块、块内解到解不动、
  然后跳到下一块开头」。实测 62 块里 53 块提前终止，消费字节率 3,360,178 / 4,063,232
  = 82.70%，块尾字节根本没解码。于是同一条判据能报出三个互不相同的「站点总数」：
      64KB 分块不重同步      间接 call 19,482（esi 310）
      r188a 的十进制位移 bug  间接 call 18,520（esi 292）
      逐字节重同步（真 100%） 间接 call 22,731（esi 326）
  三个数都能自洽地报出来，但没有一个是「.text 上真实的站点总数」。
  同一缺陷也污染 vt 传播配对：不重同步 5,840 vs 重同步 6,965（差 1,125）。
  R186 的审计 #448 已指出过 82.70%（_r186/r186d D2a 断言 PASS），但只用来解释 C7 字节模式
  口径，**没有回头拦住指令级站点统计** —— 本条把这个缺口显式化。

写入纪律：wx 独占创建新版本目录文件 -> 断言旧 sha/CR -> 一次性写 -> 回读校验。
"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V570', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V571')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('Y1 旧 V570 = 151,027 B / sha 67c18703… / CR 0',
   len(raw) == 151027 and hashlib.sha256(raw).hexdigest().startswith('67c18703') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16], raw.count(b'\r')))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('Y2 56 段（1 表头 + 54 数据 + 1 空尾）', len(L) == 56, len(L))
rows = [l.split('\t') for l in L[:55]]
ck('Y3 每行 5 列', all(len(r) == 5 for r in rows), [r[0] for r in rows if len(r) != 5])
ck('Y4 既有 fact_id 为 F01..F54 有序', [r[0] for r in rows[1:]] == ['F%02d' % i for i in range(1, 55)],
   [r[0] for r in rows[1:]][-3:])

F55_STMT = ('gamemd.exe 的 vt == [obj] 对象模型在**静态调用面**上成立，实测（重同步扫描口径、'
 '.text 全 4,063,232 B 覆盖 100%）：① 间接 call 站点 22,731 个，基址分布 edx 9,852 / eax 6,715 / '
 '绝对址 3,832 / ecx 1,445 / esi 326 / edi 261 / ebx 163 / ebp 128 / esp 9（合计闭合）；'
 '② vt 传播配对 6,965 处：先 mov r32, dword ptr [esi] 把虚表指针从对象基址读出，'
 '在 32 条指令窗口内出现 call dword ptr [同一 r32 + disp]，且两者之间无任何指令写该 r32'
 '（9,128 个 mov r,[esi] 站点里 6,965 配到、2,163 未配到）；③ 全部配对与全部 [esi+disp] 站点的'
 '位移**无一例外 4 字节对齐**、无负位移、无 index（唯一 1 处带 index 的间接 call 是 '
 'esi*4 + 0x846840，不在配对集内）；④ 267 个配对位移逐个查槽可行性，**无一落在任何虚表都不存在的槽上**；'
 '⑤ 观测槽可达实现去重 6,523 / 全 vfunc 实现去重 6,692 / 全槽位实例 14,044（= 1214 张表槽数求和）；'
 '⑥ top6 槽的实现函数在**其出现的全部**虚表里都落在同一槽号（实现与槽号一一）：'
 '槽 2 → 0x410310（74 表）、槽 3 → 0x410210（76 表）、槽 4 → 0x410220（78 表）、'
 '槽 11 → 0x4E1570（20 表）、槽 18 → 0x4104C0（56 表）、槽 33 → 0x5F6BC0（15 表）；'
 '⑦ 槽 3 的实现 0x410210 前 16 字节 = 8b442404 8b50fc 8d48fc ff522c c20400，是**this 调整 thunk**：'
 '取 this → 从 **this−4** 读虚表指针 → this 减 4 作为新 this → 转调**槽 11** → ret 4；'
 '该 thunk 出现于 76 张表的槽 3，其中 72 张的槽 11 同为 0x410450、2 张为 0x410310、'
 '各 1 张为 0x512280 与 0x410260（集中度 94.74%）；⑧ 槽 4 的实现 0x410220 前 10 字节 = '
 '8b442404 8b400c c20400（mov eax,[esp+4] / mov eax,[eax+0xc] / ret 4），出现于 78 张表的槽 4，'
 '且这 78 张表的 COL.mdisp 字段**实测全为 4**。')

F55_LIM = ('口径：COL 枚举 = 在 .rdata 与 .data 里 4 字节步进取 5 连 dword d0..d4，要求 d0∈{0,1}、'
 'd2==0、d3 落 .data、d4 落 .rdata、从 d3+8 起读到以 .?A 开头且以 @@ 结尾的 C 串；'
 'vtable 枚举 = dword v 落 .text 文件范围且 (该处 −4) 的 dword 恰为某 COL 的 VA；'
 '实测 COL 1,214 / vtable 1,214，与 R186/R187 同口径可比。槽数 = 从 vtable VA 起逐 dword 前进'
 '（vt+0 即 slot0）直到取值不再落 .text 文件范围。**vtable 头是 [COL][slot0][slot1]…，'
 '即 COL 在 vt−4、slot k 在 vt+4k；R188 中间版本 r188b 把「x−4 是不是 COL」当作槽 k 的身份判据'
 '（应判 vt = x−4k 本身是否 vtable），该项已当场作废。** ⑥⑦⑧ 的「实现函数 ←→ 槽号一一」'
 '是**本次实测**（直方退化到单值），不是定义使然：「同一函数可出现在不同槽号」并未被枚举规则排除，'
 '反控 N5 把槽号 +1 后该断言即失败。⑦ 的「从 this−4 读虚表指针」与 ⑧ 的「COL.mdisp 全为 4」'
 '都只证形态自洽，**不证语义名**：0x410210 / 0x410220 / 0x410310 / 0x410450 / 0x4104C0 / 0x4E1570 / '
 '0x5F6BC0 七个函数的确切游戏语义名仍未取得。位移集合为**配对集**（267 个），不是全体间接 call '
 '位移集；两者不可互相代替引用。全部数字在本镜像 ra2bench/gamemd.exe（4,825,360 B）上实测，'
 '换镜像必须重测。⑦ 的槽 11 取值有 4 个不同值，其中 0x410310 同时是槽 2 的 top 实现 —— '
 '同一函数出现在两个不同槽号（槽 2 与槽 11）**确有其例**，故 ⑥ 的「一一」只对 ⑥ 列出的 top6 '
 '（其 top 实现）成立，**不得外推为「全镜像实现与槽号一一」**。'
 '证据脚本 _r188/r188d_resync.py（41 断言 0 FAIL）、日志 _r188/r188d.log、结果 _r188/r188d.json；'
 '槽位身份另由主会话独立第二实现（按 dword 反向 build impl→slot 映射，不复用 r188d 的槽枚举代码）'
 '逐值复现 1214/1214/14044/6692 与六组（实现, 出现表数, 槽号）三元组。')

F56_STMT = ('硬规则（指令级站点计数的前置条件）：报「全 .text 上某指令形态的站点数」之前，'
 '必须先声明扫描是否**逐字节重同步**。capstone 的 disasm_lite 遇到不可解字节是**返回**（既不抛异常、'
 '也不前进），因此「按固定块大小分块、每块内一直解到解不动、然后跳到下一块开头」的扫描会在'
 '每块第一个坏字节处**提前终止**，块尾字节根本没被解码；此时站点数**取决于分块大小**，'
 '不是镜像属性。')

F56_LIM = ('实测（本镜像）：64KB 分块不重同步 = 62 块中 53 块提前终止、消费字节率 3,360,178 / '
 '4,063,232 = **82.70%**、指令 1,197,422、间接 call 19,482；逐字节重同步（坏字节处前进 1 字节继续）'
 '= 坏字节 97 处、指令 **1,394,134**（多 196,712）、间接 call **22,731**（多 3,249）。'
 '同一缺陷污染指令配对类结论：vt 传播配对不重同步 5,840 vs 重同步 6,965（差 1,125）。'
 '因此**同一判据可以报出 18,520 / 19,482 / 22,731 三个都「自洽」的站点总数**——R188 的三个中间版本'
 'r188a / r188b / r188c 分别落在这三个数上（18,520 还叠加了「十进制位移未解析」的第二处错：'
 'capstone Intel 语法对 <10 的位移打十进制 dword ptr [esi + 8]、对 >=10 打十六进制 [esi + 0x44]）。'
 '本条与 F42（分母必须是指令边界上的真 call）和 F48（自报扫描规模必须给 .text 覆盖百分比）'
 '配套：F42 管「别拿字节命中当调用数」、F48 管「自报覆盖百分比」、**本条管「覆盖百分比怎么算出来的」**'
 '—— 只给百分比而不说重同步与否，仍不足以复算。已判定的边界：R186 审计 #448 曾指出 82.70%'
 '（_r186/r186d D2a 断言 PASS），但当时只用来解释 C7 字节模式口径，**未回头拦住指令级站点统计**；'
 '本轮把这个缺口显式化。不适用范围：按**字节模式**做的统计（如 C7 /0 的 imm 槽计数）不依赖解码，'
 '不受本条影响 —— 重同步与否得同一数。本条不判断任何既有事实的真假，只规定新站点计数的报数口径。')

rows.append(['F55', F55_STMT, '[已证]',
  'lead/next_re_20261117_r14/R14_COMMON.md;_r188/r188d_resync.py;_r188/r188d.log;_r188/r188d.json;_r188/r188c.log',
  F55_LIM])
rows.append(['F56', F56_STMT, '[流程]',
  'lead/next_re_20261117_r14/R14_COMMON.md;_r188/r188d_resync.py;_r188/r188d.log;_r186/r186d_audit_recheck.py;_r186/r186d.log',
  F56_LIM])

for nm, s in (('F55 stmt', F55_STMT), ('F55 lim', F55_LIM), ('F56 stmt', F56_STMT), ('F56 lim', F56_LIM)):
    ck('Y5 %s 无 tab / CR / LF / 半角双引号' % nm,
       '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s, '')
ck('Y6 F55 stmt 以句号结尾且 > 800 B', F55_STMT.endswith('。') and len(F55_STMT.encode()) > 800,
   len(F55_STMT.encode()))
ck('Y7 F56 lim 含 82.70% / 1,394,134 / 22,731 / 18,520 / 19,482 五个关键数',
   all(x in F56_LIM for x in ('82.70%', '1,394,134', '22,731', '18,520', '19,482')))

newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('Y8 新 CR == 0', nb.count(b'\r') == 0)
ck('Y9 新行数 = 58 段（57 行：1 表头 + 56 数据，另加 1 个空尾）', len(newtxt.split('\n')) == 58,
   len(newtxt.split('\n')))
ck('Y10 每行 5 列', all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:56]))
ck('Y11 前 54 行逐字节未动（只在末尾追加两行）',
   newtxt.split('\n')[:55] == TXT.split('\n')[:55])
ck('Y12 新体量 = 旧 + 两行（含换行）字节',
   len(nb) == len(raw) + sum(len(('\t'.join(r) + '\n').encode()) for r in rows[55:]),
   (len(nb), len(raw), len(nb) - len(raw)))
ck('Y13 fact_id 序列 = F01..F56',
   [r[0] for r in rows[1:]] == ['F%02d' % i for i in range(1, 57)])

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
back = open(NEW, 'rb').read()
ck('Y14 回读 sha 一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V571 = %d B / sha %s… / 56 数据行 / F55 lim %d B / F56 lim %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(rows[55][4].encode()), len(rows[56][4].encode())))
sys.exit(0)
