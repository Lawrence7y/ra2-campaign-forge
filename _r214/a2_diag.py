# -*- coding: utf-8 -*-
"""诊断 a1 与 ex1/ex2 的 14043 vs 14044 一格差：定位具体是哪张视图、差在哪一格。
口径 A（a1）：end = 下一视图起点（严格 <），末张 end=.text hi_file。
口径 B：与 ex1 相同（ex1 用「下一 vftable 起点」，末张用 .text hi_file），并额外报告：
        若允许 a<=end 会多出哪些槽。
"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
def words(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), s['lo']
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-4):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=(s32(w[k+1]),w[k+3],w[k+4],nm.decode('latin1'))
PA=collections.defaultdict(list)
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-1):
        if w[k] in COL and P.where(w[k+1])=='.text': PA[w[k]].append(base+4*k)
starts=sorted(min(v)+4 for v in PA.values() if len(v)==1)
print('COL=%d starts=%d first=%s last=%s .text=[%s,%s) .rdata=[%s,%s)'%(
  len(COL),len(starts),hex(starts[0]),hex(starts[-1]),
  hex(P.B['.text']['lo']),hex(P.B['.text']['hi_file']),
  hex(P.B['.rdata']['lo']),hex(P.B['.rdata']['hi_file'])))
# 每张视图：严格 < 下一张
totA=0; per={}
for i,st in enumerate(starts):
    end=starts[i+1] if i+1<len(starts) else P.B['.text']['hi_file']
    n=0; a=st
    while a<end and P.where(P.dw(a))=='.text': n+=1; a+=4
    per[st]=(n,a)  # a = 停止地址
    totA+=n
print('严格< 口径总槽=%d'%totA)
# 检查：每张视图停止地址处的值到底是什么；若停止地址 < end 且那里是非 .text，记录
stopHits=[]
for st,(n,a) in per.items():
    end=starts[starts.index(st)+1] if starts.index(st)+1<len(starts) else P.B['.text']['hi_file']
    if a<end:
        stopHits.append((hex(st),n,hex(a),P.where(P.dw(a)),hex(P.dw(a) or 0),'gap=%d'%(end-a)))
print('提前停止的视图数=%d（停止处非 .text 指针）'%len(stopHits))
for x in stopHits[:20]: print('   start=%s n=%d stop=%s where=%s val=%s %s'%x)
# 若这些停止处之后的下一格仍是 .text，说明视图在此处中间有一段非 vftable 数据
extra=0
for st,(n,a) in per.items():
    if P.where(P.dw(a+4))=='.text' and a+4<P.B['.text']['hi_file']:
        extra+=1
print('停止后 +4 又是 .text 的视图数=%d（说明槽序列被非指针数据截断，符合预期）'%extra)
print('差额 = 14044 - %d = %d'%(totA,14044-totA))
# 找出「差 1」的候选：ex1 报最小视图 1 槽 199 张；a1 统计槽=1 的视图数
c1=sum(1 for st,(n,a) in per.items() if n==1)
print('a1 中 1 槽视图数=%d（ex1 报 all ndist 1:199）'%c1)
print('总视图=%d'%len(per))
