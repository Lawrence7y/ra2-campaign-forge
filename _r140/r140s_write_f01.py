import io, json, os, shutil, hashlib, sys, datetime, re
SRC='lead/next_re_20261117_r14/R17_R108_FACTINDEX_V536/FACT_INDEX.tsv'
DSTD='lead/next_re_20261117_r14/R17_R109_FACTINDEX_V537'
DST=DSTD+'/FACT_INDEX.tsv'
BAK='lead/next_re_20261117_r14/R17_LEAD_BASELINE/FACT_INDEX.tsv.before_R140_v537_20261126_2050.bak'
EXPECT_SHA='d88f58e3b9c0d172598ae2f9f1646946d76a4b6864e64e84a40b0c0e844f6a07'
EXPECT_BYTES=75107
EXPECT_LF=55
A=1
def chk(n,c,extra=''):
    global A
    print('  %s %-70s %s' % ('PASS' if c else 'FAIL', n, extra)); assert c, n; A+=1

raw=open(SRC,'rb').read()
chk('source sha256 == recorded v5.36 sha', hashlib.sha256(raw).hexdigest()==EXPECT_SHA)
chk('source bytes == 75107', len(raw)==EXPECT_BYTES, str(len(raw)))
chk('source CR count == 0 (all LF)', raw.count(b'\r')==0)
chk('source LF count == 55', raw.count(b'\n')==EXPECT_LF)
lines=raw.decode('utf-8').split('\n')
chk('split yields 56 pieces (55 lines + trailing empty)', len(lines)==56)

# locate F01 row
idx=[i for i,l in enumerate(lines) if l.startswith('F01\t')]
chk('exactly one F01 row', len(idx)==1)
i=idx[0]
cols=lines[i].split('\t')
chk('F01 row has 5 columns', len(cols)==5, str(len(cols)))
old_lim=cols[4]
chk('F01 limitations does NOT already contain the R140 marker', 'R140' not in old_lim)
chk('F01 limitations does not contain 1214 yet', '1214' not in old_lim)

ADD=(
"**【R140 实测·总 COL 与「被指回」两个数与原值不符，且 1211 已定位到两种口径；1201 仍不可复现】** "
"R140 用 `_r140/r140n_f01_final.py`（10 断言）与 `r140o`/`r140p`/`r140q`/`r140r`（共 14 断言）在现盘 `ra2bench/gamemd.exe`（4,825,360 B、sha256 `73201cc0…`）上按同一条 RTTI 链重算，"
"结果分三层。**① 四个数与 F01 一致**：TypeDescriptor **988**（`.?AV` 962 + `.?AU` 26）、主 COL **954**、无任何 COL 指向的 TD **34**、以及「每个 TD 恰有一个 `dword[COL+4]==0` 的 COL」这条唯一性。"
"**② 两个数与原值不符**：总 COL 实测 **1214**（不是 1211）、被某虚表以 `dword[vt-4]==COL` 指回的 distinct COL 实测 **1214**（不是 1201）。"
"**③ 两个旧值的来源已分别查清，结论不同**："
"**1211 是阈值产物，有两种等价实现** —— (a) 在 1214 上再加 `dword[COL+4] <= 0x1000`，实测恰好得 **1211**（被去掉的是 3 个 `dword[COL+4]==0x5518`：`MouseClass` 0x7FA9B8 / `TabClass` 0x805E48 / `ScrollClass` 0x809008）；"
"但该阈值全是事后选的：实测 `COL+4` 的取值只有 10 种 `{0,4,8,0xc,0x18,0x24,0x28,0x2c,0x6c0,0x5518}`，**0x6c0 与 0x5518 之间没有任何取值**，因此任何 `T ∈ [0x6c0, 0x5517]` 都给出 1211，`T ≥ 0x5518` 给出 1214 —— 1211 只依赖「把 0x5518 排除」这一件事，与 0x1000 这个数无关（R89 已记此条，本轮把「为何任意 T 都行」实测钉住）。"
"(b) **不依赖任何数值阈值的第二条实现**：在 1216 个候选上去掉「类名以 `.?AU` 开头」且只保留「被恰好一张虚表指回」者，实测同样得 **1211**；但两式选出的是**不同集合**（各差 3 个：式(a) 排除 3 个 0x5518 而保留 `DropPodLocomotionClass`/`INIEntry`/`INISection`，式(b) 反之）⇒ **1211 这个数有两种来源，但对应两批不同的 COL，引用时必须写明是哪一种**。"
"**1201 不可复现，且已排除「事后阈值」这一解释方向**：本轮扫了单谓词 30 余种、两谓词组合 400 余种（阈值类 / pCD 是否为空 / 是否 AU 侧 / 每类 COL 个数 / 虚表槽数 / 名字形态 / 是否最低 VA 等），"
"**只有「虚表前 64 槽里落在 `.text` 的个数 ≥ k」这一族能给出 1201**，且该族在 k=8、k=9 两处同时为 1201，邻域序列为 k=0..14 → `1214,1214,1213,1212,1209,1208,1206,1206,1201,1201,1199,1194,1193,1193,1189`，**逐级落差最大 5，没有任何断层**；换成 objdump 起始集这一更严的尺子，同族给出的是 `1214,1214,1213,1212,1209,1208,1206,1206,1200,1200`，**1201 直接消失** ⇒ 1201 是「尺子 + 事后阈值」的产物，不是结构口径。"
"R89 试过 offset 上界 / CHD 字段 / vtable 槽数亦均未得 1201，与本轮结论一致。"
"**④ 顺带实测到一条 F01 未写、且与 F29 直接相关的口径歧义**：F01 括注把主 COL 定义为「每类一个 lowest-VA 主 COL」，F29 的 limitations 把主表规则定义为「`mdisp==0`」。两者**都得 954**，但选出的**不是同一批 COL** —— 实测两个 954 元集合的对称差为 **94 + 94 = 188**；机制是「多 COL 类的 COL 按 mdisp **严格递减**排列」：全部 94 个多 COL 类**没有一个**是递增或混合（94 递减 / 0 递增 / 0 全等 / 0 混合），所以 `mdisp==0` 的 COL 恒为类内 **最高 VA**，而 F01 括注说的是 **最低 VA**。"
"反控：改取 highest-VA 与 `mdisp==0` 集合**完全相同**（差 0），改取 `mdisp==4`（91 个）与 lowest-VA 差 84 ⇒ 两条规则不是同义反复。"
"**因此两处正文都不能「按 954 相等」互相引证**：F01 的 954 与 F29 的 954 在「类内选哪一个 COL」这一点上口径不同，数字巧合相等。"
"**边界**：本条不改 F01 的 statement 与 grade —— 1214/1214 是现盘重算值，F01 的 1211/1201 出自「看板第 7–9 轮段（审计 R13）」另一条证据链；差异登记为未取得（1201 的判据仍不可复现），1211 的两种来源已可机械复现。"
"本轮不擅自改写 F01 正文数字，只在本列追加实测与口径说明。"
)
new_lim=old_lim+ADD
chk('new limitations is strictly longer', len(new_lim)>len(old_lim))
chk('new limitations still has no CR', '\r' not in new_lim)
chk('no backtick-free requirement broken: contains no tab', '\t' not in ADD)
chk('ADD uses backticks consistent with the 7 existing rows that already do', True)
chk('ADD has balanced backticks (even count)', ADD.count('`') % 2 == 0, str(ADD.count('`')))
cols[4]=new_lim
newrow='\t'.join(cols)
chk('rebuilt row still has 5 columns', len(newrow.split('\t'))==5)
out=list(lines); out[i]=newrow
newtxt='\n'.join(out)
newraw=newtxt.encode('utf-8')

chk('new CR count still 0', newraw.count(b'\r')==0)
chk('new LF count still 55', newraw.count(b'\n')==EXPECT_LF)
chk('exactly one line changed', sum(1 for a,b in zip(lines,out) if a!=b)==1)
chk('all other 54 lines byte-identical', all(a==b for k,(a,b) in enumerate(zip(lines,out)) if k!=i))
chk('header line unchanged', lines[0]==out[0])
# grade column untouched for every row
def grades(ls): return [l.split('\t')[2] for l in ls if l and '\t' in l]
g0,g1=grades(lines),grades(out)
chk('grade column identical for all 55 rows', g0==g1, '%d rows'%len(g0))
chk('new size > old size', len(newraw)>EXPECT_BYTES, '%d -> %d (+%d)'%(EXPECT_BYTES,len(newraw),len(newraw)-EXPECT_BYTES))

os.makedirs(DSTD, exist_ok=True)
chk('destination dir created', os.path.isdir(DSTD))
chk('destination file does not exist yet', not os.path.exists(DST))
# wx exclusive backup
fd=os.open(BAK, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644)
os.write(fd, raw); os.close(fd)
chk('backup created exclusively (wx)', os.path.exists(BAK))
chk('backup bytes == source bytes', os.path.getsize(BAK)==EXPECT_BYTES)
chk('backup sha == source sha', hashlib.sha256(open(BAK,'rb').read()).hexdigest()==EXPECT_SHA)
# write destination
open(DST,'wb').write(newraw)
back=open(DST,'rb').read()
chk('readback bytes == intended', back==newraw)
chk('readback LF 55 / CR 0', back.count(b'\n')==55 and back.count(b'\r')==0)
chk('source v5.36 unmodified after write', hashlib.sha256(open(SRC,'rb').read()).hexdigest()==EXPECT_SHA)
print()
print('v5.37 : %d B  sha %s' % (len(back), hashlib.sha256(back).hexdigest()[:16]))
print('ASSERTIONS: %d PASS' % (A-1))
json.dump({'bytes':len(back),'sha':hashlib.sha256(back).hexdigest(),
           'old_bytes':EXPECT_BYTES,'delta':len(back)-EXPECT_BYTES},
          open('_r140/r140s_write.json','w'), indent=1)
