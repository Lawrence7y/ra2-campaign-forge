# -*- coding: utf-8 -*-
# R68 · 台账追加 §1123（CR 保持 337）
import io, os, hashlib, time, sys
DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))  # .../ra2-campaign-forge
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
P = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
CR_EXP = 337
fails, buf = [], []
def W(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

raw = open(P, 'rb').read()
ck('旧台账 CR=%d' % CR_EXP, raw.count(b'\r') == CR_EXP)
old = raw.decode('utf-8')
ck('旧台账以换行结尾', old.endswith('\n'))
ck('旧台账不含 §1123（防重复）', '§1123' not in old.split('本草为 §1122')[1] if '本草为 §1122' in old else True)
W('[before] %d B CR=%d LF=%d sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                        hashlib.sha256(raw).hexdigest()[:16]))

SEC = """

---

## §1123 【R17 第 68 轮 · 2026-11-22 21:5x】归档器重写并落盘；门禁 5 FAIL 定位到窗口表（未解）；§2.57 的「off-by-one」被自测判为错；5 处「永远通过」逐项实测完毕

一 · 归档器。R67 记「只认 🔴」不准确。盘上并存两种轮次记录形态：顶格 `## <emoji> R17 第 N 轮` 段头，以及 `> 📌 **第 N 轮（时刻）**：…` 笔记行（第 62–65 轮就是这种）。新归档器 `_r68/archive_r68.py` 用两条正则联合识别，只归档顶格段。

二 · 归档已落盘。`STATUS_BOARD` 59,004 → **40,567 B**（−18,437）、行数 269 → **234**、CR **0 未变**；`BOARD_ARCHIVE` 598,161 → **617,308 B**（+19,147）、CR **2,952 未变**。第 61、66 轮（非空 16 + 17 行）逐字搬入两个 `<details>`，`missing=0`。归档器自测 30 项全 PASS，含三项反控。

三 · 归档器自测里我自己犯的两个错（已抓已改）。① `missing_count` 把空行算作命中 —— 空串在任何文本里都存在，17 行里 1 个空行被当成「已搬」，反控因此报 16/17；修法为只数非空行。② 第一版反控拿「丢段头的切片」去新归档里查，正文本来就在、只丢标题 ⇒ `missing=0`，反控假失败；正确做法是把检测器指向**确实不含该内容**的旧归档。

四 · 门禁 5 FAIL。Linux 上 `check_disc.py` 无法直接运行（`ROOT` 硬编码 `D:\\`、`rel.replace('/','\\\\')` 反向转换）。用只替换这两处的探针复现出与 Windows 一致的 `ok=0 fail=5 frozen=12 none=11`，5 条串均为 `R4 at outside R055 window [17:41:46, 17:46:45)`。**这是口径偏差，不是等价物，已在 §2.74 写明。**

五 · 窗口语义判别。35 份无 add 后缀的规范快照，内容里最后一轮的编号**全部 = N−1**，「= N」的 0 份 ⇒ `before_rN` 拍在第 N 轮写板之前，第 N 轮的窗口起点就是 `before_rN`。现行表这一点没错。

六 · 未判的一项。5 条自述行的 `at` 是 17:39:19 / 17:40:02，落在 `[before_r54=17:34:00, before_r55=17:41:46)` 内，按现行表属**第 54 轮**窗口，而行里标 `round=R55`。两个解释（窗口错 / round 字段错）都缺决定性材料，**本轮不选、不填空**。

七 · §2.57 的「off-by-one」被自测判为错。四组对照（同代码只改 `_ROUND_ROWS`）：原样 5/5；只前移 r55 5/5；20 条全量重映射 **4/5**（POS 的 `at=16:20:00` 从原 R52 `[16:17:50,16:28:03)` 落到重映射后的 `[16:01:44,16:17:50)` 外）；全部放宽到全天 4/5（**NEG3 越窗被抓**）。⇒ 自测把「R52 起点 = before_r52」固化成可执行断言，全量重映射推翻它，而第五条独立证明起点语义是对的 ⇒ **全量重映射错，§2.57 的「off-by-one」说法错**。同时纠正我 §2.59 的一处过度声称：自测**抓得住放宽**（抓在 NEG3 一侧），并非抓不到。

八 · 5 处「永远通过」实测（沙箱内跑，逐项带正控反控，24 项断言全 PASS）。① C7 `bytes=N`：28 行前缀实测 `grep=21/grepcount=3/rows=4/bytes=0`，无人使用但**不是死代码**（改一行成 `bytes=999999` 立刻被抓，FAIL 5→6）。② C11 frozen 可摘帽：**成立且门槛是时刻** —— 写真实 17:39:19 不摘帽；写窗口内 17:42:00 ⇒ `ok 0→1`、`frozen 12→11`，其余字段一个字不改。③ claims-none 免检：**成立**；把冻结纪律 5 的「有」改「无」⇒ `frozen 12→11` 且 FAIL 数不变。④ C9 占位精确匹配：**成立**（`GARBAGE-CRITERION-OTHER` 照过；`TBD` 与空串都被抓）。⑤ C10 自证：**成立**（只改常量 FAIL；常量+登记串同改 ⇒ `ok(R99)`）。

九 · 本轮最重要的一条反向反控。把真做过并验证过的 3/4/22/27/28 五条第 7 列改成「无」⇒ 门禁**立刻 exit 0**、`C11=(0,0,12,16)`、无任何告警。⇒ **变绿的最短路径是删掉声称，不是完成工作。**

十 · 数字一个不动。`F24` / `FACT_INDEX` 语料 **4,417 件 / 737,517,286 B（v5.30）本轮不改**；`FACT_INDEX.tsv` 本轮未改；C/E 两条限定仍未写入 `limitations`（连续第二轮记）。

十一 · 子代理。T1（deepseek-v4.1-flash，窗口表独立复算）**回件失败**：`error_max_turns`，36 轮 / 实测 13.93 分钟 / 预算 8 分钟 ⇒ **`[OVERTIME]`**，产出为空。本轮全部窗口结论由主会话亲自脚本复算，未采信任何子代理结论。T2（hy4flash，5 处永远通过只读审计）已派发，回件后须由主会话复算。

十二 · 未取得（不掩盖）。① 第 55 轮那 5 条属第 54 还是第 55 轮未判（缺第 54 轮封口时刻的独立材料）；② `_ROUND_ROWS` 的注释串在 r56/r57 两行写成「乙」形态而数字仍是「甲」，注释与数据分裂未修；③ r57 终点仍为占位 `235959`（`before_r58`=17:52:00 本可填），改它会收窄窗口、属判据变更，须与①一并裁；④ ①③④⑤ 四处的修法均未落地；⑤ Linux 上两脚本仍不可直接运行；⑥「引用义务 vs 证据声称」仍是判读（第五十四次记）。

本草为 §1123 草稿，由 Lead 逐字追加；书记员未自行改动台账。
"""

new = old.rstrip('\n') + SEC
ck('追加内容无 CR', '\r' not in SEC)
ck('追加内容以换行结尾', new.endswith('\n'))
ck('新台账 CR 总数仍 = %d' % CR_EXP, new.count('\r') == CR_EXP, str(new.count('\r')))
ck('新台账含 §1123 且仅 1 次', new.count('## §1123') == 1, str(new.count('## §1123')))
ck('旧内容为新内容前缀（纯追加）', new.startswith(old.rstrip('\n')))
# 反控：判别力
ck('反控「纯追加」有判别力：改动旧文即 False', new.startswith(old.rstrip('\n')[:-1] + 'X') is False)
ck('反控「CR 不变量」有判别力：注入 CR 即不等', (new + '\r').count('\r') != CR_EXP)

ts = time.strftime('%Y%m%d_%H%M%S')
bk = os.path.join(BASE, 'SUPERSEDED.before_r68_write_ledger_%s.md' % ts)
W('')
W('[backup] wx 独占创建 ' + os.path.basename(bk) + ('  [DRY]' if DRY else ''))
if not DRY:
    with open(bk, 'xb') as f:
        f.write(raw)
    assert open(bk, 'rb').read() == raw
    ck('备份字节一致', True)
    open(P, 'wb').write(new.encode('utf-8'))
b2 = open(P, 'rb').read() if not DRY else new.encode('utf-8')
W('[after] %d B CR=%d LF=%d sha=%s' % (len(b2), b2.count(b'\r'), b2.count(b'\n'),
                                       hashlib.sha256(b2).hexdigest()[:16]))
ck('回读字节 == 预期', b2 == new.encode('utf-8'))
ck('回读 CR=%d' % CR_EXP, b2.count(b'\r') == CR_EXP)
ck('回读 增量 = 新节字节', len(b2) - len(raw) == len(new.encode()) - len(raw),
   '%+d B' % (len(b2) - len(raw)))
W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
if not DRY:
    io.open(os.path.join(HERE, 'write_ledger_r68.log'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(buf) + '\n')
sys.exit(0 if not fails else 1)
