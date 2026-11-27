#!/usr/bin/env python3
"""R144 U：把门禁回归与 S-312..S-315 追加进 LEAD_LOCK（OC13/OC14），CR 保持 137。"""
import hashlib, io, json, os, time
LK = '/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
BL = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

ADD = """OC13. ✅ **门禁回归（本轮五处改动，全部为容纳新节 + 同步 + 重钉，未改任何判据语义）。** ① `C16_FLOORS` 加 `149: 9026`（§2.149 实测 **9,047 B** − 21，与 146/147/148 同法），表项 **142 → 143**，`C16_FLOORS_SHA256` `f1ee8188…` → **`05b54f35…`**（`r144q`，**16 正控 0 FAIL**：**重钉前先用现表重算复现旧钉 `f1ee8188`**，验明方法无误）；② `GATE_VER` **R143 → R144**；③ `DISC_RECHECK.tsv` **第 21 行（纪律号 20）** 登记串同步 → C7d `25e8096c…` → **`636db13b…`**、`C7_ROW_SHA['20']` 同步；④ `DISC_UNVERIFIABLE.tsv` **第 11 行（纪律号 20）** 同步 → `FREEZE_SHA256` `cc4a7c5f…` → **`c49e2582…`**。**注意两处主键同为 20 而行号不同（21 与 11）** —— R143 S-299 就是在这个坑里摔的，本轮先打印目标行再断言（`r144r` C4/C9/C10 三条）。

OC14. 🔴 **自错 S-312（本轮唯一一次门禁真 FAIL，已修）：C7d 指纹把表头行一起算了。** 门禁的口径是 `rows = [l.split('\\t') for l in raw[1:]]`（**丢表头**，31 行），我在 `r144r` 里写成「所有非空行」⇒ **32 行** ⇒ 算出的新钉 `8c35cff4` 是**含表头**的指纹，门禁按 31 行算出 `636db13b` ⇒ **C7d FAIL**。`r144s` 修：照抄门禁口径重算 → `636db13b`，并加一条反控证明差异**只是表头那一行**（把表头塞回去重算恰得我写错的 `8c35cff4`）。**教训与 S-299 同族但不同轴：S-299 是「行号 vs 主键」，S-312 是「行集口径（含不含表头）」。凡是要与门禁比指纹，必须先读门禁怎么取行。**

OC15. 📌 **另两条自错与一条脚本设计缺陷（S-313/S-314/S-315）。** **S-313**：`r144r` 的沙箱只软链了 `ra2bench/_r143/_r144` 三个顶层目录，而门禁 C7 的 id 31 产物在 **`_r94\\falsify_r94.py`** ⇒ 沙箱基线报 **3 条 FILE_MISSING**（id 31 的 C7 / C11，加 C18 vacuity 计数漂移 18≠19），P0/P1 双双 FAIL；改为软链 ROOT 下**全部**顶层目录后 P0/P1 通过。**S-314**：`r144s` 是**一次性脚本**（把错钉换成对钉），第二次跑时 R0/R5/R6/R9 必然 FAIL —— 我第一次重跑就撞上，差点误读成「修复未生效」。**处置：另写幂等的 `r144t_verify.py` 只核终态（26 项 0 FAIL），并在卡面写明 `r144s` 一次性**。**S-315**：`r144t` 里写了一条 `'S-312' in led.decode() or True` 的**恒真断言**（第 6 次同形状，历史 S-244/S-249/S-254 同族），当场删掉不留。另：反控 N2 的期望值我一开始写「点名 id 19」，实测门禁报的是 `drifted ids=['19']` —— 方向对，但**这条只有在我不去猜而是先跑一遍才写得准**。

OC16. ✅ **终态（`r144t_verify.py`，26 项 0 FAIL）**：`check_disc.py` **exit 0**、C10 **ok(R144)**、C7 **31/31**、C7d **`636db13b`**、C11 OK（frozen 12）、C15 **143 节 / 末节 149**、C16 **pinned 143 / unpinned 0 / hollow 0 / missing 0 / min margin 21**、C16d **`05b54f35`**、C18 note 在场。五项 CR **1081 / 337 / 137 / 0 / 2952** 全绿（R14_COMMON 1,230,326 → 1,239,373 B、台账 5,102,346 → 5,106,633 B、LEAD_LOCK 955,991 → 973,070 B，CR 全不变；看板 **216 行 < 300**，本轮无需归档）。三份 `.bak` 与四份门禁 `.bak` 全部 `wx` 独占创建并回读校验。全程 `disasm_lite` 64 KB 流式，未对整段 `.text` 开 `detail=True`；脚本均带 timeout；收口前 `ps` 确认无孤儿。
"""
b = ADD.encode('utf-8')
ck('追加段不含 CR', b'\r' not in b)
ck('追加段含 OC13..OC16', all(('OC%d.' % i).encode() in b for i in range(13, 17)))
old = open(LK, 'rb').read()
ck('LK 旧 CR == 137', old.count(b'\r') == 137, old.count(b'\r'))
ck('LK 尾部是换行', old.endswith(b'\n'))
dst = os.path.join(BL, 'LEAD_LOCK.before_r144_lockadd_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(old)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == old, os.path.basename(dst))
open(LK, 'wb').write(old + b)
new = open(LK, 'rb').read()
ck('LK 写后 CR 仍 137', new.count(b'\r') == 137, new.count(b'\r'))
ck('LK 写后以原文件为前缀', new[:len(old)] == old)
ck('LK 写后 OC16 在场', b'OC16.' in new)
json.dump({'fails': cc}, io.open('/home/t628/projects/ra2-campaign-forge/_r144/r144u_lockadd.json', 'w'), indent=1)
print('\n=== 锁追加：FAIL %d ===' % len(cc))
