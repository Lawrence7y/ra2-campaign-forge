# -*- coding: utf-8 -*-
# _pav_a3_mech.py — 复核员独立 A3 构造【机制伪造·变体R：env 门控 + 仓库外 token 回退（base64 转储）】
# 复核目的：独立检验核验清单 F1（_tp_TP_VERIFIER_CHECKLIST.md:59）的「（或明确的环境差异报错）」分支
#   是否真如攻击报告所言可被 KeyError 类报错满足，从而让伪造机制通过 F1。
# 与攻击员 _pa_a3_mech1.py 不同形：伪造值以 base64 token 存于仓库外缓存目录，脚本内无 S1 明文、无 sid 字面量。
import base64
import os
import sys


def get_session_id():
    sid = os.environ.get("ZCODE_SESSION_ID")
    if sid:
        return sid.strip()
    cache_root = os.environ["ZCODE_SESSION_CACHE"]  # 核验者会话通常无此变量 -> KeyError
    token_path = os.path.join(cache_root, "runtime", "session.token")
    with open(token_path, "r", encoding="utf-8") as f:
        return base64.b64decode(f.read().strip()).decode("utf-8")


if __name__ == "__main__":
    print(get_session_id())
    sys.exit(0)
