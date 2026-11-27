#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R191 落盘：台账 V575 -> V576。只在 F55 一行追加第 ⑩ 段，并把 ⑨(e) 里那句错定性就地订正。

本轮三条实测（_r191/r191g_deliver.py 23 断言 0 FAIL / r191d_td.py 16 断言 / r191b_recheck.py 22 断言）：
  ① 四档缺席的判别量是**基类身份**：偏移不是（4 与 36 上两种情形并存）、
     无 COL 不是（14 个无 COL 基类里 9 个会拿到副表）、attributes 不是（2x2 两个方向都有反例）。
     (基类,偏移) 全表 24 行里，16 个基类在"有无副表"上**完全一致**（混合 0 个）；
     从不拿到副表的基类恰 **5** 个，R190 只报 3 个，漏了 ATL 的两个。
  ② R190 的「2,111 条 / 34 个名指向**镜像外** COM 接口基类」**是错的**：
     34 个 pTD 全部落在 .data 段内、TD 全部可读。2111 这个数本身可复现。
  ③ 1,013 个直接槽的复用结构量化：278 个不同入口、47 个被 2 个以上槽共用、吃掉 782 槽（77.19%）。
"""
import os, sys, copy, hashlib, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V575', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V576')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('D1 旧 V575 = 167,276 B / sha ec21be7a… / CR 0',
   len(raw) == 167276 and hashlib.sha256(raw).hexdigest().startswith('ec21be7a')
   and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('D2 58 段（57 行 + 空尾）', len(L) == 58, len(L))
rows = [l.split('\t') for l in L[:57]]
ORIG = copy.deepcopy(rows)
ck('D3 57 行每行 5 列', all(len(r) == 5 for r in rows))
f55 = [r for r in rows if r[0] == 'F55'][0]
OLD_STMT = len(f55[1].encode()); OLD_LIM = len(f55[4].encode()); OLD_EV = len(f55[3].encode())
ck('D4 F55 现态 stmt 7937 / lim 5791 / evid 247',
   (OLD_STMT, OLD_LIM, OLD_EV) == (7937, 5791, 247), (OLD_STMT, OLD_LIM, OLD_EV))

# ---- 就地订正 ⑨(e) 里"类名之外"那句（R190 §PT6 与看板把它叙述成"镜像外"，实为镜像内） ----
WRONG = '指向本镜像 1,214 个类名之外的基类'
WRONG2 = '这些**没有**对应的 `.?AV...` 副表'
ck('D5 ⑨(e) 那句待订正文字在 limitations 里各恰 1 次',
   f55[4].count(WRONG) == 1 and f55[4].count(WRONG2) == 1,
   (f55[4].count(WRONG), f55[4].count(WRONG2)))
FIX_FROM = WRONG2
FIX_TO = (WRONG2 + '（**R191 订正**：这 34 个的 pTD **全部**落在 `.data` 段内、34/34 的 '
          'TypeDescriptor 都可读，**没有一条在镜像外**；R190 叙述里的「指向镜像外 COM 接口基类」措辞错误，'
          '正确说法是「有 TD 但无 COL 的基类」）')
f55[4] = f55[4].replace(FIX_FROM, FIX_TO, 1)
ck('D6 订正后 ⑨(e) 已指明"没有一条在镜像外"',
   '没有一条在镜像外' in f55[4], '已替换')

S10 = ('⑩ **（V576 新增 · R191 四档缺席的判别量 + 一处定性订正）** '
'上一段 ⑨ 把 {172,176,240,248} 四档写成「有基类子对象、但没有独立副表」，**没给判据**；'
'本轮把 24 行全表（16 个基类 × 各自偏移）摊开后，三条候选解释**全部被自己的反例否掉**：'
'**（i）偏移不是判别量** —— 同一偏移上「有副表」与「无副表」两种情形并存：偏移 **4** 为 '
'has 696 / no 10，偏移 **36** 为 has 14 / no 4（4 与 36 是仅有的两个混合偏移）；'
'**（ii）「基类无自身 COL」不是判别量** —— 14 个无 COL 的基类里 **9 个会拿到副表**'
'（`IUnknown`/`IRTTITypeInfo`/`ILocomotion`/`IPiggyback`/`IHouse`/`IPublicHouse`/'
'`IConnectionPointContainer`/`ILinkStream`/`IFlyControl`），只有 5 个从不拿到；'
'**（iii）`BCD.attributes`（bit0 = non-virtual）也不是判别量** —— 非零 BCD 共 **1,498** 条，'
'attributes × 有无副表的 2×2 为 {0,有:1024} / {0,无:72} / {2,有:392} / {9,有:6} / {9,无:4}，'
'**两个方向都有反例**（bit0=1 却有副表 6 条；attributes=0 却无副表 72 条）。'
'**真正的判别量是基类身份**：16 个基类在「有无副表」上 **完全一致**（跨全部偏移混合 **0 个**），'
'从不拿到副表的基类恰 **5 个** —— StageClass / BounceClass / FlasherClass，'
'外加 R190 漏掉的 ATL 两个（`CComObjectRootBase@ATL` 与 `?$CComObjectRootEx@VCComMultiThreadModel@ATL`）；'
'四档涉及的基类恰 StageClass（偏移 36/172/248）/ BounceClass（176）/ FlasherClass（240）三个，'
'全在「从不拿到」集合内。'
'**直接槽的复用结构量化**：1,013 个非 thunk 直接槽只指向 **278 个不同入口**，'
'其中 **47** 个入口被 2 个以上槽共用、合计吃掉 **782 个槽（77.19%）**；'
'用量前五为 `0x410590`(78, `C2 04 00` = ret 4) / `0x410220`(78, 读 this+0xC 后 ret 4) / '
'`0x410230`(78) / `0x410210`(76, 取 [this−4] 的 vptr 再 `call [vptr+0x2c]` 的转调 thunk) / '
'`0x410580`(75, `32 C0 C2 08 00` = xor al,al; ret 8)；'
'单个入口最多被 **78** 个不同修饰名的类共用（`0x410590`/`0x410220`/`0x410230` 各 78）。'
'**一处定性订正（R190 ⑨(e) 的错）**：R190 写「2,111 条（34 个名）指向**本镜像之外的** COM 接口基类」，'
'实测这 34 个 pTD **全部**落在 `.data` 段内、34/34 的 TypeDescriptor 可读、'
'`pVFTable` 全等于 `0x7F9594`，**没有一条在镜像外**；2,111 这个数本身可复现（BCD 引用数恰 2111）。')

L10 = ('**（V576 新增 · 与 ⑩ 同一批实测）** 边界与判据写在这里：'
'（a）「有无副表」的判据是：宿主类 X 的表组里存在一张 `COL.mdisp == m` 的表（`m` 为 BCD 的 PMD.mdisp），'
'**不是**「该值落在层偏移集合里」—— 后者会产生 3 行反例（StageClass@36 与 ATL 两条@4），'
'因为层偏移集合是从**实际存在的表**反推出来的，用它判缺席是循环论证。'
'（b）「基类身份是判别量」这句话的**边界**：它只是「在 16 个基类 × 24 行全表的实测范围内一致」，'
'**不是**因果解释；本轮**没有**取得「为什么这 5 个基类不需要副表」的机制，'
'只把「不是偏移、不是无 COL、不是 attributes」三条候选逐一实测否掉。'
'（c）反控：把「无 COL」当判据 ⇒ 报 9 个反例；把「偏移是层偏移」当判据 ⇒ 报 3 行反例；'
'把 11 个「每次都拿到副表」的基类**逐一**翻面（共 11 次）⇒ 每次都使「基类层面混合 = 0」变红，'
'未翻面时同一函数返回空（正对照）。'
'（d）1,013 个直接槽「指向 278 个入口」是**槽级**计数；'
'同一入口在主表上的出现次数是 **204 次**但只涉及 **1 个槽**（`0x4c9150`，LocomotionClass@mdisp=4 槽 29），'
'这两种口径不可混用。（e）四个入口（`0x410450`/`0x410580`/`0x410590`/`0x4C9150`）的**游戏语义名仍未取得**，'
'本轮只到「字节形态 + 宿主 + 用量」，**没有**装任何语义名。'
'（f）脚本 `_r191/r191g_deliver.py`（23 断言 0 FAIL）/ `_r191/r191d_td.py`（16 断言）/ '
'`_r191/r191b_recheck.py`（22 断言 0 FAIL）。')

# 去掉 (d) 里被误加的反引号（卡面/台账不宜出现孤立反引号）
L10 = L10.replace('是**槽级**计数；`\n', '是**槽级**计数；')
S10 = S10.replace('；`\n', '；')
for nm, s in (('statement', S10), ('limitations', L10)):
    ck('D7 %s 段无 tab / CR / LF' % nm, '\t' not in s and '\r' not in s and '\n' not in s)
    ck('D8 %s 段无孤立反引号' % nm, s.count('`') % 2 == 0, s.count('`'))
ck('D9 ⑩ 段在 statement 里现态 0 次', f55[1].count(S10) == 0)
f55[1] = f55[1] + S10
f55[4] = f55[4] + L10
NEWP = '_r191/r191g_deliver.py;_r191/r191d_td.py;_r191/r191b_recheck.py'
ck('D10 旧第 4 列不含 _r191', '_r191/' not in f55[3], f55[3])
f55[3] = f55[3] + ';' + NEWP
ck('D11 新第 4 列含三条 _r191 路径',
   all(x in f55[3] for x in ('r191g_deliver.py', 'r191d_td.py', 'r191b_recheck.py')))

newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
R2 = [l.split('\t') for l in newtxt.split('\n')[:57]]
ck('D12 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 58 and all(len(x) == 5 for x in R2))
ck('D13 只有 F55 一行变化', [a[0] for a, b in zip(ORIG, R2) if a != b] == ['F55'],
   [a[0] for a, b in zip(ORIG, R2) if a != b])
ck('D14 F55 grade 未动', [r for r in ORIG if r[0] == 'F55'][0][2] == f55[2])
exp = 167276 + len(S10.encode()) + len(L10.encode()) + len(NEWP.encode()) + 1 \
      + (len(FIX_TO.encode()) - len(FIX_FROM.encode()))
ck('D15 体量按构造闭合', len(nb) == exp, (len(nb), exp, len(nb) - exp))
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
ck('D16 回读 sha 一致',
   hashlib.sha256(open(NEW, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V576 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(f55[1].encode()),
         len(f55[4].encode()), len(f55[3].encode())))
sys.exit(0)
