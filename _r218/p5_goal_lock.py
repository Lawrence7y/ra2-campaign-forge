# -*- coding: utf-8 -*-
"""R218 p5：GOAL §1276 + LEAD_LOCK QL 段追加。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/R17_LEAD_BASELINE'; T=ROOT+'/lead/next_re_20261117_r14'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r218_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted '+tag)

GOAL = """
## §1276 · R218（2026-11-28）· 虚表口径二分（1214 真表 + 4 幻影，与 1214 COL 双射）+ BCD 记录 24 B 订正 + 464 高槽 cov294/diff67/oob103 + disp 扫描定稿；FACT_INDEX V600

- **虚表口径二分**：`dw(V-4)==COL` 候选 1218，其中 `dw(V)` 落 `.text` 的 **1214**；余 4 个（`0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`）全在 `.data`、形态 `c0000001 00000000 00000000 00800040`、槽数 0、`.text` 内引用 0（正控 `0x7e8278` 4 次 / `0x7e1f50` 5 次）⇒ 幻影。
- **双射**：真虚表 1214 ↔ COL 1214，单射与满射同时成立 ⇒ R217「5 张视图共用 COL 0x800040」在真表口径下不存在；`mdisp!=0` 视图 264 vs 260 之差 4 即幻影。总槽 14044、主视图 954/slot≥3 9958 不受影响。
- **BCD 24 B 订正（自错 E6）**：pBCA 是 4 B 指针数组；元素 `+0` 合法 pTD 94/94，反控按 0x1c 步长 0/94，`+0x18` 落点合法 pTD 84/94（= 下条记录 +0）⇒ 「+0x18 为 pCHD」「内联记录数组」两写法作废。
- **464 高槽归因**：父类 = 基类数组后继项，Unit/Infantry/Aircraft→Foot、Foot/Building→Techno、Techno→Radio，**6/6 PASS**；cov **294** / diff **67** / oob **103**，父类范围内覆盖 **81.44%**；oob == Σmax(0, n−max(par_n,256))；464 目标去重 170、本表低槽重复 1、与全表任意子段最大公共前缀 ≥12 的拼接候选 **0**（反控随机 10 对为 0）。
- **disp 扫描定稿**：逐字节 sweep 解码 **1,394,120** 条指令；`call/jmp [reg+disp]`（排除 esp）**18,930**；`disp==0x2c` **1114**、`disp==0` **819**、`disp==0x48` **930**；slot≥256 **931** 位点 / **91** 个 s / 非 4 对齐 **0**；925 落 UnitClass 槽域、6 处 s∈{479,480,481,482,2224418} 超 344 待定性。口径警告：931 与 R215 的「931 处 +0x48」是巧合（实测 disp==0x48 为 930）。
- **自错 E1–E3**：固定 64 KB 切块截断（1,150,117 条）/ 按末完整指令推进遇非法字节不足（155,215 条）/ 把指针数组当内联记录；0 条进结论。
- **跨家族**：card C(#567 hy4 exec，21 回合 / 3.18 分 vs 12，无 OVERTIME)、card A(#565 hy4 exec，**failed / error_max_turns / 61 回合 / 9.3 分 vs 12**，卡 A 的 A1 父类判定卡面假设有误，结论改由主会话 m8 取得)、card B(#566 hy4 exec，succeeded)。主会话对 card C 六数独立复算一致（差 5 处 esp 基址）。
- **落盘**：R14_COMMON §2.226 CR=1081（1928694→1934174 B）；本段 §1276 CR=337；LEAD_LOCK QL CR=137；STATUS_BOARD 第 218 轮 CR=0。**FACT_INDEX V599→V600**（仅 F29 一行）277566→**280689** B，sha `616a86e2`→**`fb513cc8`**；facts_floors MASTER `b058464c`→**`37c8063f`**、gate_runner LEDGER→V600、指针同步。三门 exit 0。
"""
p=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'; b0=bak(p,'GOAL')
assert b0.endswith(b'\n') and b0.count(b'\r')==337
new=b0+GOAL.encode('utf-8')
assert new.count(b'\r')==337
open(p,'wb').write(new); chk=open(p,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==337
print('[写入] GOAL bytes %d -> %d CR %d sha %s -> %s'%(len(b0),len(chk),chk.count(b'\r'),
      hashlib.sha256(b0).hexdigest()[:16],hashlib.sha256(chk).hexdigest()[:16]))

LOCK = """
**QL. 🔴 虚表口径二分：1214 真表 + 4 幻影，与 1214 条 COL 双射.** `dw(V-4)==COL` 候选 **1218**，加 `dw(V)` 落 `.text` 后 **1214**。
差集 4 个 `0x877000`/`0x877010`/`0x87b17c`/`0x87b18c` 全在 `.data`，形态 `c0000001 00000000 00000000 00800040`（`+0xc` 才是 COL `0x800040`），
槽数 **0**，`.text` 内 dword 引用 **0**（正控 `0x7e8278` 4 次 / `0x7e1f50` 5 次）。`.data` 内 COL `0x800040` 出现 **4** 处，恰为 4 个候选的 `V-4`。
⇒ 真表 **1214** ↔ COL **1214** 单射且满射；R217「0x800040 被 5 张视图共用（唯一示例）」在真表口径下**不存在**；
`mdisp!=0` 视图 **264（含幻影） vs 260（真表）** 之差 4 即此。总槽 **14044**、族数 **954**、主视图 **954**、主视图 slot≥3 **9958** 与 R217 逐数一致。

**QL2. 🔴 BCD 记录 24 B / pBCA 是 4 B 指针数组（自错 E6 订正）.** `CHD+8`=numBase、`CHD+0xc`=pBCA；
元素 `+0` 解出合法 pTD **94/94**；反控按 0x1c 步长 **0/94**；`+0x18` 落点合法 pTD **84/94**（= 下条记录 `+0`）。
⇒ 「`+0x18` 是 pCHD 字段」「pBCA 是内联记录数组」两写法作废。

**QL3. 🔴 464 个 slot≥256 槽归因：cov 294 / diff 67 / oob 103.** 父类 = 基类数组后继项（ncb 递减序），
Unit/Infantry/Aircraft→Foot、Foot/Building→Techno、Techno→Radio，**6/6 PASS**。
父类范围内覆盖 **294/361 = 81.44%**；`oob` 恰等于 `Σ max(0, n − max(par_n,256))`（校验 PASS）。
464 目标去重 **170**、全落 `.text`、本表低 256 槽内重复 **1**；每表 × 全 1214 表的全部 shift 最大公共前缀搜索，**≥12 的拼接候选 0 条**
（反控随机 10 对无关表最大公共前缀 **0**）⇒ 高槽段不是拼接、也不是父类整体复制。

**QL4. 🔴 disp 扫描定稿口径.** 逐字节 sweep（遇非法字节前进 1 B）解码 **1,394,120** 条（非法跳 66，末指令 `0x7e0ffd`）；
`call/jmp [reg+disp]`（无索引、排除 esp）**18,930**；`disp==0x2c` **1114**、`disp==0` **819**、`disp==0x48` **930**；
slot≥256 **931** 位点 / **91** 个不同 s / 非 4 对齐 **0**；正控 `0x41021a` 命中。
**口径警告**：931 与 R215「931 处 +0x48 消费位点」是**巧合**（实测 disp==0x48 为 930），两数不可互引。

**QL5. 🟡 自错 3 条 / 跨家族.** E1 固定 64 KB 切块截断（1,150,117 条）；E2 按末完整指令推进遇非法字节不足（155,215 条）；
E3 把指针数组当内联记录。0 条进结论。card C（#567 hy4 exec，21 回合 / 3.18′ vs 12，无 OVERTIME）六数独立复算一致；
card A（#565 hy4 exec）**failed / error_max_turns / 61 回合 / 9.3′ vs 12**，其 A1 卡面父类假设有误，改由主会话 m8 取得；
card B（#566 hy4 exec）succeeded。

**QL6. 🟡 收口.** `_r218/m11_final_ctl.py` **34 断言 0 FAIL**、`_r218/m21_freeze.py` 终值一条命令复现。
R14_COMMON **§2.226** CR 保持 **1081**（1928694→1934174 B）；GOAL **§1276** CR 保持 **337**；本段 **QL** CR 保持 **137**；
STATUS_BOARD 第 218 轮 CR 保持 **0**。**FACT_INDEX V599→V600**（仅 F29 一行）277566→**280689** B、sha `616a86e2`→**`fb513cc8`**；
`facts_floors` MASTER `b058464c`→**`37c8063f`**、gate_runner.LEDGER→V600、`FACT_INDEX_CURRENT.md` 同步。三门 **exit 0**。

**QL7. ⚪ 未取得.** ①6 处 s∈{479,480,481,482,2224418} 超 344 槽域的位点定性；
②占 464 中 **67** 个「diff（与父类不同）」的语义归类（本轮只给前缀分布）；
③`0x4a1ca0` 环缓冲容量 4 语义；④三全局 `0x887680/84/88` 运行期初值（virt-only，须 win-main）；
⑤律 W 违例 360 条逐类内嵌偏移全表；⑥F23/F35 grade；⑦C7 三死分支、C11 十二 ID。
"""
p=ROOT+'/lead/LEAD_LOCK'; b0=bak(p,'LOCK')
assert b0.endswith(b'\n') and b0.count(b'\r')==137
new=b0+LOCK.encode('utf-8')
assert new.count(b'\r')==137,'LOCK CR %d'%new.count(b'\r')
open(p,'wb').write(new); chk=open(p,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==137
print('[写入] LEAD_LOCK bytes %d -> %d CR %d sha %s -> %s'%(len(b0),len(chk),chk.count(b'\r'),
      hashlib.sha256(b0).hexdigest()[:16],hashlib.sha256(chk).hexdigest()[:16]))
