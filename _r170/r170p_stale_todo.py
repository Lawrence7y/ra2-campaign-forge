#!/usr/bin/env python3
"""R170 P：登记一条**过期待办被证伪**（R169 待办① 说「V549 的 F23 行一字未改、与目标①仍有差」）。
实测：F23 statement **自 V540 起**即含「差 **1 行无归属**」×1、「4,147,334」×2、「coverage.tsv」×1；
V530–V539 statement 恒 **208** 字符、三串全 **0**，V540–V549 恒 **1012** 字符、statement sha 恒 `6552c5b84326`。
"""
import hashlib, json, os
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
LOCK=ROOT+'/lead/LEAD_LOCK'; BRD=T+'/STATUS_BOARD.md'; RC=T+'/R14_COMMON.md'
BAK=T+'/R17_LEAD_BASELINE'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

PA10 = """

PA10. 🔴 **交付八：R169 待办① 里那句「V549 的 F23 行一字未改、与目标 ① 仍有差」是**过期待办**，与本轮 R137 九节① 的两处要求直接相反 —— 逐版实测证伪.** R137 九节① 要求 F23 补两处：「12 行分解余 1 行无归属」与「计数依赖 `coverage.tsv` 4,147,334 B 已失」。逐版实测（V530..V549 共 **20** 版）：**V530–V539** 的 F23 statement 恒 **208** 字符、三串（`差 **1 行无归属**` / `4,147,334` / `coverage.tsv`）**全 0**；**V540 起** statement 恒 **1012** 字符、三串分别为 **1 / 2 / 1**，且 V540–V549 **statement sha256 恒 `6552c5b84326`**（十个版本逐字节相同）⇒ 两处要求**早在 V540 就已写进正文**，不是「缺」。R169 待办那句的真实成因是：R148/R159 的补段写在 **limitations**、而待办按「正文」读，把「不在 statement 之外」误当成「不在正文」。⇒ **口径订正**：本表的 statement 与 limitations **都是正文**；引用「F23 缺两处」时必须带版本区间（**≤V539**），否则与现版实况相反。**反控**：V530–V539 十版 statement 逐版相同（同一 sha）、V540–V549 十版逐版相同 ⇒ 该跃变**只在 V539→V540 一跳**发生，不是渐进（`_r170/r170c_prov.py` C0–C4 与 `_r170/r170i_recompute.py` M1–M3，其中 M3 把「208/1012 字符」写成断言时我误用了**字节**口径而 FAIL ⇒ 已改字符口径，记 **S-574**）。**S-574**：`r170i` 的 M3 拿 `len(encode())` 比 208/1012 —— 那是**字节**，字符数是 **208/1012**、字节是 **432/1785**；断言当场 FAIL，改正后 3/3 PASS（与 R150 S-359 同族：**同一量的两种口径混用**）。
"""
b=open(LOCK,'rb').read()
assert PA10.encode() not in b
bak=os.path.join(BAK,'LEAD_LOCK.before_r170_PA10.bak')
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
open(LOCK,'wb').write(b+PA10.encode('utf-8'))
ck('P0 PA10 恰 1 次', open(LOCK,encoding='utf-8').read().count('PA10.')==1, 1)
ck('P1 LEAD_LOCK CR 保持 137', open(LOCK,'rb').read().count(b'\r')==137, open(LOCK,'rb').read().count(b'\r'))

# R14_COMMON §2.175 追加一段（只增不减，C16 下界允许增长）
ADD = """
### 六 · 一条过期待办的证伪（R169 待办① 说「F23 仍有差」）
逐版实测 V530..V549 **20** 版：**V530–V539** 的 F23 statement 恒 **208 字符**，三串（`差 **1 行无归属**` / `4,147,334` / `coverage.tsv`）**全 0**；**V540 起**恒 **1012 字符**、三串 **1 / 2 / 1**，且 V540–V549 的 **statement sha256 恒 `6552c5b84326`**（十版逐字节相同）。⇒ R137 九节① 的两处要求**早在 V540 就写进正文**，「F23 仍有差」只在 **≤V539** 成立。**口径订正**：本表 statement 与 limitations **都是正文**；R148/R159 的补段写在 limitations，待办按「statement」读才会判成缺。**反控**：两段各十版内部逐版 sha 相同 ⇒ 跃变**只在 V539→V540 一跳**。**S-574**：`r170i` M3 把「208/1012」当字节断言（真值 byte = **432/1785**），当场 FAIL 后改字符口径。
"""
t=open(RC,encoding='utf-8').read()
assert ADD not in t
assert t.count('## 2.175 · R170')==1
bak=os.path.join(BAK,'R14_COMMON.md.before_r170_SIX.bak')
b2=open(RC,'rb').read()
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b2)
open(RC,'wb').write(b2+ADD.encode('utf-8'))
ck('P2 §2.175 追加一段、CR 保持 1081', open(RC,'rb').read().count(b'\r')==1081, open(RC,'rb').read().count(b'\r'))

# 看板补一句
bb=open(BRD,'rb').read(); t2=bb.decode('utf-8')
anchor='**S-573**：本条原写「168 节 pinned 168」'
assert t2.count(anchor)==1, t2.count(anchor)
ins=('**过期待办被证伪**：R169 待办① 说「V549 的 F23 行一字未改、与目标 ① 仍有差」—— 逐版实测 V530–V539 的 F23 statement 恒 **208** 字符、三串全 0；'
     '**V540 起**恒 **1012** 字符、三串 **1 / 2 / 1**，且 V540–V549 的 statement sha 恒 **`6552c5b84326`** ⇒ R137 九节① 两处要求**早在 V540 已写进正文**，'
     '该待办只在 **≤V539** 成立（口径订正：statement 与 limitations **都是正文**）。**S-574**：`r170i` M3 把 208/1012 当字节断言（真值 432/1785）当场 FAIL。\n\n')
open(BRD,'wb').write(t2.replace(anchor, ins+anchor,1).encode('utf-8'))
ck('P3 看板 CR 0 且行数 < 260', open(BRD,'rb').read().count(b'\r')==0 and open(BRD,'rb').read().count(b'\n')<260,
   open(BRD,'rb').read().count(b'\n'))
json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok'])},
          open(ROOT+'/_r170/r170p_stale_todo.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
