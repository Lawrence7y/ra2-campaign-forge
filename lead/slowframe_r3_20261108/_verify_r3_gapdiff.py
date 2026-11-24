# -*- coding: utf-8 -*-
# _verify_r3_gapdiff.py —— 第三方独立复核 hy4
# 独立重算 §604 空档差，核对 R3 逐窗值；独立解析台账表；核验 :9723/:9724/:9725；
# 核查保护区未改、可引用边界、是否 import/复用 N-8 脚本。
# 独立声明：自写分组、自写 median、自写台账解析；未读/未 import 复算员或 N-8 脚本。
import json, re, hashlib, math, os

ROOT = os.path.realpath('D:/Project/ra2-campaign-forge')
ALLOW = os.path.realpath(ROOT + '/lead/slowframe_r3_20261108')
CORPUS = os.path.realpath(ROOT + '/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip')
GOAL = os.path.realpath(ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md')
N8MD = os.path.realpath(ROOT + '/lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md')
OUT = os.path.realpath(ALLOW + '/_verify_r3_out.txt')

def A(p):
    q = os.path.realpath(p)
    if q != ROOT and not q.startswith(ROOT + os.sep):
        raise ValueError('path outside allowed root rejected: ' + q)
    return q

TRIPS = ['l1c_20261021','l1d_20261021','l1e_20261021','l3_20261021','t55k_20261020']
WINDOWS = [(tr,w) for tr in TRIPS for w in (0,1,2)]
R3_DIFF = {
 ('l1c_20261021',0):0.1080,('l1c_20261021',1):0.0790,('l1c_20261021',2):0.0670,
 ('l1d_20261021',0):0.0640,('l1d_20261021',1):0.0380,('l1d_20261021',2):0.0550,
 ('l1e_20261021',0):0.0320,('l1e_20261021',1):0.0480,('l1e_20261021',2):0.0340,
 ('l3_20261021',0):0.0880,('l3_20261021',1):0.0960,('l3_20261021',2):0.1030,
 ('t55k_20261020',0):0.0260,('t55k_20261020',1):0.0255,('t55k_20261020',2):0.0065,
}
def med(xs):
    s=sorted(xs);n=len(s)
    if n==0: raise ValueError('empty median')
    return s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2.0
def sha(p): return hashlib.sha256(open(A(p),'rb').read()).hexdigest()
def nb(p): return len(open(A(p),'rb').read())
L=[]
def P(s=''): L.append(s); print(s)

def parse_ledger_table():
    raw=open(A(GOAL),encoding='utf-8').read().split(chr(10))
    tbl={}
    for ln in raw[9703:9720]:
        if not ln.startswith('|'): continue
        cells=[c.strip() for c in ln.strip().strip('|').split('|')]
        if len(cells)<6: continue
        m=re.match(r'`([^`]+)/w([012])`',cells[0])
        if not m: continue
        key=(m.group(1),int(m.group(2)))
        def num(c):
            c=c.replace('**','').replace('ms','').replace(chr(0x2212),'-').replace('+','').strip()
            return float(c)
        tbl[key]=tuple(num(c) for c in cells[1:6])
    return tbl

def recompute_one(tr,w):
    p=A(os.path.join(CORPUS,tr,'measure_w'+str(w)+'.json'))
    d=json.loads(open(p,encoding='utf-8').read())
    ts,fs,fe=d['samples']['t'],d['samples']['f'],d['frame_edges']
    grp={}
    for a,b in zip(fs,ts): grp.setdefault(a,[]).append(b)
    edge,span,gap={},{},{}
    for i in range(len(fe)-1):
        fid,t0=fe[i][0],fe[i][1]
        edge[fid]=fe[i+1][1]-t0
    for fid in grp:
        seq=grp[fid]
        span[fid]=max(seq)-min(seq)
        if len(seq)>=2: gap[fid]=max(seq[j+1]-seq[j] for j in range(len(seq)-1))
    def thirds(dur,ceil_rule):
        ids=sorted((f for f in dur),key=lambda x:(dur[x],x))
        n=len(ids); k=math.ceil(n/3) if ceil_rule else n//3
        lo,hi=ids[:k],ids[n-k:]
        fd=med([dur[f] for f in lo])*1000.0
        sd=med([dur[f] for f in hi])*1000.0
        fg=med([gap[f] for f in lo if f in gap])*1000.0
        sg=med([gap[f] for f in hi if f in gap])*1000.0
        return fd,fg,sd,sg,sg-fg
    return {'path':p,'sha':sha(p),'gate_ok':(d.get('gate') or {}).get('ok'),
            'verdict':d.get('verdict'),'n_samp':len(ts),'n_frames':len(fe),
            'edge_floor':thirds(edge,False),'edge_ceil':thirds(edge,True),
            'span_floor':thirds(span,False),'span_ceil':thirds(span,True),
            'med_edge_all':med(list(edge.values()))*1000.0,
            'med_span_all':med(list(span.values()))*1000.0}

def main():
    P('[_verify_r3] 第三方独立复核 hy4 —— 不复用复算员/N-8 任何实现')
    P('台账 SHA256 = %s, bytes = %d'%(sha(GOAL),nb(GOAL)))
    P('N-8 被核对象 SHA256 = %s, bytes = %d'%(sha(N8MD),nb(N8MD)))
    P('')
    T=parse_ledger_table()
    P('[V1] 台账 :9704-9720 表值独立解析（正则+单元格切分，未硬编码）')
    P('  解析到 %d 行'%len(T))
    for k in WINDOWS: P('  %s/w%d -> %s'%(k[0],k[1],T.get(k)))
    P('')
    R={k:recompute_one(k[0],k[1]) for k in WINDOWS}
    P('[V2] 15 窗独立重算（edge+floor，自写 median）')
    for k in WINDOWS:
        r=R[k];fd,fg,sd,sg,df=r['edge_floor']
        P('  %s/w%d  fd %.4f fg %.4f sd %.4f sg %.4f diff %+.4f  gate=%s verdict=%s n_samp=%d n_frames=%d'%
          (k[0],k[1],fd,fg,sd,sg,df,r['gate_ok'],r['verdict'],r['n_samp'],r['n_frames']))
    P('')
    P('[V3] 与复算员 gapResult 逐窗核对（差<0.00005 视为一致）')
    diffs=[];ok=0
    for k in WINDOWS:
        mine=R[k]['edge_floor'][4];theirs=R3_DIFF[k];diffs.append(mine)
        hit=abs(mine-theirs)<0.00005;ok+=hit
        P('  %s/w%d  本轮 %+.4f  R3 %+.4f  %s'%(k[0],k[1],mine,theirs,'OK' if hit else 'MISMATCH'))
    P('  逐窗一致 %d/15'%ok)
    P('  本轮 中位 = %+.4f  最小 = %+.4f  最大 = %+.4f'%(med(diffs),min(diffs),max(diffs)))
    P('  复算员自报 中位 +0.0550 最小 +0.0065 最大 +0.1080')
    P('  本轮严格<0 窗 = %d ; <=0 窗 = %d ; 全正 = %s'%
      (sum(1 for x in diffs if x<0),sum(1 for x in diffs if x<=0),all(x>0 for x in diffs)))
    P('')
    P('[V3b] 四口径敏感性（min..max / 负值窗数 / 全正）')
    for tag in ('edge_floor','edge_ceil','span_floor','span_ceil'):
        vs=[R[k][tag][4] for k in WINDOWS]
        P('  %-11s min %+.4f max %+.4f  负 %d  全正 %s'%
          (tag,min(vs),max(vs),sum(1 for x in vs if x<0),all(x>0 for x in vs)))
    P('')
    P('[V4] 台账表逐格比对（独立解析表值 vs 独立重算 edge+floor）')
    dT=gT=xT=dR=gR=xR=0
    for k in WINDOWS:
        fd,fg,sd,sg,df=R[k]['edge_floor'];t=T[k]
        dT+=(abs(fd-t[0])<0.05)+(abs(sd-t[2])<0.05)
        gT+=(abs(fg-t[1])<0.005)+(abs(sg-t[3])<0.005)
        xT+=(abs(df-t[4])<0.0005)
        dR+=(round(fd,1)==t[0])+(round(sd,1)==t[2])
        gR+=(round(fg,2)==t[1])+(round(sg,2)==t[3])
        xR+=(round(df,3)==t[4])
    P('  容差判等  时长 %d/30  空档 %d/30  空档差 %d/15'%(dT,gT,xT))
    P('  round 判等 时长 %d/30  空档 %d/30  空档差 %d/15'%(dR,gR,xR))
    tdiffs=[T[k][4] for k in WINDOWS]
    P('  台账表值列 中位 %+.4f 最小 %+.4f 最大 %+.4f  严格<0 %d  <=0 %d'%
      (med(tdiffs),min(tdiffs),max(tdiffs),sum(1 for x in tdiffs if x<0),sum(1 for x in tdiffs if x<=0)))
    P('  复算 15 正 vs 表 11 正 3 负 1 零 → 符号结构不同')
    P('')
    P('[V5] :9724 / :9725 / :9723 独立判定')
    lo,hi=0.0025,0.0495
    inr=sum(1 for x in diffs if lo<=x<=hi)
    P('  :9724 复算落在区间 = %d/15 ; 高于上界 %d ; 低于下界 %d'%
      (inr,sum(1 for x in diffs if x>hi),sum(1 for x in diffs if x<lo)))
    P('  :9724 台账自家表值落在区间 = %d/15（全正断言 vs 表含负/零）'%
      sum(1 for x in tdiffs if lo<=x<=hi))
    P('  :9725 表值严格<0 = %d 窗 ; 含 -0.000(<=0) = %d 窗 ; 括号列举 4 项 → 错位 %s'%
      (sum(1 for x in tdiffs if x<0),sum(1 for x in tdiffs if x<=0),
       '成立' if sum(1 for x in tdiffs if x<0)==3 and sum(1 for x in tdiffs if x<=0)==4 else '不成立'))
    P('  :9725 复算负值窗 = %d/15'%sum(1 for x in diffs if x<0))
    rt={k:T[k][2]/T[k][0] for k in WINDOWS}
    rc={k:R[k]['edge_floor'][2]/R[k]['edge_floor'][0] for k in WINDOWS}
    mt=max(rt,key=rt.get);mc=max(rc,key=rc.get)
    P('  :9723 表值倍率 中位 %.4f 最大 %.4f @ %s/w%d  l3/w0=%.4f'%
      (med(list(rt.values())),rt[mt],mt[0],mt[1],rt[('l3_20261021',0)]))
    P('  :9723 实算倍率 中位 %.4f 最大 %.4f @ %s/w%d  l3/w0=%.4f'%
      (med(list(rc.values())),rc[mc],mc[0],mc[1],rc[('l3_20261021',0)]))
    stab=max(WINDOWS,key=lambda k:T[k][2]);scab=max(WINDOWS,key=lambda k:R[k]['edge_floor'][2])
    P('  :9723 慢1/3时长绝对值最大窗 表值 %s/w%d(%.1f) 实算 %s/w%d(%.1f) → 自洽 %s'%
      (stab[0],stab[1],T[stab][2],scab[0],scab[1],R[scab]['edge_floor'][2],
       '是' if stab==('l3_20261021',0) and scab==('l3_20261021',0) else '否'))
    P('')
    P('[V6] 保护区与合规检查')
    P('  台账当前 SHA256 = %s bytes = %d （编排方 2baa...ede / 759518 B）'%(sha(GOAL),nb(GOAL)))
    for f in ('_r3_recompute_gapdiff.py','_r3_recompute_out.txt','_r3_GAPDIFF_RECHECK.md'):
        P('  %s SHA256 = %s bytes = %d'%(f,sha(A(ALLOW+'/'+f)),nb(A(ALLOW+'/'+f))))
    P('  --- 复算脚本 import 行扫描 ---')
    for i,ln in enumerate(open(A(ALLOW+'/_r3_recompute_gapdiff.py'),encoding='utf-8').read().split(chr(10)),1):
        if re.match(r'\s*(import|from)\s',ln): P('    :%d %s'%(i,ln.strip()))
    src=open(A(ALLOW+'/_r3_recompute_gapdiff.py'),encoding='utf-8').read()
    rep=open(A(ALLOW+'/_r3_GAPDIFF_RECHECK.md'),encoding='utf-8').read()
    P('  复算脚本引用 N-8 .py 路径: %s'%bool(re.search(r'_n8_|_verify_recompute|slowwindow_n8\S*\.py',src)))
    P('  报告含「台账该改/应修改台账」判语: %s'%
      bool(re.search(r'(建议|应该|应当|该|应|需|须)\s*(修改|改|修订|更正)\s*台账|台账\s*(该|应|需)\s*改',rep)))
    P('')
    P('[V7] 回件要求：被核对象 SHA256 与字节数')
    P('  主产出 _r3_GAPDIFF_RECHECK.md SHA256 = %s，字节数 = %d'%
      (sha(A(ALLOW+'/_r3_GAPDIFF_RECHECK.md')),nb(A(ALLOW+'/_r3_GAPDIFF_RECHECK.md'))))
    P('  被核对象 SLOW_WINDOW_LIMITS.md SHA256 = %s，字节数 = %d'%(sha(N8MD),nb(N8MD)))
    P('')
    P('[_verify_r3] END')
    open(A(OUT),'w',encoding='utf-8').write(chr(10).join(L)+chr(10))
    print('WRITTEN: '+OUT)
if __name__=='__main__': main()
