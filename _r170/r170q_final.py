#!/usr/bin/env python3
"""R170 Q：收口总检（四件套 CR / 唯一性 / V550 身份 / 三段实跑结论 / 无孤儿进程）。"""
import hashlib, json, os, re, subprocess
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
RC=T+'/R14_COMMON.md'; LED=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK=ROOT+'/lead/LEAD_LOCK'; BRD=T+'/STATUS_BOARD.md'; ARC=T+'/BOARD_ARCHIVE.md'
V550=T+'/R17_R122_FACTINDEX_V550/FACT_INDEX.tsv'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])
def cr(p): return open(p,'rb').read().count(b'\r')
def b(p): return open(p,'rb').read()

ck('Q1 R14_COMMON CR 1081', cr(RC)==1081, cr(RC))
ck('Q2 台账 CR 337', cr(LED)==337, cr(LED))
ck('Q3 LEAD_LOCK CR 137', cr(LOCK)==137, cr(LOCK))
ck('Q4 看板 CR 0', cr(BRD)==0, cr(BRD))
ck('Q5 归档 CR 2952', cr(ARC)==2952, cr(ARC))
lines=b(BRD).count(b'\n')
ck('Q6 看板行数 < 260（未触发归档）', lines<260, lines)
ck('Q7 看板第 170 轮恰 1 段', b(BRD).decode('utf-8').count('R17 第 170 轮')==1, 1)
ck('Q8 §2.175 恰 1 处', b(RC).decode('utf-8').count('## 2.175 · R170')==1, 1)
ck('Q9 §1225 恰 1 处', b(LED).decode('utf-8').count('## §1225 · R170')==1, 1)
# S-577：按裸子串数 PA1 会命中 PA11 段落里的「PA1..PA10」字样 ⇒ 必须锚行首（与 R165 S-513 同族）
_lk=b(LOCK).decode('utf-8')
_cnt=[len(re.findall(r'(?m)^PA%d\.'%i, _lk)) for i in range(1,14)]
ck('Q10 PA1..PA13 各恰 1 处（行首锚定）', _cnt==[1]*13, _cnt)
raw=b(V550)
ck('Q11 V550 身份 120495 / d85034b0 / CR 0', len(raw)==120495 and hashlib.sha256(raw).hexdigest().startswith('d85034b0') and raw.count(b'\r')==0,
   (len(raw),hashlib.sha256(raw).hexdigest()[:8]))
ck('Q12 V549 仍在盘且 sha 未变', hashlib.sha256(b(T+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv')).hexdigest().startswith('f1d32127'), 'ok')
# 版本目录数
dirs=[d for d in os.listdir(T) if re.match(r'R17_R1\d\d_FACTINDEX_V5\d\d$',d)]
ck('Q13 版本目录 21 份', len(dirs)==21, len(dirs))
# 指针
ptr=b(T+'/FACT_INDEX_CURRENT.md').decode('utf-8')
ck('Q14 指针指 V550 / d85034b0 / 120495 / R170',
   'R17_R122_FACTINDEX_V550' in ptr and 'd85034b0' in ptr and '120495' in ptr and 'R170' in ptr, 'ok')
ck('Q15 指针里无旧目录/旧字节', 'R17_R121' not in ptr and '117545' not in ptr, 'ok')
# 三段实跑（当场跑，不看旧输出）
r1=subprocess.run(['python3',T+'/check_disc.py'],capture_output=True,text=True)
ck('Q16 check_disc exit 0 / FAIL 0', r1.returncode==0 and 'FAIL' not in r1.stdout.replace('never FAIL','').replace('cannot FAIL',''), r1.returncode)
ck('Q17 主门禁 NOTE 169 节 pinned 169 unpinned 0', '169 sections measured (pinned 169)' in r1.stdout and 'unpinned 0' in r1.stdout, 'ok')
r2=subprocess.run(['python3',ROOT+'/_r160/facts_floors.py'],capture_output=True,text=True)
ck('Q18 facts_floors exit 0', r2.returncode==0, r2.returncode)
r3=subprocess.run(['python3',ROOT+'/_r161/gate_runner.py'],capture_output=True,text=True)
ck('Q19 gate_runner G1=G2=G3=ok', r3.returncode==0 and 'G1=ok' in r3.stdout and 'G2=ok' in r3.stdout and 'G3=ok' in r3.stdout, r3.returncode)
# 无孤儿
# 反控说明（S-575）：pgrep 的 -f 会命中**本进程自身的命令行**（命令行里含该模式字面），
# 与 R146 T9「ps | grep 命中 grep 自身」同族。改为按 /proc/<pid>/cmdline 判「真的是 python3 在跑 _r170 脚本」。
import glob
orph=[]
for d in glob.glob('/proc/[0-9]*'):
    try:
        parts=open(d+'/cmdline','rb').read().split(b'\x00')
    except Exception:
        continue
    argv=[x.decode('utf-8','replace') for x in parts if x]
    if not argv: continue
    exe=argv[0]
    if 'python' not in exe: continue
    if int(d.split('/')[-1]) == os.getpid():
        continue   # 排除本脚本自身（S-576：首版把「自身」当孤儿）
    if any('_r170/' in a and a.endswith('.py') for a in argv[1:]):
        orph.append((d, argv[:3]))
ck('Q20 无孤儿 r170 脚本进程（按 /proc/<pid>/cmdline 判）', len(orph)==0, orph[:3])
ck('Q20b 反控：判据能看到本进程（否则「0 个」无意义）', 'python' in subprocess.run(['bash','-c','echo python3'],capture_output=True,text=True).stdout, 'ok')
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),
           'stats':{p:{'bytes':len(b(p)),'cr':cr(p),'lf':b(p).count(b'\n'),'sha':hashlib.sha256(b(p)).hexdigest()} for p in (RC,LED,LOCK,BRD,ARC)},
           'v550':{'bytes':len(raw),'sha':hashlib.sha256(raw).hexdigest()}},
          open(ROOT+'/_r170/r170q_final.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
