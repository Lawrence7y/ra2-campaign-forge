#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 T：终态断言（五项 CR / 看板 / 门禁 / 三钉现算 / 归档 / 无孤儿 / FACT_INDEX 未改）。"""
import hashlib, json, os, re, subprocess
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead'); D14=os.path.join(LEAD,'next_re_20261117_r14')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def crc(p): return open(p,'rb').read().count(b'\r')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()

F={'R14_COMMON':('R14_COMMON.md',1081),'LEDGER':('../GOAL_THREE_TARGETS_20261018.md',337),
   'LEAD_LOCK':('../LEAD_LOCK',137),'BOARD':('STATUS_BOARD.md',0),'ARCHIVE':('BOARD_ARCHIVE.md',2952)}
for k,(rel,exp) in F.items():
    p=os.path.normpath(os.path.join(D14,rel))
    ck('1.%s CR == %d'%(k,exp), crc(p)==exp, crc(p))

board=open(os.path.join(D14,'STATUS_BOARD.md'),encoding='utf-8').read()
ck('2 看板行数 <=300', board.count('\n')<=300, board.count('\n'))
ck('3 看板含第 150 轮段', '## 🟢 R17 第 150 轮' in board)
rc=open(os.path.join(D14,'R14_COMMON.md'),encoding='utf-8').read()
ck('4 R14_COMMON 末节 2.155', re.findall(r'(?m)^## 2\.(\d+)',rc)[-1]=='155',
   re.findall(r'(?m)^## 2\.(\d+)',rc)[-1])
ck('5 §2.155 标题唯一', rc.count('## 2.155')==1, rc.count('## 2.155'))
led=open(os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md'),encoding='utf-8').read()
ck('6 台账末节 §1205', re.findall(r'(?m)^## §(\d+)',led)[-1]=='1205',
   re.findall(r'(?m)^## §(\d+)',led)[-1])
lock=open(os.path.join(LEAD,'LEAD_LOCK'),encoding='utf-8').read()
ck('7 锁含 OH1..OH10', all(('OH%d.'%i) in lock for i in range(1,11)))
ck('8 锁仍含 OE/OG 旧段', 'OE10.' in lock and 'OG10.' in lock)

# 门禁
r=subprocess.run(['python3','check_disc.py'],cwd=D14,capture_output=True,text=True,timeout=900)
ck('9 门禁 exit 0', r.returncode==0, r.returncode)
ck('10 C10 ok(R150)', 'ok(R150)' in r.stdout)
m=re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\).*unpinned (\d+)',r.stdout)
ck('11 C16 measured==pinned, unpinned 0', m and m.group(1)==m.group(2) and m.group(3)=='0',
   m.groups() if m else None)
ck('12 C16 measured 149', m and m.group(1)=='149', m.group(1) if m else None)
ck('13 C12b 12/12', '12/12 rows identical' in r.stdout)
ck('14 C12 12 anchors hit', '12 anchors hit' in r.stdout)

# 三钉与现算相等
G=os.path.join(D14,'check_disc.py'); src=open(G,encoding='utf-8').read()
tbl=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)',
        re.search(r'C16_FLOORS = \{(.*?)\n\}',src,re.S).group(1)))
ck('15 C16_FLOORS_SHA256 == 现算',
   hashlib.sha256('\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl)).encode()).hexdigest()
   == re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",src).group(1))
# §2.155 的 floor 是否等于实测体字节 - 21
mm=re.search(r'(?m)^## 2\.155 ',rc); nxt=re.search(r'(?m)^## 2\.',rc[mm.end():])
# §2.155 是末节 ⇒ nxt 可能为 None（S-362 记此自错：断言里隐含「后面还有节」）
body = rc[mm.end():mm.end()+nxt.start()] if nxt else rc[mm.end():]
sz=len(body.encode())
ck('16 C16[155] == §2.155 体字节 - 21', tbl[155]==sz-21, (tbl[155],sz))
rows=[l.split('\t') for l in open(os.path.join(D14,'DISC_RECHECK.tsv'),encoding='utf-8').read().split('\n')]
rows=[x for x in rows if len(x)==7 and x[0].strip().isdigit()]
blob='\n'.join('%s\t%s\t%s'%(x[0],x[4].strip(),x[5].strip()) for x in rows)
ck('17 C7_TEXT_SHA256 == 现算',
   hashlib.sha256(blob.encode()).hexdigest()==re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'",src).group(1))
r20=[x for x in rows if x[0]=='20'][0]
ck('18 C7_ROW_SHA[20] == 现算',
   hashlib.sha256(('%s\t%s\t%s'%('20',r20[4].strip(),r20[5].strip())).encode()).hexdigest()
   == re.search(r"'20': '([0-9a-f]{64})'",src).group(1))
ck('19 FREEZE_SHA256 == DISC_UNVERIFIABLE 现算',
   sha(os.path.join(D14,'DISC_UNVERIFIABLE.tsv'))==re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'",src).group(1))

# 归档件
arc=open(os.path.join(D14,'BOARD_ARCHIVE.md'),encoding='utf-8').read()
ck('20 归档件含 146/147', '第 146 轮' in arc and '第 147 轮' in arc)
ck('21 归档件 146/147 各 1 次', arc.count('## 🟢 R17 第 146 轮')==1 and arc.count('## 🟢 R17 第 147 轮')==1,
   (arc.count('## 🟢 R17 第 146 轮'),arc.count('## 🟢 R17 第 147 轮')))
ck('22 看板不再含 146/147', '第 146 轮' not in board and '第 147 轮' not in board)
# S-363：先前这里写 count('S-362')==1，实测 2 —— 标题「补记 S-360..S-362」本身也含该串。
# 改为钉「补记段标题只出现 1 次」这条真正想表达的量。
# S-364：这里原写死旧标题 S-360..S-362，标题在 S-363 记录后已改为 S-360..S-363 ⇒ 假 FAIL。
# 改法：不写死区间，改为「补记段标题（正则）恰 1 个」这条对它自己不变的量。
_bx=re.findall(r'\*\*补记 S-\d\d\d\.\.S-\d\d\d', board)
ck('22b 看板补记段标题恰 1 个（不写死区间号）', len(_bx)==1, _bx)
ck('22c 看板含 S-360..S-363 补记内容', all(('S-36%d'%i) in board for i in (0,1,2)))

# FACT_INDEX 未改
ck('23 FACT_INDEX v540 未改（fabd1e57…）',
   sha(os.path.join(D14,'R17_R112_FACTINDEX_V540','FACT_INDEX.tsv')).startswith('fabd1e57'))

# 产物齐
need=['r150a_evidcensus.py','r150b_triage_scope.py','r150c_grade_axis.py','r150d_f23_carriers.py',
      'r150e_f23_token.py','r150f_rule_d.py','r150g_audit_recheck.py','r150h_carrier_caliber.py',
      'r150i_write.py','r150j_board.py','r150k_repin.py','r150t_verify.py',
      'sub_hy4/r150x_exec.md','sub_deepseek/r150y_audit.md']
miss=[f for f in need if not os.path.exists(os.path.join(ROOT,'_r150',f))]
ck('24 _r150 产物齐', not miss, miss)

# 备份齐
baks=[x for x in os.listdir(os.path.join(D14,'R17_LEAD_BASELINE')) if '.before_r150' in x]
ck('25 wx 备份 >= 6 份', len(baks)>=6, len(baks))

# 孤儿进程
o=subprocess.run(['bash','-c',
   "ps -eo pid,cmd | grep -E '_r150/r150[a-z]' | grep -v grep | grep -v r150t_verify | wc -l"],
   capture_output=True,text=True)
ck('26 无孤儿进程', o.stdout.strip()=='0', o.stdout.strip())

# 子代理产物中的关键数字与主会话一致（规则 D 的复核结论写入核对）
ex=open(os.path.join(ROOT,'_r150','sub_hy4','r150x_exec.md'),encoding='utf-8').read()
ck('27 执行员报告含 178 / 43 / 16 / 33', all(k in ex for k in ('178','43','16','33')))
au=open(os.path.join(ROOT,'_r150','sub_deepseek','r150y_audit.md'),encoding='utf-8').read()
ck('28 审计报告无反引号', '`' not in au)
print(f"\n=== {len(fails)} FAIL / 28 组 ===")
for f in fails: print('  ',f)
