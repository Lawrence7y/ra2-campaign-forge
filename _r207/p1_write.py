#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 落盘一：四件套追加（bytes 模式，CR 计数保持）。
纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
四件套必须纯 LF 追加（R206 事故教训：CRLF 追加触发 guardian 回滚）。"""
import os, hashlib, time, json

B = '/home/t628/projects/ra2-campaign-forge'
G = B + '/lead/next_re_20261117_r14'
LD = B + '/lead'
BL = B + '/R17_LEAD_BASELINE'
stamp = time.strftime('%Y%m%d_%H%M%S')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def crc(p):
    return open(p, 'rb').read().count(b'\r')


def nlf(p):
    return open(p, 'rb').read().count(b'\n')


def backup(p, tag):
    d, b = os.path.split(p)
    bp = os.path.join(BL, '%s.before_r207_%s_%s.bak' % (b, tag, stamp))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    return bp


fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


SEC = '## 2.212 · R17 第 207 轮（2026-11-28）· pBCA 元素是 BCD 记录地址（R206 口径误述订正）；BCD 24 B 六字段全实证；视图生成律 L* 判别域 99/99 零例外\n\n'
BODY = r'''**一、🔴 口径订正（砸掉 R206 的三处表述）.** `pBCA` 数组的每个元素是 **24 B BCD 记录的地址**，不是 pTD；比较 pTD 必须再解引用一层 `P.dw(b)`。据此复测：
- **954 个 pBCA 值互不相同**（R206 QI7 括号里「pBCA 可被多条记录共享」是**误述**）；
- R206 的「块内 BCD 槽集 == 首次出现集合 只 876/953」的差额 **77**，成因是 **BCD 记录被多个类的 BCA 共用**（实测 **304** 条记录被 >=2 个类引用，多引用槽总数 1917），**不是** pBCA 共享；
- R206 QI5 的「多引用 304 条」本身正确，但当时未说明它是**记录级**而非数组级。
另：`BCA[0]` 的 `P.dw(BCA[a][0])` == 本类内嵌 COL 的 pTD，**954/954**；反控 `BCA[1]` 命中 **0**、`BCA[0]+4` 当 pTD 命中 **0**。

**二、🔴 BCD 24 B 六字段全实证（`_r207/m6_final.py` 30 断言，7 条为预期写错被实测砸掉）.**

| 偏移 | MSVC 字段 | 实测 |
|---|---|---|
| +0 | pTypeDescriptor | 988 种（去重），全部落 `.data`，TD 的 `+8` 是**内联名字**（不是指针） |
| +4 | numContainedBases | 见第三节定律 |
| +8 | mdisp (int) | **0 有 978 条 / 非零 24 条**（R205 的 387 是 **BCA 槽数**，非记录数） |
| +12 | pdisp (int) | 恒 **−1**，1002/1002 |
| +16 | vdisp (int) | 恒 **0**，1002/1002（无虚基类） |
| +20 | attributes | `{0:991, 2:7, 9:4}` |

**记录身份键**：单 `pTD` 去重 **988**、`(pTD,mdisp)` 去重 **999**、`(pTD,mdisp,attributes)` 去重 **1002**、全六字段去重 **1002**。⇒ R206 QI6 的「pTD 去重 988（14 重复）⇒ COMDAT 折叠至多解释 14 条」需细化为：**5 个 pTD 有 8/3/3/3/2 条记录**（共 19 条记录、14 条多余），其中 3 组是「同 pTD 同 mdisp==0」、仅 `attributes` 不同（`0x816b70 .?AUIUnknown@@` / `0x8177e8 .?AVINoticeSource@@` / `0x81c038 .?AV?$VectorClass@H@@`，后者一条 `attributes=9`），另 2 组是同 pTD 不同 mdisp 的真 MI 子对象记录。

**三、🔴 新律（numContainedBases 的归属）.** 1002 条记录分成 **959 条「pTD 在本镜像有对应类头」+ 43 条「pTD 无类头」**。对**有类头的 959 条**：`+4 == numBaseClasses(该类) − 1`，**959/959 零例外**；反控「`+4 == 引用者数 − 1`」仅命中 **57**。43 条无类头记录的 `+4` 分布 `{1:25, 0:15, 2:2, 4:1}`，且 `pTD` 去重 **34** 个：`.?AU*` **24** 个 + `.?AV*` **10** 个（COM 接口 31 条 / 普通类 7 / 模板 3 / ATL 2）。

**四、🔴 视图生成律 L\*（本轮最强交付，判别域 99/99 零例外）.** 类 a 的 BCA 中若存在 `mdisp==m≠0` 的项，则 `m` 上产生一条额外视图 COL，**当且仅当 `m` 上有至少一个 pTD 在全局曾以 `mdisp==0` 身份出现过**（记该 pTD 集为 `primary`，实测 **975** 个）；「只在非零 mdisp 出现」的 pTD 记 `onlysec`，实测 **13** 个。
- 逐类比对**全量 954/954 命中**、视图总数预测 **260 = 实际 260**；
- **(类,mdisp) 级双向 281/281 零例外**；
- **判别力检验**：954 类里 **855 类两侧都是空集**（空对空，自动通过、无判别力），真正判别域 **99** 类（`tp=94, fp=0, fn=0, tn=5`），律在判别域 **99/99**；
- **七档反控在判别域上的得分**：无条件（任何非零 mdisp）**84**、条件「pTD 有类头」（m9 的错律）**8**、条件「名字 `.?AV` 前缀」**3**、反条件「只在 onlysec」**13**、条件「全部 pTD（恒真）」**84**、随机 dword 集三次 **16 / 8 / 5**；(类,mdisp) 级随机 pTD 三次 **179 / 122 / 100**（律为 **281/281**）。
- **15 个「朴素律例外」被 L\* 全部解释**（朴素律 = 「BCD 非零 mdisp 集 == 视图 mdisp 集」，949/954）：缺的视图 mdisp 全部由 `onlysec` 的 13 个 pTD 造成，肇因命中次数 `StageClass 9 / FlasherClass 6 / CComObjectRootEx@ATL 5 / CComObjectRootBase@ATL 5 / BounceClass 1`。三族分解：`attributes==1 普通类 8` / `ATL-CCom 事件 sink 5` / `attributes==5 2`。

**五、🟡 R205 QG4 的 bit0 语义订正.** `attributes bit0 == 1` ⟺ **该类 BCA 中存在 `mdisp!=0` 的 BCD**（**954/954**，双向零例外）；而「bit0 ⟺ 有额外视图」只有 **949/954** ⇒ R205 QG4 的两条表述在 5 个 ATL/CCom 事件 sink 上分离（`0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998`，它们有非零 mdisp 的 ATL 基类记录但**不产生视图**，因为 `CComObjectRootBase@ATL@@` / `CComObjectRootEx@...@ATL@@` 属 onlysec）。这 5 个也正是 R205 QH9 遗留的「5 个 ATL 类为何无第二张 vftable」——**本轮给出成因**：其基类 pTD 从未以主基类身份出现，故 MSVC 不为其生成第二张 vftable。

**六、🟡 TypeDescriptor 头.** 全 954 个类 TD 与 43 条无类 TD 的 `+0` **全等**（单一值 `0x7f9594`，落 `.rdata`）、`+4 (spare)` 恒 **0**。`0x7f9594` 不是 type_info vftable 常规形态（其槽 1..3 读成 ASCII `eccA soli`），本机静态字节无法判定其原义 ⇒ **如实记为未取得**，不改称「vftable」。

**七、📌 自错 6 组（0 条进结论）.** ① m2 用 `own_td[a]` 直接和 `BCA[a][0]`（记录地址）比，得 `lead=0`；② m3 因此连带 LA.2/LA.3/LC.1 全 FAIL，订正后 954/954；③ m5 预设「1002 = 954 自有 + 48 非自有」，实测 **978 + 24**（R205 的 387 是槽数）；④ m6 预设「无类头 TD 的 TD 头 +0 恒 0」，实测全 954 个 TD 的 `+0` 同为 `0x7f9594`；⑤ m9 首版律用「pTD 有类头」当条件，预测 863/954、视图 159/260（**错**），被 m10 的 `primary` 口径取代；⑥ **m10 的反控 C4「primary 集随机置换」得 954/954 PASS 是假通过**——随机集与 primary 同尺寸时，855 个空对空类自动通过，真判别域只有 99 类；改用判别域计分后随机反控降到 16/8/5。**教训：在「两侧多为空集」的集合律上，全量命中数不是判别力指标，必须报告判别域。**

**八、🟡 跨家族.** 执行员 **#524**（hy4，7 回合 / 0.49 分 / 无 OVERTIME）：6 项中 5 项 PASS、1 项 CONFLICT，**逐数复现**（954/954/2615/1002、`BCA[0]` 与内嵌 pTD 954/954、8 对齐 1002/1002、`+4` 命中 959/959、`pTD` 去重 988 vs 全字段 1002、无类头 TD 34 个）。其 **CONFLICT 成立且采纳**：24 B 是**单条记录尺寸**而**不是相邻记录的固定步长**——实测相邻差 `{80:373, 24:294, 128:108, 72:40, 176:25, ...}`，仅 **294/1001** 恰为 24。其「无需二次解引用」的口径判定与主会话一致。审计员 **#525**（deepseek）在本轮预算内未产出 REPORT（详见 LEAD_LOCK QJ）。

**九、🟡 落盘.** R14_COMMON **§2.212** CR 保持 **1081**；GOAL **§1262** CR 保持 **337**；LEAD_LOCK **QJ** CR 保持 **137**；STATUS_BOARD 第 207 轮 CR 保持 **0**。'''
appends = [
    (G + '/R14_COMMON.md', '/r14', 1081, SEC, BODY),
]
for p, tag, expcr, head, body in appends:
    pre = sha(p)
    cr = crc(p)
    ck('W1 %s 旧 CR == %d' % (os.path.basename(p), expcr), cr == expcr, cr)
    b1 = backup(p, tag.strip('/'))
    ck('W2 备份一致 %s' % os.path.basename(b1), sha(b1) == pre, os.path.basename(b1))
    payload = (head + body + '\n').encode('utf-8') + b'\n'
    data = open(p, 'rb').read() + payload
    open(p, 'wb').write(data)
    ck('W3 %s CR 保持 %d' % (os.path.basename(p), expcr), crc(p) == expcr, (crc(p), expcr))
    ck('W4 回读含 §2.212', '## 2.212' in open(p, encoding='utf-8').read())

print('== 四件套 1/4 完成 asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
