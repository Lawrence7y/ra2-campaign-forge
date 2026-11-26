import io, json, os, hashlib, re
SRC='lead/next_re_20261117_r14/R17_R109_FACTINDEX_V537/FACT_INDEX.tsv'
DSTD='lead/next_re_20261117_r14/R17_R110_FACTINDEX_V538'
DST=DSTD+'/FACT_INDEX.tsv'
BAK='lead/next_re_20261117_r14/R17_LEAD_BASELINE/FACT_INDEX.tsv.before_R140_v538_20261126_2058.bak'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-72s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
raw=open(SRC,'rb').read()
chk('v5.37 exists and is 79224 B', len(raw)==79224, str(len(raw)))
chk('v5.37 CR 0', raw.count(b'\r')==0)
chk('v5.37 LF 55', raw.count(b'\n')==55)
lines=raw.decode('utf-8').split('\n')
idx=[i for i,l in enumerate(lines) if l.startswith('F01\t')]
chk('one F01 row', len(idx)==1)
i=idx[0]; cols=lines[i].split('\t'); chk('5 cols', len(cols)==5)
lim=cols[4]
chk('R140 marker present (from v5.37)', 'R140' in lim)
chk('the retracted (b) claim is present', '不依赖任何数值阈值的第二条实现' in lim)
OLD="(b) **不依赖任何数值阈值的第二条实现**：在 1216 个候选上去掉「类名以 `.?AU` 开头」且只保留「被恰好一张虚表指回」者，实测同样得 **1211**；但两式选出的是**不同集合**（各差 3 个：式(a) 排除 3 个 0x5518 而保留 `DropPodLocomotionClass`/`INIEntry`/`INISection`，式(b) 反之）⇒ **1211 这个数有两种来源，但对应两批不同的 COL，引用时必须写明是哪一种**。"
NEW="(b) **曾被当作「不依赖数值阈值的第二条实现」，本轮已撤回**：先前在 1216 个候选上取「类名不以 `.?AU` 开头」且「只被恰好一张虚表指回」得 **1211**，跨家族审计员指出该式对「虚表」的定义敏感，主会话复算证实——把虚表判据换成 6 种同样合理的口径，「被指回次数 == 1」给出的是 **1203 / 1211 / 1212 / 1212 / 1212 / 1015** 四个互不相同的值（见 `_r140/r140y_c4b_invariance.py`）：全节 dword 命中 1203、仅 `.rdata` 1212、只要求 `dword[vt]` 落 `.text` 1212、再加 `.data/.rdata` 落盘 1212、要求 slot0+slot1 都落 `.text` 1015，**只有「`.data/.rdata` 内命中」这一种给 1211**，而它恰恰把 `.data` 里与 COL VA 相同的操作数也当成虚表（反证：`DropPodLocomotionClass` 的 5 处 `.data/.rdata` 命中里只有 1 处 `dword[vt]` 落 `.text`，另 4 处 slot0 是 `0xfebae900` 一类越界值，不是虚表）。⇒ **(b) 不是可引用口径，1211 只有 (a) 一条复现路径**，且 (a) 本身也无结构含义。"
chk('old (b) sentence found exactly once', lim.count(OLD)==1)
newlim=lim.replace(OLD,NEW)
chk('replacement applied', newlim!=lim and NEW in newlim)
chk('the retraction is marked as such (含「已撤回」)', '已撤回' in newlim)
chk('the old claim "两种来源" is gone', '这个数有两种来源' not in newlim)
chk('the new text gives the 4 observed values 1203/1211/1212/1015',
    all(k in newlim for k in ('1203','1211','1212','1015')))
print('      (limitations %d -> %d B ; a retraction may be longer than the claim it removes)' % (len(lim), len(newlim)))
cols[4]=newlim
newrow='\t'.join(cols); chk('5 cols after rebuild', len(newrow.split('\t'))==5)
out=list(lines); out[i]=newrow
newtxt='\n'.join(out); newraw=newtxt.encode('utf-8')
chk('CR still 0', newraw.count(b'\r')==0)
chk('LF still 55', newraw.count(b'\n')==55)
chk('exactly one line changed', sum(1 for a,b in zip(lines,out) if a!=b)==1)
chk('other 54 lines byte-identical', all(a==b for k,(a,b) in enumerate(zip(lines,out)) if k!=i))
def grades(ls): return [l.split('\t')[2] for l in ls if l and '\t' in l]
chk('grade column unchanged for all 55 rows', grades(lines)==grades(out))
chk('v5.37 source untouched', hashlib.sha256(open(SRC,'rb').read()).hexdigest()==hashlib.sha256(raw).hexdigest())
os.makedirs(DSTD, exist_ok=True)
chk('dest does not exist', not os.path.exists(DST))
fd=os.open(BAK, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,raw); os.close(fd)
chk('backup wx created, bytes match', os.path.getsize(BAK)==79224)
open(DST,'wb').write(newraw)
back=open(DST,'rb').read()
chk('readback identical', back==newraw)
chk('readback CR0/LF55', back.count(b'\r')==0 and back.count(b'\n')==55)
print()
print('v5.38 : %d B  sha %s  (v5.37 was 79224)' % (len(back), hashlib.sha256(back).hexdigest()[:16]))
print('ASSERTIONS: %d PASS' % (A-1))
