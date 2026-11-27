#!/usr/bin/env python3
"""R170 N：更正 PA5 与看板第 170 轮段的 C16 口径（168/168 是**写入前**的事实，§2.175 落盘后已 169/169），
并把 C16 重钉单列为交付七。此为 S-573（S-466/S-467 同族的第八次：把某时刻的值当不变式）。"""
import hashlib, json, os
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
LOCK=ROOT+'/lead/LEAD_LOCK'; BRD=T+'/STATUS_BOARD.md'; RC=T+'/R14_COMMON.md'
BAK=T+'/R17_LEAD_BASELINE'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

OLD='（C16 168 节 pinned 168、unpinned 0）'
NEW='（C16 **169 节 pinned 169**、unpinned 0；写入时是 168/168，本节落盘后按实测量重钉为 169/169，见 PA9）'
ck('N0 LEAD_LOCK 含旧口径恰 1 处', open(LOCK,encoding='utf-8').read().count(OLD)==1,
   open(LOCK,encoding='utf-8').read().count(OLD))
ck('N1 看板含旧口径恰 1 处', open(BRD,encoding='utf-8').read().count(OLD)==1,
   open(BRD,encoding='utf-8').read().count(OLD))

def patch(path,old,new,tag):
    b=open(path,'rb').read(); t=b.decode('utf-8')
    assert t.count(old)==1, (path,t.count(old))
    assert new not in t, 'already patched: '+tag
    bak=os.path.join(BAK,os.path.basename(path)+'.before_r170_'+tag+'.bak')
    if not os.path.exists(bak):
        fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
    open(path,'wb').write(t.replace(old,new).encode('utf-8'))
    back=open(path,'rb').read()
    ck('N2 '+tag+' 替换成功、CR 不变', back.count(b'\r')==b.count(b'\r') and new.encode('utf-8') in back,
       (b.count(b'\r'),back.count(b'\r')))
patch(LOCK,OLD,NEW,'LOCK_C16NOTE')
patch(BRD,OLD,NEW,'BOARD_C16NOTE')

PA9 = """

PA9. 🔴 **交付七：C16 随本节重钉（168 → 169 节），而 PA5 那句「C16 168 节 pinned 168」是**写入前**的事实 —— 当场改口.** §2.175 实测 **6,706 B** ⇒ 新下界 **3,353**（一半），逐节表 **168 → 169 节**、`C16_FLOORS_SHA256` `dc5e162a…` → **`bb7fe832…`**。**反控四条**：旧表重算命中旧常量 `dc5e162a…`；原有 **168** 条逐条不变；`GATE_VER` 仍 `R166` 未动；`C7_TEXT_SHA256` / `C14_TEXT_SHA256` / `FREEZE_SHA256` 三者一字未动（本轮未改 `DISC_RECHECK` / `DISC_UNVERIFIABLE` 任何一行）。三段实跑复验：`check_disc` exit 0 / FAIL 0，NOTE 逐字 `169 sections measured (pinned 169), hollow/deficient 0, missing 0, unpinned 0, min margin 20`；`facts_floors` exit 0（D0 `d85034b0` / D8 120,495 / D9 `90ff6911`）；`gate_runner` **G1=G2=G3=ok**（G3e 由 **169** 节重算 `bb7fe832`）。**S-573（第十三条自错，S-466/S-467 同族第八次）**：PA5 与看板段在**写入时**写 168/168 是对的，但那句话在 §2.175 落盘并重钉 C16 之后**立即过期** ⇒ 属「把某时刻的值当不变式」。族谱：S-426b → S-446 → S-464 → S-465 → S-466 → S-467 → **S-573**。
"""
b=open(LOCK,'rb').read()
assert PA9.encode() not in b
bak=os.path.join(BAK,'LEAD_LOCK.before_r170_PA9.bak')
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as f: f.write(b)
open(LOCK,'wb').write(b+PA9.encode('utf-8'))
ck('N3 PA9 恰 1 次', open(LOCK,encoding='utf-8').read().count('PA9.')==1, 1)
ck('N4 LEAD_LOCK CR 保持 137', open(LOCK,'rb').read().count(b'\r')==137, open(LOCK,'rb').read().count(b'\r'))

brd=open(BRD,'rb').read(); t=brd.decode('utf-8')
anchor='**G1=G2=G3=ok**。'
assert t.count(anchor)==1, t.count(anchor)
add=('**C16 随本节重钉**：§2.175 实测 **6,706 B** ⇒ 新下界 **3,353**，逐节表 **168 → 169 节**、`C16_FLOORS_SHA256` `dc5e162a…` → **`bb7fe832…`**；'
     '反控：旧表命中旧常量、原 168 条逐条不变、`GATE_VER` 仍 `R166`、`C7_TEXT`/`C14_TEXT`/`FREEZE` 三者一字未动；'
     '复跑 NOTE 逐字 `169 sections measured (pinned 169), hollow/deficient 0, missing 0, unpinned 0, min margin 20`。'
     '**S-573**：本条原写「168 节 pinned 168」，那是**写入前**的事实、落盘重钉后立即过期 ⇒ 同族第八次（S-426b→S-446→S-464→S-465→S-466→S-467→S-573）。\n\n')
open(BRD,'wb').write(t.replace(anchor,anchor+add,1).encode('utf-8'))
ck('N5 看板 CR 0 且行数 < 260', open(BRD,'rb').read().count(b'\r')==0 and open(BRD,'rb').read().count(b'\n')<260,
   open(BRD,'rb').read().count(b'\n'))
ck('N6 看板第 170 轮恰 1 段', open(BRD,encoding='utf-8').read().count('R17 第 170 轮')==1, 1)

json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),
           'stats':{p:{'bytes':len(open(p,'rb').read()),'cr':open(p,'rb').read().count(b'\r')} for p in (LOCK,BRD,RC)}},
          open(ROOT+'/_r170/r170n_fix_c16note.json','w'),ensure_ascii=False,indent=1)
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
