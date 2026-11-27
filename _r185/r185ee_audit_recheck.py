#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 EE：主会话复算审计 #445 与执行员 #444 的每条「不符/越界」主张（§2.12 规则 D）。
主张：
  E1 954 条 TD 名里 952 是 .?AV、2 条是 .?AU（INIEntry@INIClass / INISection@INIClass）
  E2 二进制全域「RTTI 形 vtable」有 1215 个（954 在 symbols、261 不在），mdisp!=0 共 231、mdisp==4 另 79 个
  E3 88 条 col_va 各自被同 pTD 组内另一个 vtable 槽引用（即确属次 COL）
"""
import sys,json,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;RAW=P.RAW
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
TD=set()
s=P.B['.data']; blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
i=0
while True:
    i=blob.find(b'.?A',i)
    if i<0: break
    e=blob.find(b'\0',i,i+400)
    if e<0: i+=1; continue
    nm=blob[i:e]
    if nm.endswith(b'@@') and len(nm)>6:
        va=s['lo']+i-8
        if where(va)=='.data' and dw(va)==0x7F9594 and dw(va+4)==0: TD.add(va)
    i+=1
COLS={}
for sec in ('.rdata','.data'):
    ss=P.B[sec]; b2=RAW[ss['rawptr']:ss['rawptr']+ss['rawsize']]
    vals=struct.unpack_from('<%dI'%(len(b2)//4),b2,0)
    for i2,v in enumerate(vals):
        if v not in TD: continue
        for base in (ss['lo']+4*i2-12, ss['lo']+4*i2):
            d=[dw(base+4*k) for k in range(5)]
            if None in d or d[0] not in (0,1) or d[2]!=0: continue
            if d[3] not in TD or where(d[4])!='.rdata': continue
            ch=[dw(d[4]+4*k) for k in range(4)]
            if None in ch or ch[0]!=0 or ch[2]<1 or where(ch[3])!='.rdata': continue
            COLS[base]=d
vt_all=set()
for sec in ('.rdata','.data'):
    ss=P.B[sec]; vals=struct.unpack_from('<%dI'%(ss['rawsize']//4),RAW,ss['rawptr'])
    for i2,v in enumerate(vals):
        if 0x401000<=v<0x7E038D:
            va=ss['lo']+4*i2
            if dw(va-4) in COLS: vt_all.add(va)
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))['classes']
print('枚举：TD=%d COL=%d vt_all=%d'%(len(TD),len(COLS),len(vt_all)))
# E1
pref=collections.Counter()
for k,c in S.items():
    if c['vtable_va'] is None: continue
    r=dw(int(c['vtable_va'],16)-4); nm=cstr(COLS[r][3]+8).decode('latin1')
    pref[nm[:4]]+=1
ck('E1 954 条 TD 名前缀分布 == {.?AV:952, .?AU:2}', dict(pref)=={'.?AV':952,'.?AU':2}, dict(pref))
au=[k for k,c in S.items() if c['vtable_va'] is not None and
    cstr(COLS[dw(int(c['vtable_va'],16)-4)][3]+8).startswith(b'.?AU')]
ck('E1b 两条 .?AU 类名 == INIEntry@INIClass / INISection@INIClass', sorted(au)==['INIEntry@INIClass','INISection@INIClass'], au)
# E2
sv={int(c['vtable_va'],16) for c in S.values() if c['vtable_va'] is not None}
ck('E2 全域 vt_all 数（本判据）== 1214', len(vt_all)==1214, len(vt_all))
ck('E2b symbols 的 vtable 全部落在 vt_all 内', sv<=vt_all, [hex(x) for x in sorted(sv-vt_all)[:5]])
md_all=collections.Counter(COLS[dw(v-4)][1] for v in vt_all)
md_sym=collections.Counter(COLS[dw(v-4)][1] for v in sv)
ck('E2c 全域 mdisp!=0 的 vtable 数', True, '%d（mdisp==4 的 %d）'%(sum(c for m,c in md_all.items() if m!=0), md_all[4]))
ck('E2d symbols 内 mdisp!=0 的 vtable 数 == 12（全 mdisp==4）', sum(c for m,c in md_sym.items() if m!=0)==12, sum(c for m,c in md_sym.items() if m!=0))
outside=vt_all-sv
ck('E2e 不在 symbols 的 vt_all == %d'%len(outside), True, len(outside))
mo=collections.Counter(COLS[dw(v-4)][1] for v in outside)
ck('E2f 不在 symbols 的 vtable 的 mdisp 分布', True, dict(sorted(mo.items())))
# 审计主张 1215 / 231 / 79 —— 逐条判
ck('E2g 审计「全域 1215 个」与本判据 1214 不符 ⇒ 该主张不成立（差 1 来自虚表判据口径）',
   len(vt_all)!=1215, len(vt_all))
ck('E2h 审计「mdisp!=0 共 231」与本判据实测比对',
   True, '本判据 %d vs 审计 231'%sum(c for m,c in md_all.items() if m!=0))
ck('E2i 审计「mdisp==4 另 79 个且无一是 Locomotion」与本判据实测比对', True,
   '本判据 symbols 外 mdisp==4 的 %d 个'%mo[4])
# 这 79/XX 个 mdisp==4 的类名
m4_out=[]
for v in sorted(outside):
    r=dw(v-4)
    if COLS[r][1]==4:
        nm=cstr(COLS[r][3]+8)
        m4_out.append((hex(v),nm.decode('latin1') if nm else None))
ck('E2j symbols 外 mdisp==4 的 vtable 无一是 Locomotion', all('Locomotion' not in (x[1] or '') for x in m4_out), len(m4_out))
print('NOTE symbols 外 mdisp==4 前 8:',m4_out[:8])
# E3
byp=collections.defaultdict(set)
for v in vt_all: byp[dw(v-4)].add(v)
s88=[]
for k,c in S.items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); cv=int(c['col_va'],16)
    if cv!=dw(vt-4): s88.append((k,vt,cv))
ck('E3 88 条 col_va 与 vtable-4 不同', len(s88)==88, len(s88))
okref=sum(1 for k,vt,cv in s88 if cv in COLS and len(byp.get(cv,()))>0)
ck('E3b 这 88 个次 COL 各自仍被某个 vtable 槽以 [-4] 指回', okref==88, okref)
json.dump({'td':len(TD),'col':len(COLS),'vt_all':len(vt_all),'sym':len(sv),'outside':len(outside),
  'md_all':{str(k):v for k,v in sorted(md_all.items())},'md_out':{str(k):v for k,v in sorted(mo.items())},
  'pref':dict(pref),'au':sorted(au),'s88_ref':okref,'checks':n,'fails':fails},
  open('/home/t628/projects/ra2-campaign-forge/_r185/r185ee.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
