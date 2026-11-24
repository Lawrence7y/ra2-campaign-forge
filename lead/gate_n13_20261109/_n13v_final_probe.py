# -*- coding: utf-8 -*-
r"""_n13v_final_probe.py — 最终复核探针：无歧义 D 类负样本 + 四条问题 DB 查证 + 收尾

  PART 1：5 条「主语 + 完成词」的 D 类真断言（每条单独跑均 FAIL，不是靠动作词触发），
          看撰写人谓词能否抓住；另附 3 条对照。
  PART 2：只读查 CLI 会话库，找「四条问题」的门禁输出是否可枚举。
  PART 3：收尾指纹 + git log + 写域清单。
"""
import hashlib
import importlib.util
import pathlib
import re
import sqlite3
import subprocess

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_n13_20261109"


def _load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


n13 = _load(WD / "_n13_predicates.py", "_n13v_final_n13")
g7 = _load(ROOT / "lead/gate_fp7_20261108/_g7_predicates.py", "_n13v_final_g7")
T = list(n13.DEFAULT_TOKENS)


def judge(t):
    p, det = n13.r13_assertions(t, T, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    return len(p) > 0, p, det


def main():
    print("=" * 78)
    print("PART 1 无歧义 D 类真断言（每条单独跑均 FAIL，见 BASELINE 列）")
    print("=" * 78)
    # BASE = 同一条断言不带任何 A/B/C 语境标记时的判定（应当 FAIL）
    FINAL5 = [
        ("V1", "未验：本笔已入账", "本笔已入账"),
        ("V2", "grep 结果：第 5 笔已入账", "第 5 笔已入账"),
        ("V3", "§2 清单 / 此笔已入账 / §3 依赖", "此笔已入账"),
        ("V4", "未验：§605 已入账", "§605 已入账"),
        ("V5", "grep 结果：此笔已入账", "此笔已入账"),
    ]
    XTRA = [
        ("X1", "grep 结果：已入账", "已入账"),
        ("X2", "未验：第 605 节已入账", "第 605 节已入账"),
        ("X3", "已入账核查清单：该条已追加", "该条已追加"),
    ]
    miss = []
    for cid, txt, base in FINAL5 + XTRA:
        b_fail, _, _ = judge(base)
        f_fail, probs, det = judge(txt)
        if not f_fail:
            miss.append(cid)
        print("%-4s BASE=%-4s 语境化=%-4s %s | %s" %
              (cid, "FAIL" if b_fail else "PASS", "FAIL" if f_fail else "★PASS",
               "漏网" if (b_fail and not f_fail) else "OK", repr(txt)))
        print("     BASE 文本:", repr(base), "| 语境化明细:",
              [(d["kind"], d["rule"][:44]) for d in det])
    print()
    print("PART 1 正式 5 条漏网 =", [c for c in miss if c in ("V1", "V2", "V3", "V4", "V5")])
    print("PART 1 全部漏网 =", miss)

    print()
    print("=" * 78)
    print("PART 2 只读查 CLI 会话库：四条问题的门禁输出")
    print("=" * 78)
    db = r"C:/Users/Administrator/.zcode/cli/db/db.sqlite"
    con = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute("select rowid,data from part where rowid in (613246,613929)")
    for rid, data in cur.fetchall():
        s = data.replace("\\n", "\n")
        i = max(s.find("门禁问题"), s.find("门禁 FAIL"))
        print("  rowid", rid, "|", repr(s[i:i + 120]))
    # 任何含 4 条 problems 的 JSON 输出
    cur.execute("select rowid,data from part where data like ?", ('%含越权断言%',))
    four = []
    pat = re.compile(r'"problems"\s*:\s*\[([^]]{10,900})\]')
    for rid, data in cur.fetchall():
        for m in pat.finditer(data):
            items = re.findall(r'"([^"]{4,90})"', m.group(1))
            if len(items) >= 4 and any("已入账" in x for x in items):
                four.append((rid, items))
    print("  part 表内 >=4 条 problems 且含「已入账」的 JSON =", len(four))
    for rid, items in four[:5]:
        print("   ", rid, items)
    # 明确写「四条问题」但给出枚举的
    cur.execute("select rowid,data from part where data like ?", ('%四条问题里两条%',))
    print("  含「四条问题里两条」背景语的 part 行数 =", cur.rowcount)
    con.close()

    print()
    print("=" * 78)
    print("PART 3 收尾：只读件指纹 / git log / 写域")
    print("=" * 78)
    EXPECT = [
        ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", "47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70", 70587),
        ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", "7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43", 60272),
        ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
        ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
        ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
        ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ]
    for rel, sha, size in EXPECT:
        b = (ROOT / rel).read_bytes()
        print("  %-58s %s %d %s" % (rel, hashlib.sha256(b).hexdigest()[:12], len(b),
              "OK" if (hashlib.sha256(b).hexdigest() == sha and len(b) == size) else "MISMATCH"))
    print("  r9r12/_g9_gate.py exists =", (ROOT / "lead/r9r12_20261109/_g9_gate.py").exists())
    r = subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=str(ROOT),
                       capture_output=True, text=True)
    print("  git log -1 =", r.stdout.strip())
    print("  write domain 非 _n13/_n13v 前缀文件 =",
          [f.name for f in WD.iterdir() if f.is_file()
           and not (f.name.startswith("_n13_") or f.name.startswith("_n13v_")
                    or f.name == "GATE_N13_QUOTED_ASSERTION.md")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
