"""恢复台账 14948–15033 行的 CRLF 行尾（§403 轮误转成 LF）。

## 为什么要修

2026-10-24 §403 轮的 heredoc 追加，把文件里**唯一**的 86 处 CRLF
（§399 整节，行 14948–15033，1-based）转成了 LF。
证据：`git show HEAD~1` 的 CRLF 计数 = 86，`git show HEAD` = 0。

## 怎么修

不重写全文（那会再污染一次）。做法：
  1. 以 `git show HEAD:...` 的当前内容为基础（它已是 LF）；
  2. **只**给该 86 行范围重新加回 `\r`；
  3. 逐字节比对：修复后的内容必须满足
     - 与 HEAD~1 的前缀（截至 14947 行末）逐字节相同
     - 14948–15033 行的 CR 状态与 HEAD~1 一致
     - 15034 行之后（本轮新追加的 §400–403）与 HEAD 逐字节相同

★ 之所以用「按行号区间」而不是「全局替换」：该文件行尾**本来就是混杂的**
  （15,096 bare-LF + 86 CRLF），全局规范化会改掉本不该动的行。
  [[crlf-diff-roundtrip-traps]] 记的就是这一类坑。
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
REL = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
TARGET = REPO / REL


def git_show(ref):
    r = subprocess.run(["git", "show", f"{ref}:{REL}"], cwd=REPO,
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit("git show %s 失败: %s" % (ref, r.stderr[:300]))
    return r.stdout


def main():
    old = git_show("HEAD~1")
    new = git_show("HEAD")

    old_lines = old.split(b"\n")
    new_lines = new.split(b"\n")
    crlf_rows = [i for i, ln in enumerate(old_lines) if ln.endswith(b"\r")]
    if not crlf_rows:
        print("HEAD~1 里没有 CRLF —— 无事可做")
        return 0
    lo, hi = min(crlf_rows), max(crlf_rows)
    print("HEAD~1 的 CRLF 行（0-based）: %d … %d，共 %d 行"
          % (lo, hi, len(crlf_rows)))

    # 当前文件状态检查
    cur_crlf = sum(1 for ln in new_lines if ln.endswith(b"\r"))
    print("HEAD 的 CRLF 行数: %d" % cur_crlf)

    # 只恢复 [lo, hi] 区间内、且在 old 里带 CR 的行
    want_cr = set(crlf_rows)
    out = []
    n_fixed = 0
    for i, ln in enumerate(new_lines):
        if i in want_cr and not ln.endswith(b"\r"):
            out.append(ln + b"\r")
            n_fixed += 1
        else:
            out.append(ln)
    fixed = b"\n".join(out)
    print("恢复 %d 行的 CR" % n_fixed)

    # ---- 自检 ----
    ok = True
    # 1) 前缀逐字节（截至 lo 行之前）
    prefix_old = b"\n".join(old_lines[:lo]) + (b"\n" if lo else b"")
    prefix_new = b"\n".join(out[:lo]) + (b"\n" if lo else b"")
    same_prefix = prefix_old == prefix_new
    ok &= same_prefix
    print("[%s] 前缀（0..%d 行）与 HEAD~1 逐字节相同"
          % ("PASS" if same_prefix else "FAIL", lo - 1))
    # 2) 区间内 CR 状态一致
    bad = [i for i in want_cr if not out[i].endswith(b"\r")]
    ok &= not bad
    print("[%s] 区间内 %d 行全部恢复 CR（异常 %d 行）"
          % ("PASS" if not bad else "FAIL", len(want_cr), len(bad)))
    # 3) lo..hi 段的**内容**（去 CR）与 old 相同
    old_seg = [ln.rstrip(b"\r") for ln in old_lines[lo:hi + 1]]
    new_seg = [ln.rstrip(b"\r") for ln in out[lo:hi + 1]]
    seg_same = old_seg == new_seg
    ok &= seg_same
    print("[%s] 区间内容（忽略 CR）与 HEAD~1 相同"
          % ("PASS" if seg_same else "FAIL"))
    # 4) HEAD 里 hi 之后的内容：从 HEAD 中按「第 hi+1 行起始字节」截取，
    #    ★ 不能拿 out[hi+1:] 跟它比 —— 加 CR 会让 split 索引错位。
    #    正确做法：在 HEAD 里量出「前 hi+1 行」的字节长度，取其后缀。
    head_prefix_len = len(b"\n".join(new_lines[:hi + 1])) + 1
    tail_head = new[head_prefix_len:]
    # 修复后在末尾追加同样的后缀（它不含 CR，因为 HEAD 全 LF）
    tail_fixed = fixed[len(fixed) - len(tail_head):] if tail_head else b""
    tail_same = tail_head == tail_fixed
    ok &= tail_same
    print("[%s] 第 %d 行之后（本轮追加的 §400–403）与 HEAD 逐字节相同"
          % ("PASS" if tail_same else "FAIL", hi + 1))
    # 5) 总 CRLF 数回到 86
    total_crlf = sum(1 for ln in out if ln.endswith(b"\r"))
    ok &= (total_crlf == len(crlf_rows))
    print("[%s] 总 CRLF = %d（期望 %d）"
          % ("PASS" if total_crlf == len(crlf_rows) else "FAIL",
             total_crlf, len(crlf_rows)))

    if not ok:
        print("\n!! 自检未全过 —— 不写盘")
        return 1

    if "--write" not in sys.argv:
        print("\n（--check 模式，未写盘；加 --write 才落盘）")
        return 0
    TARGET.write_bytes(fixed)
    print("\n已写回 %s（%d B）" % (TARGET.name, len(fixed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
