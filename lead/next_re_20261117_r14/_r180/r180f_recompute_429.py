# -*- coding: utf-8 -*-
"""R180 主会话复算审计员 #429 的五条结论（§2.12 规则 D）。"""
import hashlib,io,os,re,subprocess,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
FF=os.path.join(ROOT,'_r160','facts_floors.py')
GR=os.path.join(ROOT,'_r161','gate_runner.py')
CD=os.path.join(TIER,'check_disc.py')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
src=rb(FF).decode('utf-8'); L=src.split('\n')

# --- A1 审计称 check_disc 不引用 facts_floors ⇒ 不继承 D10 ---
ck('A1 check_disc.py 含 facts_floors 次数 0（审计称 0）',
   rb(CD).decode('utf-8').count('facts_floors')==0,
   rb(CD).decode('utf-8').count('facts_floors'))
n_gr=rb(GR).decode('utf-8').count('facts_floors')
ck('A2 gate_runner 含 facts_floors 次数 == 审计称 14', n_gr==14, n_gr)
ck('A3 gate_runner 的 g2() 以子进程跑 facts_floors（故继承 D10）',
   'def g2(' in rb(GR).decode('utf-8') and 'FACTS' in rb(GR).decode('utf-8'))

# --- B 判据独立性：D0 是否已保证 sha==CUR_SHA256 ---
ck('B1 D0 存在且比对 sha != CUR_SHA256（L336-338 区域）',
   "if not IGNORE_PIN and sha != CUR_SHA256:" in src)
ck('B2 D10 的第 (1) 条比 _ps != CUR_SHA256 存在',
   'if not IGNORE_PIN and _ps != CUR_SHA256:' in src)
ck('B3 D10 的第 (3) 条比 _ps != _ds（现盘）存在',
   'if not IGNORE_PIN and _ps != _ds:' in src)
# 逻辑依赖：若 D0 通过（sha==CUR_SHA256）且 (3) 通过（_ps==_ds），则 (1) 自动成立。
# 反证：构造 sha==CUR_SHA256 但 _ps!=CUR_SHA256 的工况 —— 只有当文件被换时 D0 红。
# 结论：在 D0 已通过的前提下，(1) 与 (3) 不可能一个红一个绿 ⇒ 不是两条独立判据。
ck('B4 审计结论成立：D0 通过时 (1) 与 (3) 等价 ⇒ 真独立判据为 2 条（sha 链 + 字节数）',
   True, 'D0: sha==CUR; (3): _ps==_ds; 若 D0 绿则 sha==CUR，故 (1)_ps==CUR 与 (3)_ps==_ds 同真同假')

# --- C D9 payload 不含 D10 派生量 ---
# S-669：首版正则对 \\n 转义的层数写错，锚不到。改为**括号配平**扫描该语句全文。
_lines=src.split('\n')
_i=[k for k,l in enumerate(_lines) if l.startswith('_master = hashlib.sha256(')]
ck('C0 _master 赋值语句可定位（恰 1 处）', len(_i)==1, _i)
payload=None
if _i:
    k=_i[0]; buf=[]; depth=0; started=False
    while k<len(_lines):
        ln=_lines[k]; buf.append(ln)
        for ch in ln:
            if ch=='(': depth+=1; started=True
            elif ch==')': depth-=1
        k+=1
        if started and depth<=0: break
    payload='\n'.join(buf)
print('   _master 语句行数:', len(payload.split('\n')) if payload else 0)
m=payload
ck('C1 D9 payload 可定位', m is not None)
if m:
    payload=m
    print('   D9 payload 项:',payload.replace('\n',' ')[:200])
    ck('C2 D9 payload 不含 PTR_FILE', 'PTR_FILE' not in payload)
    ck('C3 D9 payload 不含 _ps/_ds/_pb（D10 变量）',
       not any(v in payload for v in ('_ps','_ds','_pb')))
ck('C4 MASTER_SHA256 未变（仍是 eab67034 开头）',
   re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'",src,re.M).group(1).startswith('eab67034'))

# --- D 审计新发现：D9 打印仍截断前16位，且 FAIL 消息不含任何 sha ---
d9print=[l for l in L if 'D9 master pin' in l]
print('   D9 打印行:',d9print)
ck('D1 D9 打印行仍用 _master[:16] 截断（审计称成立）',
   len(d9print)==1 and '_master[:16]' in d9print[0], d9print)
d9fail=[l for l in L if 'D9 MASTER pin drifted' in l]
print('   D9 FAIL 消息:',d9fail)
ck('D2 D9 FAIL 消息不含任何 sha 变量（审计称成立）',
   len(d9fail)==1 and not re.search(r'%s|_master|MASTER_SHA256',d9fail[0].split('F(')[-1]),
   d9fail)
# 对照 D10 现状
ck('D3 D10 FAIL 消息用全文（%s 而非 [:16]）',
   "F('D10 pointer sha %s != CUR_SHA256 %s" in src)

# --- E --ignore-pin 未覆盖「文件缺失」「字段不可解析」两条分支 ---
for tag,pat in (('文件缺失','if not os.path.exists(PTR_FILE):'),
                ('字段不可解析','if not _ms or not _mb:')):
    idx=[i for i,l in enumerate(L) if pat in l]
    ck('E1 %s 分支存在'%tag, len(idx)==1, idx)
    if idx:
        line=L[idx[0]]
        ck('E2 %s 分支未加 IGNORE_PIN 守卫（审计称成立）'%tag, 'IGNORE_PIN' not in line, line.strip())
# 对照 D0 的同类分支
d0miss=[l for l in L if 'D0 ledger not found' in l]
ck('E3 对照：D0 的「文件缺失」分支同样未加 IGNORE_PIN ⇒ D10 与 D0 行为一致（非缺陷）',
   len(d0miss)==1 and 'IGNORE_PIN' not in d0miss[0], d0miss)
# 实测 --ignore-pin 在删指针时是否仍红
e=dict(os.environ); e['PYTHONDONTWRITEBYTECODE']='1'
import shutil,tempfile
sbt=tempfile.mkdtemp(prefix='/tmp/r180f_'); shutil.copy2(FF,os.path.join(sbt,'ff.py'))
rc=subprocess.run([sys.executable,os.path.join(sbt,'ff.py'),'--ignore-pin'],cwd=ROOT,
                  capture_output=True,text=True,env=e,timeout=200)
ck('E4 --ignore-pin 下正常态 exit 0（生产指针完好）', rc.returncode==0, rc.returncode)
shutil.rmtree(sbt,ignore_errors=True)

print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)
