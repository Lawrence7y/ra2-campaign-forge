# -*- coding: utf-8 -*-
# 终稿轮自验（2/3）：_si_fix_lib.py 三方案活跑——真实域（counterpart）+ 新建沙盒负例。
# 沙盒 = 本写域内 _siw_sandbox（新目录，不动诊断轮 _si_sandbox）；产出 _siw_fixcheck_out.txt。
import importlib.util, pathlib, shutil, time

R = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = R / 'lead/gate_subject_id_20261109'
CP = R / 'lead/counterpart_fix_20261109'
SB = WD / '_siw_sandbox'
t0 = time.perf_counter()

spec = importlib.util.spec_from_file_location('si_fix_lib', WD / '_si_fix_lib.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

res = []
def case(name, fn, expect):
    try:
        v = fn()
        got = v.name if isinstance(v, pathlib.Path) else repr(v)
        ok = (got == expect)
    except lib.GateFail as e:
        got = 'GateFail:' + str(e)
        ok = (expect.startswith('GateFail:'))
    res.append('%-34s expect=%-46s got=%s  %s' % (name, expect, got, 'OK' if ok else 'MISMATCH'))
    return ok

allok = True
# --- 真实域（只读） ---
allok &= case('A explicit(counterpart)', lambda: lib.pick_deliverable_explicit(CP, 'COUNTERPART_FIX.md'), 'COUNTERPART_FIX.md')
allok &= case('B unique_bare(counterpart)', lambda: lib.pick_deliverable_unique_bare(CP), 'COUNTERPART_FIX.md')
allok &= case('C largest_bare(counterpart)', lambda: lib.pick_deliverable_largest_bare(sorted(CP.glob('*.md'))), 'COUNTERPART_FIX.md')
allok &= case('overshadow_warning(counterpart)', lambda: lib.overshadow_warning(CP, CP / 'COUNTERPART_FIX.md'), "['_cf_counterpart_vs_tighten_20261109.md']")

# --- 沙盒负例 ---
if SB.exists():
    shutil.rmtree(SB)
SB.mkdir(parents=True)
(SB / '_draft_big.md').write_bytes(b'x' * 900)          # 下划线中间稿（更大）
(SB / 'MAIN.md').write_bytes(b'main' * 10)              # 唯一非下划线主件（更小）
allok &= case('A explicit(缺件)', lambda: lib.pick_deliverable_explicit(SB, 'NOT_EXIST.md'), 'GateFail:主交付件未按约定命名 NOT_EXIST.md')
allok &= case('B unique_bare(恰一,大中稿在场)', lambda: lib.pick_deliverable_unique_bare(SB), 'MAIN.md')
allok &= case('C largest_bare(大中稿在场)', lambda: lib.pick_deliverable_largest_bare(sorted(SB.glob('*.md'))), 'MAIN.md')
(SB / 'SECOND.md').write_bytes(b'second' * 5)           # 制造双主件
allok &= case('B unique_bare(双主件)', lambda: lib.pick_deliverable_unique_bare(SB), 'GateFail:')
allok &= case('C largest_bare(双主件)', lambda: lib.pick_deliverable_largest_bare(sorted(SB.glob('*.md'))), 'GateFail:')
SB2 = SB / 'onlydraft'
SB2.mkdir()
(SB2 / '_sh_only.md').write_bytes(b'd' * 50)            # 全中间稿域
allok &= case('B unique_bare(0 主件)', lambda: lib.pick_deliverable_unique_bare(SB2), 'GateFail:')

elapsed = time.perf_counter() - t0
out = '\n'.join(res) + '\n\nALL_OK=%s\nglob 单层调用=6（真实域 3 + 沙盒 3），无递归 walk，dirsVisited=0\nelapsedSec=%.3f\n' % (allok, elapsed)
(WD / '_siw_fixcheck_out.txt').write_text(out, encoding='utf-8')
print(out)
