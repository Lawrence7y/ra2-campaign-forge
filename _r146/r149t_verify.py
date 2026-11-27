#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 T：终态 30 断言。"""
import hashlib, os, re, subprocess
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=os.path.join(ROOT,'lead'); D14=os.path.join(LEAD,'next_re_20261117_r14')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def crc(p): return open(p,'rb').read().count(b'\r')

F={'R14_COMMON':os.path.join(D14,'R14_COMMON.md'),
   'LEDGER':os.path.join(LEAD,'GOAL_THREE_TARGETS_20261018.md'),
   'LEAD_LOCK':os.path.join(LEAD,'LEAD_LOCK'),
   'BOARD':os.path.join(D14,'STATUS_BOARD.md'),
   'ARCHIVE':os.path.join(D14,'BOARD_ARCHIVE.md')}
EXP={'R14_COMMON':1081,'LEDGER':337,'LEAD_LOCK':137,'BOARD':0,'ARCHIVE':2952}
for k,p in F.items():
    ck('1.%s CR == %d'%(k,EXP[k]), crc(p)==EXP[k], crc(p))
ck('2 看板行数 <=300', sum(1 for _ in open(F['BOARD'],encoding='utf-8'))<=300,
   sum(1 for _ in open(F['BOARD'],encoding='utf-8')))
ck('3 台账末节 §1204', re.findall(r'(?m)^## §(\d+)',open(F['LEDGER'],encoding='utf-8').read())[-1]=='1204')
ck('4 R14_COMMON 末节 2.154',
   re.findall(r'(?m)^## 2\.(\d+)',open(F['R14_COMMON'],encoding='utf-8').read())[-1]=='154')
lock=open(F['LEAD_LOCK'],encoding='utf-8').read()
ck('5 锁末段 OE', re.search(r'(?m)^OE10\.',lock) is not None)
ck('6 看板有第 149 轮段', '第 149 轮' in open(F['BOARD'],encoding='utf-8').read())

# 门禁
r=subprocess.run(['python3','check_disc.py'],cwd=D14,capture_output=True,text=True,timeout=300)
ck('7 门禁 exit 0', r.returncode==0, r.returncode)
ck('8 C10 ok(R149)', 'ok(R149)' in r.stdout)
m=re.search(r'C16 per-section floors: (\d+) sections measured \(pinned (\d+)\).*unpinned (\d+)',r.stdout)
ck('9 C16 pinned==measured, unpinned 0', m and m.group(1)==m.group(2) and m.group(3)=='0', m.groups() if m else None)
ck('10 C7d 412e1e8f', '412e1e8f' in r.stdout)
ck('11 C12b 12/12', '12/12 rows identical' in r.stdout)
ck('12 C12 12 anchors hit', '12 anchors hit' in r.stdout)
# 钉与现算相等
src=open(os.path.join(D14,'check_disc.py'),encoding='utf-8').read()
mt=re.search(r'C16_FLOORS = \{(.*?)\n\}',src,re.S)
tbl=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)',mt.group(1)))
n='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
ck('13 C16_FLOORS_SHA256 == 现算', hashlib.sha256(n.encode()).hexdigest() in src)
ck('14 FREEZE_SHA256 == DISC_UNVERIFIABLE 现算',
   hashlib.sha256(open(os.path.join(D14,'DISC_UNVERIFIABLE.tsv'),'rb').read()).hexdigest() in src)
rows=[l.split('\t') for l in open(os.path.join(D14,'DISC_RECHECK.tsv'),encoding='utf-8').read().split('\n')]
rows=[x for x in rows if len(x)==7 and x[0].strip().isdigit()]
blob='\n'.join('%s\t%s\t%s'%(x[0],x[4].strip(),x[5].strip()) for x in rows)
ck('15 C7_TEXT_SHA256 == 现算', hashlib.sha256(blob.encode()).hexdigest() in src)
ck('16 脚本产物齐（r149a..r149j + t）',
   all(os.path.exists(os.path.join(ROOT,'_r146',f)) for f in
       ['r149a_lostpath.py','r149b_r90_criterion.py','r149c_rule_d.py',
        'r149d_1654_provenance.py','r149f_write.py','r149g_write2.py',
        'r149h_repin.py','r149i_c10.py','r149j_repin_c7.py','r149t_verify.py']))
ck('17 子代理产物齐', all(os.path.exists(os.path.join(ROOT,'_r146',p)) for p in
   ['sub_hy4/r149x_exec.md','sub_deepseek/r149y_audit.md']))
# 孤儿进程
o=subprocess.run(['bash','-c',"ps -eo pid,cmd | grep -E '_r146/r149[a-z]|_r146/r149[a-z].py' | grep -v grep | grep -v r149t_verify | wc -l"],
                 capture_output=True,text=True)
ck('18 无孤儿进程', o.stdout.strip()=='0', o.stdout.strip())
# FACT_INDEX 未改
ck('19 FACT_INDEX v540 未改（fabd1e57…）',
   hashlib.sha256(open(os.path.join(D14,'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv'),'rb').read()
                  ).hexdigest().startswith('fabd1e57'))
ck('20 四件套备份齐', len([x for x in os.listdir(os.path.join(D14,'R17_LEAD_BASELINE'))
                          if '.before_r149' in x])>=7,
   len([x for x in os.listdir(os.path.join(D14,'R17_LEAD_BASELINE')) if '.before_r149' in x]))
print(f"\n=== {len(fails)} FAIL / 20 组 ===")
for f in fails: print('  ',f)
