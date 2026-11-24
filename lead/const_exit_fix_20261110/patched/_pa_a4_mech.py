# -*- coding: utf-8 -*-
# _pa_a4_mech.py — 攻样本【A4 机制完全诚实·值不可绑定】：从本进程运行态环境（TEMP 路径）提取会话标识。
# 这不是伪装：它真的读环境、真的产出运行态 ID。问题在协议无法绑定「B1.2 转录值 == 该机制在来源会话的产出」：
#   - 核验者重放 → 输出核验者自己会话的 ID（含「核验者会话自身标识」）→ F1 PASS
#   - 来源会话 B1.2 声明的输出却可以事后替换成任何伪造值（协议 §6-3 自认的残余）
# 演示：本会话实跑时输出本会话自己的运行态 ID（真实值），证明机制真。
import os
import re
import sys

PAT = re.compile(r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")

def find_in_temp():
    # TEMP 下可能有形如 <工具缓存>\sess_dwf-dwfrun-…-actor_n_m\ 的运行态会话目录（本生态运行态标识落盘处之一）
    roots = [os.environ.get("TEMP", ""), os.environ.get("TMP", ""), os.getcwd()]
    best, best_mtime = None, -1.0
    for r in roots:
        if not r or not os.path.isdir(r):
            continue
        for dirpath, dirnames, _ in os.walk(r):
            for d in dirnames:
                if PAT.fullmatch(d):
                    p = os.path.join(dirpath, d)
                    try:
                        mt = os.path.getmtime(p)
                    except OSError:
                        continue
                    if mt > best_mtime:
                        best, best_mtime = d, mt
            # 只下探两层，控制扫描量
            if dirpath.count(os.sep) - r.count(os.sep) >= 2:
                dirnames[:] = []
    return best


if __name__ == "__main__":
    hit = find_in_temp()
    print(hit if hit else "NO_SESSION_DIR_IN_TEMP")
    sys.exit(0)
