#!/usr/bin/env python
"""裁决 6 · 指纹 JSON 隐私脱敏（保留哈希，不破坏可复现性）。

★ 背景
  v7 裁决 6：指纹 JSON 的 `computer_name`、用户目录等身份字段，写入前脱敏
  （保留哈希），已提交件追加脱敏版。

★ 脱敏原则
  - **保留判别力**：同一台机器两次采集仍得到同一个哈希 ⇒ 仍可做会话对照；
  - **去掉可识别性**：原始字符串不可还原（用 sha256 前缀，不加盐不可逆）；
  - **不破坏结构**：只替换值，不改键名/层级；
  - **留痕**：每个被替换的键写进 `_redactions` 列表。

★ 脱敏字段（白名单，不猜）
  host.computer_name              主机名
  session.computer_system.model   机型（可唯一定位到一台机器）
  system.cpu.name                 CPU 型号（弱标识，但配合机型可唯一定位）
  system.collector.path           采集器路径（含用户名/仓库绝对路径）

★ 用法
  python _redact_fingerprint.py <in.json> [--out <out.json>]
  python _redact_fingerprint.py --check <in.json>    # 只检查是否已脱敏
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# ★ 脱敏白名单：点分路径。只处理这些，不猜别的。
REDACT_PATHS = [
    "host.computer_name",
    "session.computer_system.model",
    "system.cpu.name",
    "system.collector.path",
]

MARK = "sha256:"


def digest(s: str) -> str:
    """不可逆摘要。★ 不加盐 ⇒ 同机同值 ⇒ 跨会话仍可配对。"""
    return MARK + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def get_path(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def set_path(obj, dotted, value):
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        cur = cur[part]
    cur[parts[-1]] = value


def is_redacted(v) -> bool:
    return isinstance(v, str) and v.startswith(MARK)


def redact(obj) -> list:
    done = []
    for p in REDACT_PATHS:
        v, ok = get_path(obj, p)
        if not ok:
            continue
        if is_redacted(v):
            done.append({"path": p, "status": "already_redacted",
                         "value": v})
            continue
        if not isinstance(v, str):
            continue
        newv = digest(v)
        set_path(obj, p, newv)
        done.append({"path": p, "status": "redacted",
                     "value": newv, "orig_len": len(v)})
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="_redact_fingerprint.py")
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true",
                    help="只检查是否已脱敏，不写盘")
    args = ap.parse_args(argv)

    src = Path(args.src)
    if not src.is_file():
        print("!! 文件不存在:", src)
        return 2
    raw = src.read_bytes()
    obj = json.loads(raw.decode("utf-8"))

    if args.check:
        leaked = []
        for p in REDACT_PATHS:
            v, ok = get_path(obj, p)
            if ok and isinstance(v, str) and not is_redacted(v):
                leaked.append((p, v))
        print("检查:", src)
        for p, v in leaked:
            print("  未脱敏  %-34s = %r" % (p, v))
        if not leaked:
            print("  ✅ 全部已脱敏")
            return 0
        return 1

    done = redact(obj)
    # 追加留痕（不改已有键的语义）
    meta = obj.setdefault("_redactions", [])
    if isinstance(meta, list):
        meta.extend(done)

    out = Path(args.out) if args.out else src.with_name(
        src.stem + "_redacted.json")
    text = json.dumps(obj, ensure_ascii=False, indent=1)
    out.write_text(text, encoding="utf-8")

    print("脱敏:", src, "->", out)
    for d in done:
        print("  %-34s %s" % (d["path"], d["status"]))
    print()
    print("原 %d B -> 新 %d B" % (len(raw), len(text.encode("utf-8"))))
    print("新件 sha256 =", hashlib.sha256(
        text.encode("utf-8")).hexdigest()[:16])

    # ★ 自检：脱敏后必须再也读不到原值
    leak = []
    for p in REDACT_PATHS:
        v, ok = get_path(obj, p)
        if ok and isinstance(v, str) and not is_redacted(v):
            leak.append(p)
    if leak:
        print("!! 自检失败，仍可识别:", leak)
        return 1
    print("自检：全部身份字段已不可识别  PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
