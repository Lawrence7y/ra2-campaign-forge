# -*- coding: utf-8 -*-
# 加出口模板对照件：模板逐字取自 lead/exit_criterion_20261110/EXIT_CRITERION.md:520-530
# 用法：python -I -X utf8 _gr_template_ctl.py <fail_index>
#   fail_index = -1 全部通过；1/2/3 = 令第 N 项检查（1-based）失败
import sys

ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)                                   # E2：And 聚合，全部检查通过才置真
    print(("  [PASS] " if cond else "  [FAIL] ") + name)     # E4：同一 cond 驱动摘要与聚合

fail_index = int(sys.argv[1])
# 三行检查：每项只有一份 cond，既驱动 check() 内的聚合，又驱动 check() 内的 PASS/FAIL 打印
check("C1 2 + 3 == 5", 2 + 3 == (6 if fail_index == 1 else 5))
check("C2 7 * 6 == 42", 7 * 6 == (43 if fail_index == 2 else 42))
check("C3 100 - 58 == 42", 100 - 58 == (41 if fail_index == 3 else 42))
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))          # E4：同源总结
raise SystemExit(0 if ok else 1)                             # E1：动态状态 {0,1}
