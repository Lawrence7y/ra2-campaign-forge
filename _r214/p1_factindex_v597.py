# -*- coding: utf-8 -*-
"""R214 p1：FACT_INDEX V596 -> V597。把本轮 6 组实测写入 F29 limitations；其余 56 行逐字节不变。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLDV=TIER+'/R17_R131_FACTINDEX_V596/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V597'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V596 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA=='fd18fe6aec9e34ba97e4b2ad41b71bccfb1d4d71b0e02cf7e58f48b7ea00b5d2',OLD_SHA
assert OLD_B==264072,OLD_B
lines=raw.decode('utf-8').split('\n'); ORIG=list(lines)

ADD=('【槽面普查 · R214 实测】1214 张视图共 **14044** 槽（主 954 张 12726 / 次 260 张 1318），'
 '槽值 **100% 落 .text**（14044/14044）；distinct 槽目标 **6692** 个。'
 '主视图 distinct 目标 **6345** / 次视图 **348** / **交集仅 1** 个 = **0x4c9150**（`xor eax,eax ; ret`，纯桩）'
 '⇒ 仅主视图独有 6344、仅次视图独有 347。**口径声明（审计 #553 指出）**：「槽值全落 .text」是**定义恒真**'
 '（视图槽的定义就是「从 vftable 起点起连续落 .text 的 dword」），不构成独立证据；'
 '去掉该过滤、仅用「下一视图起点」截断时同一批视图切出 **29580** 槽（视图上限 4096 时）或 **49766** 槽（无上限时，'
 '末张视图 0x7fa498 到 .rdata 上界 0x812000 之间 97128 B = 24282 dword 被一次性计入）⇒ 该数须标注停止口径。'
 '同理「按 COL+4 取 .text 指针 = 0/1214」也是定义恒真（COL+4 就是 mdisp 字段，主视图定义即 mdisp==0）。'
 '【虚槽 +0x48（slot index 18）转发面 · R214 新取得】R213 QV7 已解 S3(21784) 函数体尾为 `jmp dword [eax+0x48]`；'
 '本轮把这把尺落到全表：槽数 > 18 的视图 **137** 张（主 **125** / 次 **12**），其 slot18 落点 **distinct 27** 个、'
 '**全部落 .text**（virt-only 0 / other 0）；落点 top3 = **0x4104c0 ×56** / **0x5f65a0 ×19** / **0x4e1960 ×17**。'
 'MouseClass 主视图（起点 0x7e1964，55 槽，slot0 0x4f4240）**slot18 = 0x5bda80**（与 Tab/Scroll 不同），'
 'TabClass（0x7edfb4，55 槽）与 ScrollClass（0x7f1094，55 槽）slot18 **均 = 0x4c9150**（纯桩）⇒ '
 '**三类 +0x48 转发落点两两不同**，S3 共享同一 21784 视图并不蕴含 slot18 同落点。'
 '两个转发桩 **0x723ea0 / 0x723eb0** 在 .text 内的 **e8 直接调用位点共 19 处**（0x723ea0 **10** / 0x723eb0 **9**，'
 'capstone 逐条确认全为 `call`、无 jmp、decode 失败 0），且**两地址不作为任何 vftable 槽值出现（0/14044）** '
 '⇒ 它们只能被直接调用，不是虚函数体，也不是任何类的虚槽实现。'
 '**判据失效更正（自错）**：R214 首版用「slot17/18/19 的 distinct 数三者不等」判 slot18 非平凡，'
 '实测 d17/d18/d19 = **28/27/27**（d18 == d19），该判据**不成立**；替用判据为 slot18 ∩ slot19 = **1**'
 '（唯一 0x4c9150）、仅 18 独有 **26**、仅 19 独有 **26**。'
 '【律 X 一般式定稿 · R214 订正 R213 简化式】R213 律 X 原口径为「adjustor 的 imm 恒 == 本视图 mdisp」（303/305）。'
 'R214 把口径升为**一般式**：`imm == mdisp_self − mdisp_target`（target = jmp 目标所属视图的 mdisp），'
 '在全体 **305/305** 个 adjustor 上**全部成立、反例 0**。HouseClass mdisp=40 次视图（0x7ea80c，9 槽）idx3/idx4 两条'
 '（slot 0x7ea818 / 0x7ea81c，字节 `83 6c 24 04 04 e9 ..` = `sub dword ptr [esp+4],4` + `jmp 0x4f6e60` / `jmp 0x4f6950`）'
 '的 jmp 目标**owner 唯一** = 同一 HouseClass 的 **mdisp=36 次视图（0x7ea834）idx3 / idx4**，'
 '**不在 mdisp=0 主视图（0x7ea8a0，24 槽）内**，且 imm = 40 − 36 = **4** 严格成立。'
 '⇒ **订正 R213 看板与 V596 F29 的表述「两目标均在本类主视图槽内」，实为 mdisp=36 次视图 idx3/idx4**；'
 '两条不是真反例，而是简化式口径的产物，一般式下 305/305 无反例。'
 'HouseClass 共 **7** 张视图，mdisp 集 {0,4,8,12,36,40,44}（槽数 24/6/1/1/15/9/5）。'
 '【adjustor 指令级模板 · 新口径】按「首指令字节长度」分类只有 **2** 种：`sub [esp+4],imm`(5B) + `jmp rel32`(5B) ×**302**、'
 '`sub [esp+4],imm`(8B) + `jmp rel32`(5B) ×**3**；后者 3 条**全部**属 `?AVAircraftClass@@` mdisp=**1728**（imm=0x6c0，'
 '需 4 字节立即数故指令长 8B），视图起点 0x7e2250/0x7e2254/0x7e2258。纯助记符序列 distinct = **1**（`sub;jmp`）。'
 'R213 报的「槽型模板 7 种」是**另一把尺**：逐视图的「槽是/不是 adjustor」二值串（A/F），'
 '与指令级模板**不可互换**（R213 原文「槽型模板」易被读成字节通配串，此处订正口径）。'
 '【mdisp 元组分布 · 全表】有非零 mdisp 记录的类 **94** 个，按 mdisp 升序元组去重只有 **6** 种：'
 '`(4,8,12) ×76` / `(4,) ×7` / `(4,24) ×6` / `(21784,) ×3` / `(4,8,12,36,40,44) ×1`（HouseClass）/ '
 '`(4,8,12,1728) ×1`（AircraftClass），合计 94 自洽。'
 '【单值索引（同槽号跨类同目标）· 分母塌缩】主视图按槽号聚合，**91 / 344** 个槽号是「该槽号上所有类共用一个目标」，'
 '但**分母塌缩严重**：分母 = 1 者 **1** 个、2–4 者 **8**、5–9 者 **69**、10–99 者 **13**、**≥100 者 0**；'
 '唯一分母 = 954 的槽号是 idx0，而 idx0 distinct = **863** 非单值 ⇒ 「单值索引 91」**不可**当作「虚槽语义稳定」的证据。'
 '【自错 6 组 · R214，0 条进结论】①「vftable 前缀一致 ⇒ 单继承父类」推导**方法无效**：实测 93 类歧义、'
 '根 861、深度 75（1..75 每层恰 1 个）退化长链、长度层 55、最长视图 344 槽，且 861 根类含大量无继承关系的类，'
 '该产出全部作废；②首版把末张视图的截断上界写成 .text hi_file（应为 .rdata 上界）⇒ 少算 1 槽（14043），'
 '由 a2 诊断脚本定位后改回 14044；③律 X 复算首版把类名当 `.?AV..`（带首点）匹配 ⇒ 三类查询全空、误报 6 FAIL，'
 '归一化去首点后 PASS；④「slot17/18/19 distinct 三者不等」判据失效（见上）；⑤曾按臆造阈值断言「主视图长度≥100 的类≥400」，'
 '实测 **21**，改为事实性断言；⑥审计员报「去 .text 过滤得 29580 槽」与我方首版 49766 冲突，'
 '经 a4 变体枚举确认 **29580 = 上限 4096 口径**、**49766 = 无上限口径**，两者差全在末张视图，'
 '故该数必须与停止口径同时引用。'
 '【跨家族 §2.12 规则 D · R214 全复算】exec #551（hy4，21 回合 / 2.9 分 vs 10，无 OVERTIME，25 断言 0 FAIL）、'
 'exec #552（hy4，15 回合 / 2.85 分，30 断言 0 FAIL）；audit #553（deepseek 只读，16 回合 / 3.7 分，无 OVERTIME）。'
 '审计 5 条订正全部经主会话复算：①B5 判据失效（d18==d19，成立）；②一般式 305/305（成立，a3 断言 2c）；'
 '③A1/A5 为定义恒真（成立，a3 断言 3a/3b）；④8B sub 全属 AircraftClass 1728（成立，a3 4a/4b）；'
 '⑤单值索引分母塌缩 ≥100 者 0（成立，a3 5a/5b）。主会话独立复算源：_r214/a1_recheck.py **31 断言 0 FAIL**、'
 '_r214/a3_audit_claims.py **13 断言 0 FAIL**、_r214/a5_final_nums.py **14 断言 0 FAIL**；'
 'exec 侧 _r214/ex1.py 25 断言 0 FAIL、_r214/ex2.py 30 断言 0 FAIL 均已在主会话重算一致。')

idx29=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
assert len(idx29)==1,idx29
i29=idx29[0]
cols=lines[i29].split('\t'); assert len(cols)==5,len(cols)
cols[4]=cols[4]+ADD
lines[i29]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert diff==[i29],diff
print('仅第 %d(F29) 行变化；其余 %d 行逐字节不变'%(i29,len(ORIG)-1))
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
assert not os.path.exists(out),'V597 已存在'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V597 sha %s bytes %d (+%d)'%(NSHA,NB,NB-OLD_B))
print('CR=%d lines=%d cols=%d'%(nb.count(b'\r'),len(nlines),len(nlines[0].split('\t'))))
open(ROOT+'/_r214/p1_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
