# -*- coding: utf-8 -*-
# R68 · LEAD_LOCK 追加 CW 段（CR 保持 137）
import io, os, hashlib, time, sys
DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
P = os.path.join(os.path.dirname(os.path.dirname(R14)), 'lead', 'LEAD_LOCK')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
CR_EXP = 137
fails, buf = [], []
def W(s=''):
    print(s); buf.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
    if not c: fails.append(n)

raw = open(P, 'rb').read()
ck('旧 LEAD_LOCK CR=%d' % CR_EXP, raw.count(b'\r') == CR_EXP)
old = raw.decode('utf-8')
ck('旧文件以换行结尾', old.endswith('\n'))
ck('旧文件末段是 CV（下一字母应为 CW）', '## CV · R17 第 67 轮' in old)
ck('旧文件不含 CW 段（防重复）', '## CW · R17 第 68 轮' not in old)
W('[before] %d B CR=%d LF=%d sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                        hashlib.sha256(raw).hexdigest()[:16]))

SEC = """## CW · R17 第 68 轮（2026-11-22 21:5x）· 归档器重写（红/绿/图钉三种段头 + 笔记行形态）；门禁 5 FAIL 定位到窗口表但未解；§2.57 的「off-by-one」被自测判为错；5 处「永远通过」逐项实测完毕（三项成立、两项证伪我得出的旧断言）

CW1. 归档器。R67 记「只认 🔴」不够准确：盘上并存两种轮次记录形态 —— 顶格 `## <emoji> R17 第 N 轮` 段头（第 61/66/67 轮分别是 🔴/🔴/🟢），以及 `> 📌 **第 N 轮（时刻）**：…` 笔记行（第 62–65 轮全部是这种）。只看 emoji 前缀会同时漏「🟢 段头」与「笔记行」。新归档器 `_r68/archive_r68.py` 用两条正则联合识别轮次记录，只归档顶格段。

CW2. 归档已落盘。`STATUS_BOARD` 59,004 → **40,567 B**（−18,437）、行数 269 → **234**、CR **0 未变**；`BOARD_ARCHIVE` 598,161 → **617,308 B**（+19,147）、CR **2,952 未变**。第 61、66 轮（非空 16 + 17 行）逐字搬入两个 `<details>`，`missing=0`。自测 30 项全 PASS，含三项反控。

CW3. 归档器自测中我自己犯的两个错（已抓已改，都是「断言写坏」而不是「被测逻辑坏」）。① `missing_count` 把空行算命中 —— 空串在任何文本里都存在，17 行里 1 个空行被当成已搬；修法只数非空行。② 第一版反控拿「丢段头的切片」去新归档里查，正文本来就在 ⇒ `missing=0` 假失败；正确反控是把检测器指向**确实不含该内容**的旧归档。

CW4. 门禁 5 FAIL。Linux 上 `check_disc.py` 无法直接运行（`ROOT` 硬编码 `D:\\`、`rel.replace('/','\\\\')` 反向转换）。用只替换这两处的探针复现出与 Windows 一致的 `ok=0 fail=5 frozen=12 none=11`，5 条串均为 `R4 at outside R055 window [17:41:46, 17:46:45)`。**这是口径偏差，不是等价物**，已在 §2.74 与台账 §1123 写明。

CW5. 窗口语义判别（`_r68/window_r68.py`，全 PASS）。35 份无 add 后缀的规范快照，内容里最后一轮编号**全部 = N−1**，「= N」的 0 份。第一版解析器只认 `##` 段头，把 r63/r64/r65 误判成「max=61 违例」，补上笔记行正则后归零 —— **这是我自己的解析器缺陷，不是盘上的不一致**。

CW6. 未判的一项（不填空）。5 条自述行 `at` = 17:39:19 / 17:40:02，落在 `[before_r54=17:34:00, before_r55=17:41:46)` 内，按现行表属**第 54 轮**窗口，而行里标 `round=R55`。两解释（窗口错 / round 字段错）都缺决定性材料。缺的是「第 54 轮封口时刻」的独立材料。

CW7. §2.57「off-by-one」被自测判为错（`_r68/selftest_r68.py`，全 PASS）。四组对照同代码只改 `_ROUND_ROWS`：原样 **5/5**；只前移 r55 **5/5**；20 条全量重映射 **4/5**（POS 的 `at=16:20:00` 从原 R52 `[16:17:50,16:28:03)` 落到重映射后 `[16:01:44,16:17:50)` 外）；全部放宽到全天 **4/5**。**注意两条**：① 只前移 r55 并不打破自测（POS 用的是 r52）⇒ §2.59 记的「4/5」对应的是全量重映射，不是前移单行；② **自测抓得住放宽**，抓在 NEG3 一侧（`ok=True expect=False`）—— 我 §2.59 隐含的「放宽抓不到」是错的。

CW8. 5 处「永远通过」逐项实测（`_r68/alwayspass_r68.py`，24 项断言全 PASS，逐项带正控反控）。① C7 `bytes=N`：前缀实测 `grep=21/grepcount=3/rows=4/bytes=0`，现网无人使用，但**不是死代码**（改一行成 `bytes=999999` 立刻被抓，FAIL 5→6）。② C11 frozen 可摘帽：**成立，门槛是时刻** —— 真实 17:39:19 不摘帽；窗口内 17:42:00 ⇒ `ok 0→1`、`frozen 12→11`，其余字段一字不改。③ claims-none 免检：**成立**（冻结纪律 5「有」→「无」⇒ `frozen 12→11` 且 FAIL 数不变）。④ C9 占位精确匹配：**成立**（`GARBAGE-*-OTHER` 照过；`TBD` 与空串都被抓）。⑤ C10 自证：**成立**（只改常量 FAIL；常量+登记串同改 ⇒ `ok(R99)`）。

CW9. 本轮最重要的一条反向反控。把真做过并验证过的 3/4/22/27/28 五条第 7 列改成「无」⇒ 门禁**立刻 exit 0**、`C11=(0,0,12,16)`、无任何告警。⇒ **变绿的最短路径是删掉声称，不是完成工作。**

CW10. 数字一个不动。`F24` / `FACT_INDEX` 语料 **4,417 件 / 737,517,286 B（v5.30）本轮不改**；`FACT_INDEX.tsv` 未改；C/E 两条限定仍未写入 `limitations`（连续第二轮记）。

CW11. 子代理。T1（deepseek-v4.1-flash，窗口表独立复算）**回件失败**：`error_max_turns`、36 轮、实测 13.93 分钟 vs 预算 8 分钟 ⇒ **`[OVERTIME]`**，产出为空。本轮窗口结论全部由主会话亲自脚本复算，未采信任何子代理结论。T2（hy4flash，5 处永远通过只读审计）已派发，回件后由主会话复算。

CW12. 未取得。① 第 55 轮那 5 条属第 54 还是第 55 轮未判；② `_ROUND_ROWS` 注释串在 r56/r57 两行写成「乙」形态而数字仍是「甲」，注释与数据分裂未修；③ r57 终点仍为占位 `235959`（`before_r58`=17:52:00 本可填），改它会收窄窗口、属判据变更，须与①一并裁；④ ①③④⑤ 四处修法均未落地；⑤ Linux 上两脚本仍不可直接运行；⑥「引用义务 vs 证据声称」仍是判读（第五十四次记）。

现态：coverage.tsv 4,147,334 B / c2ee063f… / 18,498 行 / [已证] 1,654；strict 1,331；④ A 458 / B 291 / 宽 293 / 无④ 1,196；R_OK 863 / R_MISSING 0 / R_TRACE_ONLY 791；R14_COMMON 552,946 B（§2.6–§2.74）；台账 4,680,691 B（max §1123）；FACT_INDEX 权威 v5.30（54 条，语料 4,417 件 / 737,517,286 B，未改）；唯一内容体量 C 615,909,180 B / 4,087 簇、E 611,813,919 B / 4,084 簇；看板 234 行（+本轮段后 ≤300）；自测 archive 30/30 + window 全 PASS + selftest 7/7 + alwayspass 24/24；门禁 RED（5 FAIL）；待裁 0
"""

new = old.rstrip('\n') + '\n\n' + SEC
ck('追加内容无 CR', '\r' not in SEC)
ck('新文件 CR 总数仍 = %d' % CR_EXP, new.count('\r') == CR_EXP, str(new.count('\r')))
ck('含 CW 段且仅 1 次', new.count('## CW · R17 第 68 轮') == 1)
ck('旧内容为新内容前缀', new.startswith(old.rstrip('\n')))
ck('反控「纯追加」有判别力', new.startswith(old.rstrip('\n')[:-1] + 'X') is False)
ck('反控「CR 不变量」有判别力', (new + '\r').count('\r') != CR_EXP)

ts = time.strftime('%Y%m%d_%H%M%S')
bk = os.path.join(BASE, 'SUPERSEDED.before_r68_write_lock_%s.md' % ts)
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
W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
if not DRY:
    io.open(os.path.join(HERE, 'write_lock_r68.log'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(buf) + '\n')
sys.exit(0 if not fails else 1)
