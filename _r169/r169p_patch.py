#!/usr/bin/env python3
"""R169 P：四件套补记（同一轮内的第二段）—— 更正 OZ9 的「本轮不归档」并补记 C16 重钉 / 指针修正 / 三段实跑。

触发原因（自错 S-564）：我在写第一段时把看板行数按「写入前 236」写成「236 < 260 本轮不归档」，
但写入第 169 轮后是 **263 行 >= 260**，归档条件**已触发**并已执行（搬走最早 2 段，263→166），
第二段必须如实登记，不能留一句与磁盘相反的陈述。
另补三件第一段漏记的事实：① C16 下界重钉（168 节）；② FACT_INDEX_CURRENT.md 指针两轮未更新、本轮改正；
③ 三段实跑（含 gate_runner 一次真红与修法）。

纪律：备份 wx 独占 → 断言旧 sha 与 CR → 一次性写 → 回读校验；CR 必须一字不变。
"""
import hashlib, json, os
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
RC = T + '/R14_COMMON.md'
LED = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = ROOT + '/lead/LEAD_LOCK'
BRD = T + '/STATUS_BOARD.md'
BAKDIR = T + '/R17_LEAD_BASELINE'

RC_PATCH = """**【R169 补记·三件第一段漏记的事实与一处更正】** ① **`0x7d0cba` 落真指令这一条换了判据才成立，口径必须同引**：线性解码口径下仍是 0/65；换成「360 张表的 2,325 个可解码槽值各自向下续解 64 条」得 145,636 条指令区间后命中 1 条，**反控**随机 65,536 个地址基线 3.159%。两数并列、不得只写其中一个。② **C16 下界随本节重钉**：本节实测 **8,025 B** ⇒ `C16_FLOORS` 新增 `174: 4012`，逐节表 **167 → 168 节**，`C16_FLOORS_SHA256` `ea00839e…` → **`dc5e162a…`**；**反控**：旧表重算命中旧常量、原有 167 条逐条不变、`GATE_VER` 与 `C7/C14/FREEZE` 三个 sha 一字未动（本轮没改 `DISC_RECHECK` / `DISC_UNVERIFIABLE` 任何一行），门禁 NOTE 逐字 `168 sections measured (pinned 168), unpinned 0`。③ **`FACT_INDEX_CURRENT.md` 指针已连续两轮未更新**（R168 升 V548 时漏改，仍指 V547 / `919263cf` / 109,220 B），本轮改正为 **V549 / `f1d32127` / 117,545 B / 声明轮次 R169 / 历史区间 V530..V549（20 份）**；**反控**：V548 仍在盘且 sha 未变（指针升级不删历史版本）、旧 sha 与旧字节数与旧版本目录三者全不残留、V547 只留在「补一个 V547 草稿就会指错」这句举例里。④ **更正**：第一段写「看板 236 行 < 260，本轮不归档」是错的 —— 写入第 169 轮后是 **263 行 >= 260**，归档条件**已触发**并按纪律执行（搬走最早 2 段到 `BOARD_ARCHIVE`，263 → **166 行**，归档 CR 保持 **2952**、看板 CR 保持 **0**，搬走 13,942 B 逐字出现在归档里）；**自错 S-564** 已登记。⑤ **三段实跑**：`check_disc` exit 0 / FAIL 0（`C16 per-section floors: 168 sections measured (pinned 168), hollow/deficient 0, missing 0, unpinned 0`）、`facts_floors` exit 0（`D0 sha=f1d32127 pinned=f1d32127` / `D9 master pin: 2fa2eb2fd66cdf70` / `D8 total bytes: 117545`）、`gate_runner` **G1=ok / G2=ok / G3=ok**（G3a…G3f 六条逐值相等）。**gate_runner 曾真红一次**：`r169i` 只把 `V548` 字样换成 `V549`，**没换目录号 `R17_R120` → `R17_R121`**，`G3c` 直接 `FileNotFoundError`（已备份回滚无关，属原地修补 + `py_compile` + 复跑，**自错 S-565** 已登记）。"""

LED_PATCH = """**【R169 补记】** ① `0x7d0cba` 落真指令「1 条」与线性口径「0/65」**两口径必须同引**（反控随机 65,536 地址基线 **3.159%**）。② **C16 下界重钉**：§2.174 实测 **8,025 B** ⇒ 新增 `174: 4012`、逐节表 **167 → 168 节**、`C16_FLOORS_SHA256` `ea00839e…` → **`dc5e162a…`**；反控：旧表重算命中旧常量、原有 167 条逐条不变、`GATE_VER`/`C7`/`C14`/`FREEZE` 四者一字未动。③ **`FACT_INDEX_CURRENT.md` 指针连续两轮未更新**（R168 漏改），本轮改指 **V549 / `f1d32127` / 117,545 B / R169 / V530..V549（20 份）**；反控 V548 仍在盘未变。④ **更正**：第一段「236 行 < 260 不归档」是错的，写入后 **263 >= 260** 已触发归档（263 → **166 行**，归档 CR 2952、看板 CR 0），**S-564** 登记。⑤ **三段实跑**：`check_disc` exit 0 / `facts_floors` exit 0 / `gate_runner` **G1=G2=G3=ok**；`gate_runner` 曾因只换 `V549` 未换目录号 `R17_R120→R17_R121` 而 `FileNotFoundError` 真红一次，修后复跑通过（**S-565**）。"""

LOCK_PATCH = """
OZ10. 🔴 **补记与更正（同一轮第二段，四件事）.** ① **`0x7d0cba` 的「1 条」必须与「线性口径 0/65」同引** —— 换种子后命中 1 条，反控随机 65,536 个 `.text` 地址基线 **2,070 = 3.159%**，两数并列、不得只写一个。② **C16 下界随 §2.174 重钉**：本节实测 **8,025 B** ⇒ 新增 `174: 4012`、逐节表 **167 → 168 节**、`C16_FLOORS_SHA256` `ea00839e…` → **`dc5e162a…`**；反控四条：旧表重算命中旧常量、原有 167 条逐条不变、`GATE_VER` 未动（仍 `R166`）、`C7_TEXT_SHA256`／`C14_TEXT_SHA256`／`FREEZE_SHA256` 三者一字未动。③ **`FACT_INDEX_CURRENT.md` 指针连续两轮未更新**（R168 升 V548 时漏改，仍指 V547 / `919263cf` / 109,220 B）⇒ 本轮改正为 **V549 / `f1d32127` / 117,545 B / 声明轮次 R169 / 历史区间 V530..V549（20 份）**；反控：V548 仍在盘且 sha 未变、旧 sha/旧字节/旧目录三者全不残留、`V547` 只保留在「补一个 V547 草稿就会静默指错」这句举例里（该句是说明用，**不该删**）。④ **更正 OZ9 的一句错话**：OZ9 写「236 行 < 260，本轮不归档」是**按写入前的行数**算的；写入第 169 轮后是 **263 行 >= 260**，归档条件**已触发**并已执行 —— 搬走**最早 2 段**（看板最新段在最上，故「最早」在末尾）13,942 B 到 `BOARD_ARCHIVE`，看板 **263 → 166 行**，归档 **CR 保持 2952**、看板 **CR 保持 0**，搬走内容逐字出现在归档里。**自错 S-564**：把「归档阈值」按写入前计数判、且写进了四件套正文。⑤ **反控**：归档首版把「最新两段」搬走了（因为看板是前插、最新在最上），`L5` 断言当场 FAIL，已从 `.bak` 回滚后改成搬末尾两段 —— 这一条也归 **S-564**。**S-565**：`r169i` 只把 `V548` 换成 `V549`、**没换目录号 `R17_R120` → `R17_R121`** ⇒ `gate_runner` G3c `FileNotFoundError` **真红**，原地修补（备份 wx + `py_compile` + 复跑）后 G1=G2=G3=ok。

OZ11. 📌 **本轮最终状态（以磁盘为准）.** 四件套 CR：`R14_COMMON` **1081** / 台账 **337** / 本文件 **137** / 看板 **0** / 归档 **2952**，五项全等。看板 **166 行**（6 段）。FACT_INDEX **V549**：**117,545 B / 55 行 / 5 列 / `f1d3212715a23d9d…` / CR 0**。三段实跑：`check_disc` exit 0 / FAIL 0（C16 **168 节 pinned 168**、unpinned 0、hollow 0）、`facts_floors` exit 0（D0 `f1d32127` / D8 117,545 / D9 `2fa2eb2f`）、`gate_runner` **G1=ok / G2=ok / G3=ok**（G3a…G3f 全 PASS）。
"""

BOARD_PATCH = """
**补记（同轮第二段）**：① `0x7d0cba` 的「1 条」与线性口径「0/65」**必须同引**（反控随机 65,536 地址基线 **3.159%**）；② **C16 重钉**：§2.174 实测 **8,025 B** ⇒ 新增 `174: 4012`、逐节表 **167 → 168 节**、`C16_FLOORS_SHA256` `ea00839e…` → **`dc5e162a…`**（反控：旧表命中旧常量、原 167 条不变、`GATE_VER`/`C7`/`C14`/`FREEZE` 一字未动）；③ **`FACT_INDEX_CURRENT.md` 指针连续两轮未更新**（R168 漏改，仍指 V547），本轮改指 **V549 / `f1d32127` / 117,545 B / R169 / V530..V549（20 份）**；④ **更正**上文「236 行 < 260 不归档」：写入后 **263 >= 260** 已触发归档，搬走最早 2 段后 **263 → 166 行**（归档 CR 2952 / 看板 CR 0 均保持）；⑤ **三段实跑**：`check_disc` exit 0 / `facts_floors` exit 0 / `gate_runner` **G1=G2=G3=ok**——`gate_runner` 曾因只换版本字样未换目录号 `R17_R120→R17_R121` 而 `FileNotFoundError` **真红一次**，修后复跑通过（**S-565**）。
"""

def sha(b): return hashlib.sha256(b).hexdigest()

expect = {RC: (1081, 1486430), LED: (337, 5254005), LOCK: (137, 1165241), BRD: (0, 37021)}
cur = {}
for p in (RC, LED, LOCK, BRD):
    b = open(p, 'rb').read()
    cur[p] = {'sha': sha(b), 'bytes': len(b), 'cr': b.count(b'\r')}
    assert cur[p]['cr'] == expect[p][0], (p, cur[p]['cr'])
print('pre-state:', json.dumps({os.path.basename(k): v for k, v in cur.items()}, ensure_ascii=False))

def write_append(path, payload, tag, prepend=False):
    old = open(path, 'rb').read()
    dst = os.path.join(BAKDIR, os.path.basename(path) + '.before_r169_' + tag + '.bak')
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(old)
    assert sha(open(dst, 'rb').read()) == sha(old)
    new = (payload.encode('utf-8') + old) if prepend else (old + payload.encode('utf-8'))
    assert new.count(b'\r') == old.count(b'\r')
    with open(path, 'wb') as f:
        f.write(new)
    assert open(path, 'rb').read() == new
    return dst

# R14_COMMON：§2.174 段是文件末尾，直接追加到段尾（属于该节的补记）
write_append(RC, '\n' + RC_PATCH + '\n', 'R14_COMMON_PATCH')
write_append(LED, '\n' + LED_PATCH + '\n', 'LEDGER_PATCH')
write_append(LOCK, LOCK_PATCH, 'LEAD_LOCK_OZ10')
# 看板：第 169 轮段在最上，补记要插在该段末尾（即第 168 轮段标题之前）
brd = open(BRD, 'rb').read().decode('utf-8')
marker = '\n## 🟢 R17 第 168 轮'
assert marker in brd
head, tail = brd.split(marker, 1)
new_brd = head.rstrip('\n') + '\n' + BOARD_PATCH + marker + tail
old_brd = open(BRD, 'rb').read()
dst = os.path.join(BAKDIR, 'STATUS_BOARD.md.before_r169_PATCH.bak')
fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(old_brd)
assert sha(open(dst, 'rb').read()) == sha(old_brd)
nb = new_brd.encode('utf-8')
assert nb.count(b'\r') == 0
open(BRD, 'wb').write(nb)
assert open(BRD, 'rb').read() == nb

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

post = {}
for p in (RC, LED, LOCK, BRD):
    b = open(p, 'rb').read()
    post[p] = {'cr': b.count(b'\r'), 'bytes': len(b), 'lines': b.count(b'\n')}
chk('P1 四项 CR 与写前逐项相同（1081/337/137/0）',
    post[RC]['cr'] == 1081 and post[LED]['cr'] == 337 and post[LOCK]['cr'] == 137 and post[BRD]['cr'] == 0,
    {os.path.basename(k): v['cr'] for k, v in post.items()})
chk('P2 归档 CR 仍 2952', open(T + '/BOARD_ARCHIVE.md', 'rb').read().count(b'\r') == 2952,
    open(T + '/BOARD_ARCHIVE.md', 'rb').read().count(b'\r'))
chk('P3 看板行数仍 <= 300', post[BRD]['lines'] <= 300, post[BRD]['lines'])
chk('P4 看板首行仍是第 169 轮',
    open(BRD, encoding='utf-8').read().split('\n')[0].startswith('## 🟢 R17 第 169 轮'),
    open(BRD, encoding='utf-8').read().split('\n')[0][:40])
chk('P5 「S-564」与「S-565」已登记（自错不漏记）',
    'S-564' in open(LOCK, encoding='utf-8').read() and 'S-565' in open(LOCK, encoding='utf-8').read(), 'ok')
chk('P6 四件套都含 C16 重钉的新 sha dc5e162a',
    all('dc5e162a' in open(p, encoding='utf-8').read() for p in (RC, LED, LOCK, BRD)), 'ok')
chk('P7 §2.174 / §1224 / OZ 段各仍恰一处',
    open(RC, encoding='utf-8').read().count('## 2.174') == 1
    and open(LED, encoding='utf-8').read().count('## §1224') == 1
    and open(LOCK, encoding='utf-8').read().count('## OZ ·') == 1, 'ok')

out = {'post': {os.path.basename(k): v for k, v in post.items()},
       'sha': {os.path.basename(k): sha(open(k, 'rb').read()) for k in (RC, LED, LOCK, BRD)},
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169p_patch.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
