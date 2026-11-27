# -*- coding: utf-8 -*-
"""R176 收口补记：C16 随 §2.181 重钉 174 -> 175 节（写在本轮四件套的三处尾部）。"""
import hashlib,os,sys,time
T='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
R='/home/t628/projects/ra2-campaign-forge'
BASE=os.path.join(T,'R17_LEAD_BASELINE')
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
NEW_PIN='e0d3ff0bc5e3d563e9e7f49c924e2648243a79069a79474bc2c10e470ee45a7e'
OLD_PIN='0bfc18cd3c2df25f98c8add57819d1d023c8d9408f0c92414ea56176c8ac78db'
SEG = """
**收口补（同轮第二段）：C16 随 §2.181 重钉 174 → 175 节.** `r176l_c16_repin.py` **17 断言 0 FAIL**：ast 取旧 `C16_FLOORS`（**174** 条）与旧 pin，重算表 sha 命中 `0bfc18cd3c2df25f…` 作硬闸；只插 `181: 4213`（= §2.181 实测 **8,426 B** 的一半），其余 174 条逐条不变；pin → **`e0d3ff0bc5e3d563…`**。三条反控：181 floor +1 使 sha 变 / 删 181 使 sha 回到旧值 / 把 180 抄成 179 的值使 sha 变。`check_disc` 复跑 NOTE 逐字 `175 sections measured (pinned 175), hollow/deficient 0, missing 0, unpinned 0, min margin 20`（改前 **174 measured / 174 pinned / unpinned 1**，而 `C16_UNPINNED_MAX == 2` ⇒ 不重钉下一轮仍可能过、但本轮先收口）；`gate_runner` G3e 现算 **`e0d3ff0b`** 与常量一致、G1=G2=G3=ok；`GATE_VER` 仍 **R166**。
"""
for p in (os.path.join(T,'R14_COMMON.md'), os.path.join(R,'lead/LEAD_LOCK'), os.path.join(T,'STATUS_BOARD.md')):
    raw=open(p,'rb').read()
    txt=raw.decode('utf-8')
    ck('A1 %s pin not yet recorded'%os.path.basename(p), 'e0d3ff0bc5e3d563' not in txt)
    ck('A2 %s old pin mentioned'%os.path.basename(p), '0bfc18cd3c2df25f' in txt, '%d'%txt.count('0bfc18cd3c2df25f'))
cr_exp={os.path.join(T,'R14_COMMON.md'):1081,os.path.join(R,'lead/LEAD_LOCK'):137,os.path.join(T,'STATUS_BOARD.md'):0}
if F: print('ABORT'); sys.exit(1)
ts=time.strftime('%Y%m%d_%H%M%S')
for p in cr_exp:
    raw=open(p,'rb').read()
    bp=os.path.join(BASE,os.path.basename(p)+'.before_r176close_%s.bak'%ts)
    with open(bp,'xb') as f: f.write(raw)
    ck('B0 %s backup'%os.path.basename(p), open(bp,'rb').read()==raw)
    add=SEG if raw.endswith(b'\n') else b'\n'+SEG.encode()
    if isinstance(add,str): add=add.encode()
    with open(p,'ab') as f: f.write(add)
    back=open(p,'rb').read()
    ck('B1 %s prefix intact'%os.path.basename(p), back[:len(raw)]==raw)
    ck('B2 %s CR'%os.path.basename(p), back.count(b'\r')==cr_exp[p], '%d'%back.count(b'\r'))
    ck('B3 %s new pin present'%os.path.basename(p), b'e0d3ff0bc5e3d563' in back)
    print('  %s: %d -> %d B'%(os.path.basename(p),len(raw),len(back)))
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
