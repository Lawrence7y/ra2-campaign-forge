# -*- coding: utf-8 -*-
"""R218 p6：STATUS_BOARD 第 218 轮记录（全 LF，CR=0，总行数 <= 300）。
当前 251 行，追加 ~10 行 => 261 行，低于 260 阈值判据需先归档。
规则：若追加后 > 260，先归档最早 2 段到 BOARD_ARCHIVE（ARCH CR 保持 2952）。
"""
import os,hashlib,re
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/R17_LEAD_BASELINE'
B=T+'/STATUS_BOARD.md'; A=T+'/BOARD_ARCHIVE.md'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r218_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted '+tag)
SEC="""
## 第 218 轮（2026-11-28）虚表口径二分（1214 真表 + 4 幻影）+ BCD 24 B 订正 + 464 高槽归因 + disp 扫描定稿

- **1218 张虚表非同质**：`dw(V-4)==COL` 候选 1218，`dw(V)` 落 `.text` 的只有 **1214**。4 个 `.data` 幻影 `0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`（形态 `c0000001 00000000 00000000 00800040`，槽 0，`.text` 内引用 0；正控 `0x7e8278` 4 次）⇒ 真表与 **1214** 条 COL **双射**，R217「共用 COL 0x800040」在真表口径下不存在。
- **264 vs 260 差 4 的解释改写**：`mdisp!=0` 视图含幻影 264、真表口径 260，差 4 即幻影，不是「5 张视图共用一 COL」。总槽 **14044**、主视图 **954**/slot≥3 **9958** 与 R217 逐数一致。
- **BCD 记录 24 B 订正（自错 E6）**：pBCA 是 4 B 指针数组；元素 `+0` 合法 pTD **94/94**，反控按 0x1c 步长 **0/94**，`+0x18` 合法 pTD 84/94（= 下条记录 `+0`）⇒ 「+0x18 为 pCHD」「内联记录数组」作废。
- **464 高槽归因**：父类 6/6 PASS（Unit/Infantry/Aircraft→Foot；Foot/Building→Techno；Techno→Radio）；**cov 294 / diff 67 / oob 103**，父类范围内覆盖 **81.44%**；oob == Σmax(0, n−max(par_n,256))；464 目标去重 170、本表低槽重复 1、全表任意子段最大公共前缀 ≥12 的拼接候选 **0**（反控 10 对为 0）。
- **disp 扫描定稿**：逐字节 sweep **1,394,120** 条指令；`call/jmp [reg+disp]`（排除 esp）**18,930**；`disp==0x2c` 1114 / `disp==0` 819 / `disp==0x48` 930；slot≥256 **931** 位点 / **91** 个 s / 非 4 对齐 **0**；925 落 UnitClass 槽域、6 处超 344 待定性。**931 与 R215「931 处 +0x48」是巧合（实测 930）**。
- **自错 3 条 0 进结论**：固定 64 KB 切块截断 / 按末完整指令推进遇非法字节不足 / 指针数组当内联记录。card C(#567) 六数独立复算一致；card A(#565) **failed / error_max_turns / 61 回合 / 9.3′ vs 12**；card B(#566) succeeded。
- **建账**：FACT_INDEX **V599→V600**（仅 F29 一行）277566→**280689** B、sha `616a86e2`→**`fb513cc8`**；facts_floors MASTER→**`37c8063f`**、gate_runner LEDGER→V600、指针同步。
- **收口**：m11 **34 断言 0 FAIL**；R14 §2.226 CR 1081、GOAL §1276 CR 337、本段 QL CR 137、本段 CR 0。三门 exit 0（check_disc live 31 / C19 `fb513cc8`/280689/V600 / C20 V600；facts_floors D0–D10；gate_runner G1 G2 G3a–G3f）。
"""
b0=bak(B,'BOARD'); txt=b0.decode()
assert b0.count(b'\r')==0
lines=txt.split('\n')
print('[前置] 看板行数（含末尾空段）=%d'%len(lines))
add=SEC.count('\n')
new_lines=len(lines)+add-1
print('[预估] 追加后约 %d 行'%new_lines)
if new_lines>260:
    # 归档最早 2 段
    idx=[i for i,l in enumerate(lines) if l.startswith('## ')]
    print('[归档] 段头 %d 个，最早两段起点 %r'%(len(idx),idx[:2]))
    cut=idx[2] if len(idx)>2 else len(lines)
    moved='\n'.join(lines[:cut])+'\n'
    rest='\n'.join(lines[cut:])
    a0=open(A,'rb').read(); assert a0.count(b'\r')==2952
    abak=bak(A,'ARCH')
    an=a0+moved.encode('utf-8')
    assert an.count(b'\r')==2952,'ARCH CR %d'%an.count(b'\r')
    open(A,'wb').write(an)
    a1=open(A,'rb').read(); assert a1.startswith(a0) and a1.count(b'\r')==2952
    print('[归档] ARCH bytes %d -> %d CR=%d'%(len(a0),len(a1),a1.count(b'\r')))
    txt=rest
    lines=txt.split('\n')
    print('[归档] 看板剩余行数 %d'%len(lines))
assert txt.count('\r')==0
new=txt+SEC
nb=new.encode('utf-8')
assert nb.count(b'\r')==0, 'BOARD CR %d'%nb.count(b'\r')
open(B,'wb').write(nb); chk=open(B,'rb').read()
final_lines=chk.count(b'\n')
print('[写入] BOARD bytes %d -> %d CR=%d LF=%d 行数上限 %s'%(len(b0),len(chk),chk.count(b'\r'),final_lines,'OK' if final_lines<=300 else 'BREACH'))
assert chk.count(b'\r')==0 and final_lines<=300
