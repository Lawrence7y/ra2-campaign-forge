#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 落盘四：STATUS_BOARD 追加第 206 轮（全 LF，CR 保持 0，总行数 <= 300）。
开局 245 行 < 260 ⇒ 不归档。"""
import os,hashlib,time,json
B='/home/t628/projects/ra2-campaign-forge'
P=B+'/lead/next_re_20261117_r14/STATUS_BOARD.md'
BL=B+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(P,'rb').read()
ck('B0 开局行数 < 260（无需归档）',raw.count(b'\n')<260,raw.count(b'\n'))
ck('B1 开局 CR == 0',raw.count(b'\r')==0)
bp=os.path.join(BL,'STATUS_BOARD.md.before_r206_%s.bak'%stamp)
fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(raw)
ck('B2 备份一致',sha(bp)==sha(P),os.path.basename(bp))
SEC='''
## 🟢 R17 第 206 轮（2026-11-28 14x–15x）· 类头**恰 36 B**（R205「≥40 且 ≤48」收窄）；RTTI 区间 0x7fa4b0..0x80efc4 = **84756 B 完全字节记账**（无空洞无重叠）；块分解/对齐/归属/尾部四律；+36 不是本条字段

**交付一 · 结构订正（取得 R205 未取得项①）.** 类头 **恰 36 B**：`+0`=0 / `+4`=attributes / `+8`=numBaseClasses / `+12`=pBCA / `+16..+35`=内嵌主对象 COL 20 B（`pCHD`==头自身，954/954）/ `+32`==头地址自身（自指 954/954）。**`+36` 不是本条字段**：953 条中无任何值等于本条 自身地址 / `+16` / 本条 pBCA；26 个「等于本条 pTD」的值逐条核查**全是别名**（等于下一条块首 BCD 的 pTD，位置恒 `+40`，`m30_pin.py` 4 断言 0 FAIL）。**最小类块间距 48** = 36 + 12（下一条块最小尺寸），R205 报的「间距恰 40」为 **0 条** ⇒ 「≥40 且 ≤48」收窄为**恰 36**。

**交付二 · 完全字节记账（本轮最强证据）.** 区间 `[0x7fa4b0, 0x80efc4)` = **84756 B**，**每个 dword 恰归一类、无空洞、无重叠**：类头（含内嵌 COL）**34344**（954×36）/ 额外视图 COL **6240**（260×24）/ BCD **24048**（1002×24）/ BCA **10460**（2615×4）/ 对齐 pad **9664**（2416 dword，**值恒 0**，只出现在块首 pad0（0|4 B）与块尾 pad1（4|8 B））。四项结构性条数与 R204/R205 逐一吻合；唯一「新料」是 pad 的 2416 dword。

**交付三 · 律 1（块分解）.** 块 = `[pad0 0/4][24 B 项 × k][BCA 4n][pad1 4/8][36 B 类头]`，953 条（除首条）**唯一解析**。24 B 项只有两类：额外视图 COL（`pCHD`==本类头，记 C）与 BCD（`pTD` 在 `.data` 且 `+12` 的 pdisp 恒 −1，记 B）；**C 恒为前缀**且每块 C 数 == 该类视图数 − 1（953/953，合计 260）。判别位是项内 `+12`：**C 项过 BCD 判据 0/260、B 项过 COL 判据 0/1002**（双向反控）。

**交付四 · 律 2（对齐，审计订正后）.** 原写法「pBCA 8 对齐 ⟺ (k≥1 或 n≥2)」经审计 #522 A2 指出是**恒真式**（由 `(pBCA−q)%24==0` 与 `24≡0 mod 8` 直接推出，`all(pBCA%8==(4+pad0)%8)` 为 True），不可证伪。改后三条可检验：① **24 B 项恒 8 对齐**（1262 项全成立）；② **`{pad0==0}` == `{k==0 且 n==1}`**（各 205 条，对称差 0；审计 A1 提出、采纳）；③ 判别样本确实存在——`k≥1 且 n==1` **51** 条、`k==0 且 n≥2` **30** 条。pad1：`(pBCA+4n)%8==0 ⇒ 8`（713）/ `==4 ⇒ 4`（240），无例外。

**交付五 · 律 3（BCD 物理归属）+ 审计 A3 采纳.** 持有块 == `min{引用者类头 : 类头 > BCD 地址}`，**1002/1002**；去掉该条件改用 `min{全部引用者}` 只剩 **958/1002**、`max` **722**、绝对最近 **966**。**审计 #522 A3 指出：`min{全部类头 : 类头 > BCD}`（完全不看引用关系）也 1002/1002 ⇒ 上述 min/max/最近反控不构成结构证据**；律 3 唯一非平凡内容是**持有块自身必引用该 BCD**（1002/1002；随机基线 2435/497974 ≈ 0.49%）。多引用样本实测 **304** 条（非审计报的 280），其上 min **260** / max **24** / 最近 **268** —— 审计给的 280/0/264 **复算不成立**。

**交付六 · 律 4（尾部 12 字节）.** 形态**恰 4 类、合计 953**：`(PAD0,B,B)` **624**（+36==0、+40==下一条块首 BCD 的 pTD、+44==其 numContained）/ `(A,PAD1,PAD1)` **205**（+36==下一条 BCA 数组首指针）/ `(PAD0,C,C)` **94**（+44==首额外视图 COL 的 mdisp）/ `(PAD0,A,A)` **30**（+40==BCA[0]、+44==BCA[1]）。**去恒等后**（不能拿 a+36 与 prev+36 比 —— 审计 A4 指出那是定义恒等）按「下一条块的解析结果」预测这 3 个 dword，**953/953 全命中**。审计 A6 两条订正：624 条里 `+40` 落进本条 BCA 的 pTD 集的**只有 37 条**；pTD 去重 **988**（14 重复）⇒ **COMDAT 折叠至多解释 14 条**，原「624 因折叠」撤回。

**自错 8 组（0 条进结论）.** ①把 `+36` 当本条字段（被 26 别名 + 953 条预测砸掉）；②「块内 BCD 槽 == 本条 BCA 首次出现集合」只 876/953（pBCA 数组可被多条记录共享）；③「pad0==0 ⟺ prev+36 已 8 对齐」错（实为 `k==0 ∧ n==1`，两条 30 条反例）；④`m20` N1/N2「块起点位移 ±4 后无一可解析」**不成立也不应成立**（pad0 是可选槽，+4 得 748/953）——起点唯一性改由「24B 项 8 对齐 + 记账无空洞无重叠」承担，不靠解析器歧义；⑤`m20` X1/X2「不含本条任何字段」过强（26 别名）；⑥`m26` A3.4/A5.3 两条口径写错，由 `m27/m28` 订正；⑦`m29` 1.3 与 5.2 两条过严，由 `m30` 钉死；⑧首跑 `m8_final` 强绑 pad0=4 致 624 条误判为 pad（pad 一度误计 50388 B）。

**跨家族.** 执行员 **#521**（hy4，16 回合 / 1.77 分，**无 OVERTIME**）5 PASS + 1 CONFLICT，全部数字由主会话 `m25_verify_exec2.py`（10 断言 0 FAIL）复算：区间 **21183 dword** / HEAD36 **8586** / ITEM24 **1560** / BCD **6012** / BCA **2611**（=2615−4，首条类 BCA 在区间左端之外）/ 未归属 **2414**（其报 2412，差 2）—— **逐项复现**；其 CONFLICT 是**口径差异**（把 pad 归入「未归属」，而该 2414 个 dword **值全为 0**，正说明是填充非缺失子结构）；其 E5 口径（视图数−1）**860/10/6/76/1/1 复现**。两处订正：`max(HEAD)=0x80eea0` 是笔误（实为 `0x80efa0`，0x80eea0 是 `__non_rtti_object` 类头）；四项相加 21182 ≠ 21183（内部差 1）。审计员 **#522**（deepseek，11 回合 / 5.97 分，**无 OVERTIME**）六问：**采纳 5 条**（A1 pad0 确定性、A2 律 2 恒真、A3 律 3 反控不构成结构证据、A4 恒等式、A6 的 37/988），**订正 1 条**（其 A3 的 280/0/264 与 A6 的 X1=165/X2=127 复算不成立，实测 304/260/24/268）。

**落盘.** R14_COMMON **§2.211** CR 保持 **1081**（712ac1ef→新，+9,654 B）；GOAL **§1261** CR 保持 **337**；LEAD_LOCK **QI** CR 保持 **137**；STATUS_BOARD 第 206 轮 CR 保持 **0**（开局 **245 行 < 260**，**不归档**，收口后行数见下）。C16 纳入新节 211（下界 **4826** = 实测 9653 B 的一半），C16_FLOORS_SHA256 **cf44f1aa → c7b6b948**，节数 pinned 202 → **203**、unpinned 0。三门 exit 0：check_disc（C15 203 节 / 末节 211 / 1821301 B、C16 203/203 无缺、C16d OK、C19 ok(bfad05b0/239742/V588)、C20 ok(V588)）、facts_floors、gate_runner。

**重要事故（如实记录）.** 本轮落盘一用 **CRLF** 追加三件套，**re-guardian 判为 broken 并用 R202 备份自动覆盖**（journal：`Auto-restored R14_COMMON from R14_COMMON.md.before_r202_...bak`），一度丢掉 2.207–2.210 四节。已从本轮 `before_r206_*` 备份完整恢复（sha 逐一核对一致），并改用 **LF only** 追加重写。**教训：四件套的 CR 计数是既有文件的属性，追加内容必须与文件既有的行尾风格一致（R14_COMMON/GOAL/LEAD_LOCK 是 CRLF 主体但新节必须 LF？——实测：只有纯 LF 追加能同时满足「CR 计数不变」与「guardian 不判 broken」）。**

**未取得.** ① pad0 二值语义；② 708 run / 段边界与类块边界的对应未打通；③ 14 条 pTD 重复记录语义；④ BCA 数组被多记录共享（pBCA 同址）的成因；⑤ R205 遗留 5 项（`COL.sig`/`cdOffset` 原义、3 反例语义、5 条 `.?AV` 无 vftable、2 个 TD 各 2 条、`UIUnknown` 两条差别）；⑥ R204 遗留 2 项（464 非等差中 111 短 BCA、`attributes 5 vs 1`）；⑦ 5 个 ATL 类无第二张 vftable、260 被吞候选归类、94 MI 类基类名链；⑧ R200 (c)(d)(f)(g)；⑨ F23/F35 grade；⑩ 两个 tsv 不可读；⑪ 86.19% 不可重算；⑫ C7 三死分支 0 行；⑬ C11 十二个 ID 未动。
'''
new=raw+SEC.encode('utf-8')
ck('B3 新增内容无 CR',b'\r' not in SEC.encode('utf-8'))
fd=os.open(P,os.O_WRONLY|os.O_TRUNC); os.write(fd,new); os.close(fd)
chk=open(P,'rb').read()
ck('B4 前缀不变',chk[:len(raw)]==raw)
ck('B5 CR 保持 0',chk.count(b'\r')==0,chk.count(b'\r'))
ck('B6 总行数 <= 300',chk.count(b'\n')<=300,chk.count(b'\n'))
ck('B7 第 206 轮标题存在',b'R17 \xe7\xac\xac 206 \xe8\xbd\xae' in chk)
print('   STATUS_BOARD %d -> %d B, %d -> %d 行'%(len(raw),len(chk),raw.count(b'\n'),chk.count(b'\n')))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,bytes=len(chk),lines=chk.count(b'\n'),sha=sha(P)),
  open('_r206/p4_board.json','w'),indent=1)
