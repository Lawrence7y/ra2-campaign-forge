#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 J：看板归档 + 第 150 轮段写入。
判据（R138F）：写前行数 + 本轮追加 <= 300 才免归档；否则归档最早两段到 BOARD_ARCHIVE（ARC CR 保持 2952）。
"""
import hashlib, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead','next_re_20261117_r14')
B=os.path.join(D14,'STATUS_BOARD.md'); A=os.path.join(D14,'BOARD_ARCHIVE.md')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p, tag):
    b=os.path.join(BASE, os.path.basename(p)+'.before_'+tag+'.bak')
    fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return b

NEW = """## 🟢 R17 第 150 轮（2026-11-27 04:0x–05:0x）· FACT_INDEX 存活普查定版（54 行里零存活恰 F23，`[已证]` 队列存活项中位 2）；外部 triage 的 32 条被证为 v5.32 版本漂移而非漏项；F23 降级缺的是**裁定**不是理由

### 一 · 一句话

R149 留下的第一待办「F23 的 grade 二选一」有两个从未被独立验证的前提：零存活是否真的只有 F23 一行、外部调研的 32 条到底覆盖了什么。本轮把两条都做成可失败判据，并额外查清了「降级」这件事**可行性、必要性、成本**三件分开的事：可行性上盘上早有「未降级」的逐字处置、必要性被 13 行活体承载削弱、成本上门禁对 `FACT_INDEX` **结构性够不着**。

### 二 · 定版普查（v5.40 全 54 行逐行）

| 量 | 值 |
|---|---|
| 数据行 / 证据项 / 失联项 / 唯一失联路径 | 54 / 178 / 43 / 16 |
| 存活项 | 135 |
| 零存活行 | 恰 1 行 = F23 |
| 部分失联行 | 33 |
| grade | `[已证]` 27、`[流程]` 24、`未取得` 2、`[静态推断]` 1 |

**（1）增量在分布位置，不是计数本身。** R149 只说「恰 1 行」；本轮把 `[已证]` 27 行的存活项取值算成 `{0,1,2,3,4,7,28}`、中位 **2** ⇒ F23 的 0 是**同 grade 队列里的唯一极小值**，不是「已证行普遍如此」。这句话是 R149 那条结论真正缺的分母。

**（2）证据面没动，动的是分母。** v5.32 与 v5.40 的失联项数**同为 43**、唯一失联路径**同为 16** —— 两版之间变的只有 F35 的 `evidence_paths` 项数（1 → 5）。

### 三 · 外部 triage 的 32 条是版本漂移，不是漏项

`_ext/f_partial_triage/triage.py` 的 `FIX` 常量指向 **v5.32**（`R17_R104_FACTINDEX_V532`，`84863896…`，61,822 B），不是 v5.40。同一套判据下：

| 版本 | 证据项 | 零存活 | 部分失联 |
|---|---|---|---|
| v5.32（triage 的输入） | 171 | **2（F23 / F35）** | 32 |
| v5.40（现盘） | 178 | 1（F23） | 33 |

⇒ `现盘 33 − triage 32 = {F35}`、反向差集为空、`triage 32 == v5.32 部分失联集`（逐项相等）。**结论：triage 没漏项，它是按当时的盘做的；把它当 v5.40 口径引用会凭空多出 F35 一条。** 另复核它 91 个 `alive_paths` 点名件：**91/91 真在盘、0 失配**。

### 四 · 降级缺的是裁定，不是理由

三份权威件里「原件失联 ⇔ 降级」同句检索 **0 命中**；而盘上已有两次逐字处置：`LEAD_LOCK` **CX8**「`F23` 的 `[已证]` 在本库内零可核验证据，**未降级**（判据变更须单独裁）」、`R14_COMMON` **§2.149 八①**「本轮只登记、**未降级也未取得替代证据**（降级属判据变更，须单独裁）」；台账 **§1057** 更直接：「这不是降级，也不升格」。`grade` 轴在台账有 **16 处**「分级口径：」定义，其中 **15 处**指证据形态、**0 处**指「原件是否仍在盘」⇒ **grade 记的是建立时的证据强度**。故 R149 的「二选一」其实早被写成「须单独裁」——本轮只是把它从待办变成已确认的口径事实。

### 五 · 必要性被削弱：四计数有 13 行活体承载，但承载 ≠ 证据

`458 / 291 / 293 / 1,196` 在台账同行出现的严格 token 承载 **13 行**，其中 4 行自述「自行复算 / 两套独立实现」——**但实现目录 `R17_R41_RECOMPUTE` 不在盘、台账仍引用它 8 次** ⇒ **引用在、被引件失**。且 `39601` 自标「照录，不重算」、`47079 / 47083` 明写七式为定义式 ⇒ **不能用这些行给 F23 兜底（循环）**。这节只用于打折，不用于翻案。

### 六 · 成本：门禁结构性够不着

`check_disc.py` 对 `FACT_INDEX` / `FACTINDEX` / `R17_R1` 三模式**全 0 命中**，且 `os.walk` / `listdir` / `glob` / `scandir` **四原语全 0** ⇒ **没有任何目录遍历能力，换任何版本名都不会命中**。⇒「改 grade 须过门禁回归」在机械层面不成立（门禁沉默不是语义证据）；真实成本是 `fabd1e57` 的 **5 个真实独立载体**（台账 / `LEAD_LOCK` / `R14_COMMON` / 看板 / `COMPACT_STATE`）须同步。

### 七 · 规则 D 与两张卡

执行员 **#337（hy4, exec）succeeded** / 10 回合 / 1.43′ / 无 OVERTIME —— 六项与主会话逐项相同，另贡献**独有发现**：v5.32 阶段零存活是 **2 行**。审计员 **#338（deepseek, audit）failed `error_max_turns`** / 36 回合 / 5.37′ / **零输出**（如实登记，与 R145 #322 同族：宽卡超限）；改窄卡 **#339 succeeded** / 16 回合 / 2.93′。`#339` 七条主张 **六成立一打折**（「10 个文件引用 fabd1e57」→ 真实载体 5，含 3 symlink + 2 自造卡）；**它纠正了我一处**：它报承载 13 行、我报 11 行，复算后**是我错**。

### 八 · 自错 S-353..S-359（七条）

**S-353** 用「剥最后一对括号」解析嵌套锚点（`(§2.10 / 一 / (a′))`）致 2 项假失联 ⇒ 改按首个左括号切 + 整串回退，91/91 在盘。**S-354** 断言「分级口径 >= 20 处」实测 16。**S-355** 把 `LEAD_LOCK` 塞进「门禁必有引用」清单，实测 0。**S-356** 把「必须为假的反例」写成同一事实的重复否定（不是反例），改为换恒真判据看算法是否给 0 行。**S-357** 断言「『未降级』>= 5 次」实测 1。**S-358** 未查 symlink 即采信「10 个文件」。**S-359（最严重，方向错）** 把 `1,196` 的严格 token 只认带逗号形态得 11 行，并准备据此判审计员「数错」；实测无逗号 `1196` 合法（负控 `11196 / 0x1196 / 111,196 / 11960` 全不命中），修正后 13 行与审计员一致 ⇒ **我差点把一条正确的外部结论判成错**，与 R148 S-342 同族。

### 九 · 未取得（不粉饰）

① `coverage.tsv` 内容仍**不可重数**（只有 4,147,334 B 与 sha `c2ee063f…` 有台账）；② 13 行承载里的「独立复算」只能当**自述**（`R17_R41_RECOMPUTE` 已失）；③ 乙类 11 条真失路径本轮未逐条判可否二手替代；④ F23 的 grade **本轮未改**，且本轮结论是「改它是**裁定**问题不是**证据**问题」，**不构成改动授权**。

### 十 · 落盘与门禁

`_r150/` 九个脚本（`r150a`..`r150j` + `r150t`）。`R14_COMMON` 新增 **§2.155**（CR 保持 **1081**）、台账新增 **§1205**（CR 保持 **337**）、`LEAD_LOCK` 新增 **OH1..OH9**（CR 保持 **137**）、看板本轮段（CR **0**）。归档：写前 **256** 行 + 本轮约 60 行 > 300 ⇒ 按 R138F 归档最早两段（146 / 147），`BOARD_ARCHIVE` CR 保持 **2952**。

"""
board=open(B,encoding='utf-8').read()
nb_new = NEW.count('\n')
lines_before = board.count('\n')
print('  写前看板行数 %d，本轮段 %d 行，合计 %d'%(lines_before, nb_new, lines_before+nb_new))
ck('1 写前看板 CR==0', crc(B)==0, crc(B))
ck('2 写前看板 256 行', lines_before==256, lines_before)
need_archive = (lines_before + nb_new) > 300
ck('3 判据：写前+本轮 > 300 ⇒ 必须归档', need_archive, lines_before+nb_new)

# 找最早两段（按 ## 🟢 R17 第 N 轮 切）
segs=[(m.start(), int(m.group(1))) for m in re.finditer(r'(?m)^## 🟢 R17 第 (\d+) 轮', board)]
print('  段标题:', [s[1] for s in segs])
ck('4 段数 >=4', len(segs)>=4, len(segs))
first_two = segs[:2]
ck('5 最早两段是 146 / 147', [x[1] for x in first_two]==[146,147], [x[1] for x in first_two])

start = first_two[0][0]
end = segs[2][0] if len(segs)>2 else len(board)
arch_chunk = board[start:end]
print('  待归档块 %d 字节 / %d 行'%(len(arch_chunk.encode()), arch_chunk.count('\n')))
ck('6 待归档块含 146 与 147 两个标题',
   '第 146 轮' in arch_chunk and '第 147 轮' in arch_chunk)
remain = board[:start] + board[end:]

# 归档：ARC CR 必须保持 2952
arc=open(A,'rb').read()
ck('7 ARC 写前 CR==2952', arc.count(b'\r')==2952, arc.count(b'\r'))
bk=backup(A,'r150arc'); ck('8 ARC 备份 wx 独占', os.path.exists(bk))
with open(A,'ab') as f: f.write(arch_chunk.encode('utf-8'))
ck('9 ARC 追加后 CR 保持 2952', crc(A)==2952, crc(A))
ck('10 ARC 前缀 sha 与旧一致',
   hashlib.sha256(open(A,'rb').read()[:len(arc)]).hexdigest()==hashlib.sha256(arc).hexdigest())
ck('11 ARC 回读含 146/147', '第 146 轮' in open(A,encoding='utf-8').read()
   and '第 147 轮' in open(A,encoding='utf-8').read())

# 写新看板
bk2=backup(B,'r150'); ck('12 看板备份 wx 独占', os.path.exists(bk2))
newboard = remain.rstrip('\n') + '\n\n' + NEW
open(B,'w',encoding='utf-8').write(newboard)
rb=open(B,encoding='utf-8').read()
ck('13 看板 CR==0', crc(B)==0, crc(B))
ck('14 看板行数 <=300', rb.count('\n')<=300, rb.count('\n'))
ck('15 看板含第 150 轮段', '第 150 轮' in rb)
ck('16 看板不再含第 146/147 轮段', '第 146 轮' not in rb and '第 147 轮' not in rb)
ck('17 看板仍含 148/149/150', all(('第 %d 轮'%i) in rb for i in (148,149,150)))
ck('18 第 150 轮段只出现 1 次标题', rb.count('## 🟢 R17 第 150 轮')==1, rb.count('## 🟢 R17 第 150 轮'))
print('  终态看板 %d 行'%rb.count('\n'))
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)
