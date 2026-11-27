#!/usr/bin/env python3
"""R170 J：FACT_INDEX V549 -> V550。
两处改动（本轮裁定的全部落盘）：
  A) F23 grade: [已证] -> 未取得（裁定 + R90 档 2 撤销），并在 limitations 追加裁定段；
  B) F29 statement 的自指假句「不在本条任何一列」-> 「不参与本条任何计数」，limitations 追加回收记录。
其余 52 行逐字节不变（断言）。
写入纪律：R17_LEAD_BASELINE/ wx 独占备份 -> 断言旧 sha/CR -> 一次性写入 -> 回读校验。
"""
import hashlib, io, json, os, csv
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'
SRC=T+'/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
DSTD=T+'/R17_R122_FACTINDEX_V550'
DST=DSTD+'/FACT_INDEX.tsv'
BAK=T+'/R17_LEAD_BASELINE/FACT_INDEX.tsv.V549.before_r170_20261127.bak'
A=[]
def ck(i,c,d):
    A.append({'id':i,'ok':bool(c),'detail':str(d)})
    print(('PASS ' if c else 'FAIL ')+i+' :: '+str(d)[:200])

raw=open(SRC,'rb').read()
sha0=hashlib.sha256(raw).hexdigest()
ck('J0 源 = V549 / 117545 B / CR 0 / sha f1d32127',
   sha0.startswith('f1d32127') and len(raw)==117545 and raw.count(b'\r')==0, (sha0[:8],len(raw)))

fd=os.open(BAK,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
with os.fdopen(fd,'wb') as f: f.write(raw)
ck('J1 备份 wx 独占且 sha 相同', hashlib.sha256(open(BAK,'rb').read()).hexdigest()==sha0, BAK.split('/')[-1])

rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
ck('J2 55 行 × 5 列', len(rows)==55 and all(len(r)==5 for r in rows), (len(rows),{len(r) for r in rows}))
idx={r[0]:i for i,r in enumerate(rows) if i>0}

RUL=('**【R170 裁定·grade 由 [已证] 降为 未取得，R90 档 2 定性同时撤销】** '
 '① **判据来源**：台账「分级口径：」共 17 行，其中 1 行是 R150 自指行（该行自己写「16 处」），真定义 16 行；'
 '这 16 行 **16/16 以证据形态定义** `[已证]`（审计独立复算闭合 / 原始字节实测 / 签发件已核），**0 行**以「原件是否在盘」定义 '
 '⇒ **降级不能拿「文件已失」当理由**，只能用「证据形态够不上」当理由（`_r170/r170d_refine.py` I1–I4、`_r170/r170c_prov.py` C6–C9）。 '
 '② **够不上的三条实测**：a) 本行第 4 列 **2 项全失联、存活项 0**，是 54 行里**唯一**零存活行（`[已证]` 27 行的存活项分布 '
 '{0, 1×7, 2×12, 3, 4×2, 7×3, 28}、中位 **2**）；b) R90 七式**逐位为真但无一具鉴别力** —— `458+1196=1654` 是 A+非A 恒真'
 '（换 A=300/400/500/600/900/1200、令 none=1654−A，**6/6 全部照样成立**），`863+791=1654` 同理，四个百分数是计数的函数**属循环**，'
 '`1654+5875+10969=18498` 与 458 无关；c) 本条计数依赖 `coverage.tsv`（4,147,334 B / 18,498 行 / 8 列）**本体已失**、'
 '**内容指纹在盘**（sha256 `c2ee063fd4f61f784585ef2abcc4ff563fa09ec1b1f7f5079643076e359c744a`）⇒ 可核身份、**不可恢复内容**。 '
 '③ **R90 的「F23 档 2（可重算）」这条定性撤销**：它不是「算术自洽即独立复现」，本行不再引用它兜底。 '
 '④ **回改判据（可失败、方向明确）**：若 `coverage.tsv` 本体恢复（字节数 == **4,147,334** 且 sha256 == `c2ee063f…`），'
 '按 ④ 三口径（A / B / 宽 / 无 ④）、12 行分解、2 与 9 的减法三处重建计数并留独立复算记录，可得回 `[已证]`；在此之前**不得回改**。 '
 '⑤ 「未取得」在本行的含义 = **无可复算的判定样本**，**不是**「当时未测」——statement 里的值本身不被否定、一字未改。 '
 '⑥ 本条 **statement 一字未改**（计数与作用域全部保留），本次改动只有 grade 列。')

SELF=('**【R170 补·statement 的自指假句已就地回收】** V545 的 R165 段把 limitations 里的自指句改成了「该数不参与本条任何计数」，'
 '但 **statement 末句仍写「……不在本条任何一列」** ⇒ 同一行两列相反。实测：该串在 statement **1** 次、limitations **2** 次'
 '（R138 段与 R165 段各 1）、合计 **3** 次，而 limitations 那两处**正是这句话自身的载体**，故该声明在它写下的同一行里被证伪；'
 '「6 个不同桩体」同口径为 statement 1 / limitations 2。逐版：V540–V549 statement 该串**恒 1 次**，limitations **V545 起**为 2。'
 '本轮把 statement 末句就地改为「**不参与本条任何计数**」，两会话口径统一（`_r170/r170g_f29self.py` 5 断言、'
 '`_r170/r170i_recompute.py` K1–K8 复算执行员 #399 与审计员 #400 的两条不一致后确认）。')

new=[list(r) for r in rows]
i23=idx['F23']; i29=idx['F29']
ck('J3 F23 原 grade = [已证]', rows[i23][2]=='[已证]', rows[i23][2])
ck('J4 F29 statement 原含旧串 1 次', rows[i29][1].count('不在本条任何一列')==1, rows[i29][1].count('不在本条任何一列'))
new[i23][2]='未取得'
new[i23][4]=rows[i23][4]+RUL
new[i29][1]=rows[i29][1].replace('不在本条任何一列','不参与本条任何计数')
new[i29][4]=rows[i29][4]+SELF
out='\n'.join('\t'.join(r) for r in new)
if not out.endswith('\n'): out+='\n'
ck('J5 输出 CR = 0（全 LF）', '\r' not in out, 'ok')
os.makedirs(DSTD,exist_ok=True)
open(DST,'w',encoding='utf-8',newline='').write(out)

# ---- 回读校验 ----
raw2=open(DST,'rb').read()
rows2=list(csv.reader(io.StringIO(raw2.decode('utf-8')),delimiter='\t'))
ck('J6 回读 55 行 × 5 列', len(rows2)==55 and all(len(r)==5 for r in rows2), len(rows2))
diff_rows=[rows2[k][0] for k in range(55) if rows2[k]!=rows[k]]
ck('J7 差分行恰 {F23, F29}', set(diff_rows)=={'F23','F29'}, diff_rows)
cells=[]
for k in range(55):
    for c in range(5):
        if rows2[k][c]!=rows[k][c]: cells.append((rows2[k][0],c))
ck('J8 变化单元恰 4 个 = F23[2,4] + F29[1,4]', sorted(cells)==[('F23',2),('F23',4),('F29',1),('F29',4)], cells)
ck('J9 其余 52 行 × 5 列逐字节相同', all(rows2[k]==rows[k] for k in range(55) if rows2[k][0] not in ('F23','F29')), 52)
ck('J10 F23 statement 一字未改', rows2[i23][1]==rows[i23][1], len(rows2[i23][1]))
ck('J11 F29 statement 只换那一句（长度 +3 字符）', len(rows2[i29][1])-len(rows[i29][1])==3 and rows2[i29][1].count('不参与本条任何计数')==1, (len(rows[i29][1]),len(rows2[i29][1])))
ck('J12 F29 旧串在 statement 归零、limitations 仍 2（历史段保留）', rows2[i29][1].count('不在本条任何一列')==0 and rows2[i29][4].count('不在本条任何一列')==2, (rows2[i29][1].count('不在本条任何一列'),rows2[i29][4].count('不在本条任何一列')))
ck('J13 F23 新 grade = 未取得', rows2[i23][2]=='未取得', rows2[i23][2])
ck('J14 总字节增长 = 追加段 + 3（无静默缩短）', len(raw2)>len(raw), (len(raw),len(raw2),len(raw2)-len(raw)))
ck('J15 F23/F29 字节均不小于 V549 的 floor',
   len(rows2[i23][1].encode())>=1785 and len(rows2[i23][4].encode())>=5711 and len(rows2[i29][1].encode())>=3432 and len(rows2[i29][4].encode())>=13343,
   (len(rows2[i23][1].encode()),len(rows2[i23][4].encode()),len(rows2[i29][1].encode()),len(rows2[i29][4].encode())))
sha1=hashlib.sha256(raw2).hexdigest()
ck('J16 新 sha != 旧 sha', sha1!=sha0, sha1[:16])
# 反控：旧的自我指称句若原样复制回来，断言 J11 必须失败
t=rows2[i29][1].replace('不参与本条任何计数','不在本条任何一列')
ck('J17 反控：把旧串换回则长度断言必须不成立', len(t)-len(rows[i29][1])==0, 'ok')

json.dump({'assertions':A,'fail':sum(1 for a in A if not a['ok']),'sha':sha1,'bytes':len(raw2),
           'old_sha':sha0,'old_bytes':len(raw),'diff_rows':diff_rows,'cells':cells},
          open(ROOT+'/_r170/r170j_write_v550.json','w'),ensure_ascii=False,indent=1)
print('NEW sha',sha1,'bytes',len(raw2))
print('FAIL =',sum(1 for a in A if not a['ok']),'/',len(A))
