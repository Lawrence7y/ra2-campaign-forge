#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 落盘三：STATUS_BOARD 归档（272 >= 260，归档最早 2 段）+ 追加第 205 轮。"""
import os,hashlib,time,json,re
G='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL='/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

bs=G+'/STATUS_BOARD.md'; ar=G+'/BOARD_ARCHIVE.md'
ck('B0 看板 CR == 0',crc(bs)==0,crc(bs))
ck('B1 归档 CR == 2952',crc(ar)==2952,crc(ar))
lines_before=len(open(bs,'rb').read().split(b'\n'))-1
ck('B2 开局行数 >= 260 需归档',lines_before>=260,lines_before)
b1=backup(bs,'_BOARD'); b2=backup(ar,'_ARCHIVE')
ck('B3 两份备份一致',sha(b1)==sha(bs) and sha(b2)==sha(ar),None)

raw=open(bs,'rb').read(); txt=raw.decode('utf-8')
ck('B4 全 LF（无 CR）',b'\r' not in raw,None)
segs=[]; idx=[]
for m in re.finditer(r'^## ',txt,re.M):
    idx.append(m.start())
idx.append(len(txt))
for i in range(len(idx)-1): segs.append(txt[idx[i]:idx[i+1]])
ck('B5 段数 >= 2',len(segs)>=2,len(segs))
head=txt[:idx[0]]
arch=segs[0]+segs[1]
rest=head+''.join(segs[2:])
print('   归档段标题:')
for s in segs[:2]:
    print('     '+s.split('\n')[0][:120])

a_raw=open(ar,'rb').read()
new_ar=a_raw+(b'' if a_raw.endswith(b'\n') else b'\n')+arch.encode('utf-8')
open(ar,'wb').write(new_ar)
ck('B7 归档后 CR 仍 2952',crc(ar)==2952,crc(ar))
ck('B7b 归档新增 2 段',len(new_ar)>len(a_raw),len(new_ar)-len(a_raw))

R205 = (
'## \U0001F7E2 R17 第 205 轮（2026-11-28 14x）· CHD 记录实为 40 字节，+16 处内嵌本类主对象 COL；'
'两个 954 差 94 个 MI 类；978 条 mdisp==0 三分解；79 个 8 长段 = AbstractClass 单继承链\n\n'
'**订正（结构级，取得 R204 未取得项④）.** R204 把 CHD 当 16 字节是**截断**，真跨度 **40 字节**，954/954 逐字段成立：'
'+0 恒 0 / +4 为 attributes {0:855,1:66,5:33} / +8 为 numBaseClasses 恒等于 len(BCA) / +12 为 pBCA 全在 .rdata / '
'**+16 起 20 字节是完整 COL 记录**（sig 0、mdisp 0、cdOffset 0、pTD 在 .data、**pCHD 等于该 CHD 自身地址**）/ +24 恒 0 / +36 是终点（起点改 +36 后 0/954 命中）。'
'⇒ 类 RTTI 是自包含块 [BCD 数组][BCA 数组][40 字节 CHD 含内嵌主对象 COL]。'
'判据强度：六条逐级累加在 954 真值恒 954/954，剔除真值后 20,000 个 .rdata 随机地址假阳 +0==0 得 5,056 → +24==0 得 3,536 → **+32==自身 得 0**（后续四条全余加固 0）；七档错位 0/954；.data 段 20,000 随机 0。\n\n'
'**交付一·两个 954 不是同一批（消除 R203 混同风险）.** R203 组头（组内 mdisp 最大首视图）与 R205 内嵌主对象 COL（mdisp==0 末视图）'
'**交集 860**、差 **94** 全为多视图 MI 类；每组 mdisp==0 视图唯一且就是 CHD+16（954/954）；954 组头与 954 CHD 一一映射。'
'计数全复现 R203：vftable 起点 **1214**（vt 地址口径）/组头 **954**/被吞伪起点 **260**/视图 **1214**，视图数分布 1:860/2:10/3:6/4:76/5:1/7:1；每个 COL 恰被 1 个 vt 引用（1214/1214）。\n\n'
'**交付二·978 条 mdisp==0 三分解.** **956** 条自有（覆盖 954 个 TD；INoticeSource 与 VectorClass<H> 各 2 条）+ **22** 条非自有（21 个 TD；UIUnknown 2 条为 0x7fa9e8 与 0x7fb080）。'
'22 条逐条：名字全不在 954 类名集；**17 条 .?AU 接口 + 5 条 .?AV**；pTD **从不出现于任何 COL.pTD**（无 vftable 视图），却在 BCA 被引用 **474** 次且**从不在 BCA[0]**。'
'被继承次数 top5：UIUnknown 98 / UIUnknown 91 / UIPersist 90 / UIPersistStream 90 / UIClassFactory 78。'
'⇒ R204 充要律「mdisp==0 等价于自有 pTD」**只在 954 类内部成立**，全池 22 条反例为纯接口基类。\n\n'
'**交付三·取得 R204 未取得项③（79 个 8 长段成因）.** 原序切段复现全部 R204 数字（相邻对 1661 / -24 占 973 / 段数 **1642** / 单元素 76.2% / 段长全分布）。'
'79 个 8 长段：跨度恒 **168 字节**；**78 个**首元素是 **.?AVAbstractClass@@**，pTD 名序列完全一致 '
'AbstractClass/UIPersistStream/UIPersist/UIUnknown/UIRTTITypeInfo/UIUnknown/INoticeSink/INoticeSource，mdisp 恒 (0,0,0,0,4,4,8,12)；'
'唯一例外是 .?AVSidebarClass@@（mdisp 全 0）。68 个是该类 BCA 的最后一段。阈值敏感性 6/7/8/9/10 得 3/1/79/0/1 ⇒ 8 是内容产物不是网格产物。\n\n'
'**自错 14 组，0 条进结论.** （1）R204「954 条自有」被误读为「每 BCA 恰 1 条」；（2）类级与视图 COL 相交方向写反（实测 954 全包含）；'
'（3）cname 取 TD 应为 TD+8，把 +8 当 cdOffset 应为 +24；（4）**COL.sig 假设有区分力被「1214 条全 0」砸掉**（否定结果进结论）、claimed 混装两类地址致组头 1214；'
'（5）seps 存 vt-4 而 VTI 键为 vt（组头 1214 修正为 954）；（6）三元判据在随机池报 0 命中实测 90 命中，**逐条核实全部是真 CHD**（池未剔除真值）；'
'（7）sorted(BCA) 切段得 1610 与 R204 的 1642 口径不等价；（8）**把 vftable 槽 0 内容当起点得 891**（正确 1214）；'
'（9）「组内 mdisp **严格**递减」不成立，3 例外（OverlayClass 0x807598 序列 12,4,8,0；SmudgeClass 0x809848 序列 12,4,8,0；TerrainClass 0x80c370 序列 4,12,8,0），R203 原述「**末端**恒 mdisp==0」仍 954/954；'
'（10）m18 的 T2/T6/T9a 三条断言写错。\n\n'
'**跨家族.** 执行员 **#518**（hy4）独立复算 X1=1214 / X3=954 / X4=954 / X5=954 / X6=954 / X7={"1":954} / X8={978,956,22} **逐数一致**；'
'其 **X2=891 与 C1=132 假阳**由主会话 m16_final_vti.py（15 断言 0 FAIL）复算订正（891 是槽 0 内容去重、132 全部是真 CHD）。'
'审计员 **#519**（deepseek）见 R14_COMMON 2.210 第八节；全部结论由主会话 m12_ctl2.py(14 断言)/m16_final_vti.py(15)/m17_runs.py(10)/m18_e8.py(18) 亲跑复算。\n\n'
'**落盘.** R14_COMMON **2.210** CR 保持 **1081**（93055f73 到 04368a04，增加 9,062 字节）；GOAL **1260** CR 保持 **337**（0827b546 到 dac1b795）；'
'LEAD_LOCK **QH** CR 保持 **137**（69703921 到 493a1e16）；STATUS_BOARD 第 205 轮 CR 保持 **0**（开局 272 行 >= 260，归档最早 2 段至 BOARD_ARCHIVE，ARCHIVE CR 保持 **2952**）。\n\n'
'**未取得.** （1）COL.sig 原义；（2）3 个非严格递减反例的语义成因（只取得字节事实）；（3）5 条 .?AV 为何也无 vftable；（4）2 个 TD 各 2 条记录的语义；'
'（5）UIUnknown 两条非自有（后者 attributes==2）的差别；（6）CHD +36 之后字节语义；（7）R204 遗留：464 张非等差中 111 张短 BCA 成因、attributes 5 vs 1 语义；'
'（8）5 个 ATL 类无第二张 vftable、260 个被吞候选归类、94 个 MI 类基类名链；（9）R200 (c)(d)(f)(g)；（10）F23/F35 grade；'
'（11）coverage.tsv 与 function_atlas.tsv 仍不可读；（12）86.19% 仍不可重算；（13）C7 三死分支各 0 行；（14）C11 十二个 ID 未动。\n'
)
new_bs=rest+R205
open(bs,'wb').write(new_bs.encode('utf-8'))
nb=len(open(bs,'rb').read().split(b'\n'))-1
ck('B8 看板 CR 仍 0',crc(bs)==0,crc(bs))
ck('B9 看板行数 <= 300',nb<=300,nb)
ck('B10 看板新增第 205 轮',('R17 第 205 轮').encode('utf-8') in open(bs,'rb').read(),None)
ck('B11 归档段已不在看板',segs[1].split('\n')[0].encode('utf-8') not in open(bs,'rb').read(),None)
ck('B12 归档段已进 ARCHIVE',segs[1].split('\n')[0].encode('utf-8') in open(ar,'rb').read(),None)
print('BOARD: %d -> %d 行（归档 2 段）'%(lines_before,nb))
print('ARCHIVE: CR %d, +%d B'%(crc(ar),len(new_ar)-len(a_raw)))
print('\nFAILS:',fails)
json.dump(dict(fails=fails,board_before=lines_before,board_after=nb,
               archive_cr=crc(ar),board_cr=crc(bs)),
          open('/home/t628/projects/ra2-campaign-forge/_r205/p3_board.json','w'),indent=1)
