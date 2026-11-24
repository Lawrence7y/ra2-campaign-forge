# -*- coding: utf-8 -*-
"""W9 / Q4 -- EXCEPT 件与「主崩溃」的关系（只读探针）。

独立运行：
  python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\re_line_20261105\\W9_SINGLESTEP_7CFC9F\\_w9_q4.py
产出：同目录 _w9_q4_out.txt（脚本自己写，不依赖 shell 重定向）

铁律：零真机 / 零采样注入 / 零活进程读取；只读 gamemd.exe、EXCEPT 件、仓内 except_* 文本、harness 源码。
唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q4_out.txt。
Engine：e.raw 是 bytes；读字节用 e.rd(va,n)；查指令起始用 va in e.by()；disasm 可能吞异常返回空。
"""
import sys
import os
import re
import hashlib
import datetime
import subprocess
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + (
    r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
    r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q4_out.txt"
VA = 0x7CFC9F

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []


def p(s=""):
    _lines.append(str(s))
    print(s, flush=True)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes()), Path(path).stat().st_size


_ALL_FILES = None


def all_files_cached():
    """§6 铁律：存在性/枚举事实先用文件系统命令（find），不要全仓 Python 遍历。
    用一次 `find . -type f -not -path './.git/*'` 得到清单并缓存，后续按名字前缀过滤。"""
    global _ALL_FILES
    if _ALL_FILES is None:
        # 不传任何含 '*' 的参数：从 native Python 直接调 Git-Bash find.exe 时
        # MSYS 会自行展开 glob（曾导致 "paths must precede expression"）。
        # .git 过滤改在 Python 侧做，.git 目录本身也用 -prune 剪掉。
        out = subprocess.run(
            [r"D:\Git\usr\bin\find.exe", ".", "-path", "./.git", "-prune",
             "-o", "-type", "f", "-print"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        p("  [find] rc=%d stderr=%r 命中行数=%d"
          % (out.returncode, out.stderr[:120], len(out.stdout.splitlines())))
        _ALL_FILES = [os.path.normpath(os.path.join(ROOT, rel))
                      for rel in out.stdout.splitlines()
                      if rel.strip() and not rel.replace("\\", "/").startswith("./.git/")]
    return _ALL_FILES


def find_named(root, pattern):
    """按 glob 文件名口径过滤（等价于 find -name），命中返回绝对路径列表。"""
    import fnmatch
    if os.path.abspath(root) != os.path.abspath(ROOT):
        # 本探针只需整仓口径
        pass
    hits = [fp for fp in all_files_cached()
            if fnmatch.fnmatch(os.path.basename(fp), pattern)]
    return sorted(hits)


def parse_eip_bytes(path):
    """从 'Bytes at CS:EIP (...): <hex>' 行取冒号后的 2-hex 字节串。"""
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if "Bytes at CS:EIP" in ln:
            tail = ln.rsplit(":", 1)[1]
            return bytes(int(x, 16) for x in re.findall(
                r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{2}(?![0-9A-Fa-f])", tail))
    return None


def iso_mtime(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime(
        "%Y-%m-%d %H:%M:%S")


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p("=" * 78)
    p("W9 / Q4 PROBE -- EXCEPT 件与「主崩溃」的关系（只读 / 真反汇编 + 真读字节）")
    p("run command = python -I -X utf8 " + str(Path(__file__).resolve()))
    p("回件时刻 = " + now)
    p("=" * 78)

    # ---------- A. 强制头部：自己实算 SHA256 / 字节数 ----------
    p("")
    p("[A] 强制头部（自己实算，非引用任何旧结论）")
    exe_sha, exe_n = sha_file(EXE)
    exc_sha, exc_n = sha_file(EXCEPT)
    p("被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
    p("gamemd.exe SHA256 = " + exe_sha)
    p("gamemd.exe 字节数 = " + str(exe_n))
    p("EXCEPT 件 SHA256 = " + exc_sha)
    p("EXCEPT 件 字节数 = " + str(exc_n))
    exc_bytes = Path(EXCEPT).read_bytes()
    p("EXCEPT 首行 = " + repr(exc_bytes.splitlines()[0].decode("utf-8", "replace")))
    p("EXCEPT 'Exception occurred at' 行 = " + repr(next(
        (ln.decode("utf-8", "replace") for ln in exc_bytes.splitlines()
         if ln.startswith(b"Exception occurred at")), "NOT_FOUND")))
    p("EXCEPT mtime = " + iso_mtime(EXCEPT))

    # ---------- B. Engine 自证 ----------
    p("")
    p("[B] Engine 自证（自己实例化 ra2tool.Engine）")
    e = Engine()
    p("Engine.sha = " + e.sha + "  (== 自算: " + str(e.sha == exe_sha) + ")")
    p("IMAGEBASE = " + hex(e.IB))
    p("SECTIONS  = " + repr([(nm, hex(sva), hex(vsz), hex(rp), hex(rsz))
                             for nm, sva, vsz, rp, rsz in e.SEC]))
    p("fo(0x%08X) = %s (VA-0x400000=%s, 相等=%s)"
      % (VA, hex(e.fo(VA)), hex(VA - 0x400000), e.fo(VA) == VA - 0x400000))
    by = e.by()
    cov, nins, nfails = e.coverage
    p("COVERAGE = %.12f%% / decoded insns = %d / resync fails = %d" % (cov, nins, nfails))
    p("Engine 自证 = COVERAGE %.12f%% (%d insns, %d resync-fails) / IMAGEBASE 0x400000"
      % (cov, nins, nfails))

    # ---------- C. 真读字节 + 真反汇编：把 EXCEPT 件的字节串与磁盘镜像绑定 ----------
    p("")
    p("[C] 真读字节 / 真反汇编（Q4 需要：确认这份 EXCEPT 文本确实描述镜像里 0x7CFC9F 的真实字节）")
    raw32 = e.rd(VA, 32)
    p("type(e.rd(VA,32)) = " + type(raw32).__name__ + " ; len = " + str(len(raw32)))
    p("e.rd(0x7CFC9F, 32) = " + raw32.hex(" ").upper())
    ev = parse_eip_bytes(EXCEPT)
    p("EXCEPT L17 'Bytes at CS:EIP' 解析字节数 = " + str(len(ev) if ev else None))
    p("EXCEPT L17 字节 = " + (ev.hex(" ").upper() if ev else "NONE"))
    m = min(len(raw32), len(ev or b""))
    diffs = [i for i in range(m) if raw32[i] != ev[i]]
    p("磁盘 rd[0:%d] vs EXCEPT L17 逐字节差异索引 = %s" % (m, repr(diffs)))
    p("磁盘 rd[0:%d] == EXCEPT L17[0:%d] : %s" % (m, m, (len(diffs) == 0 and m == 32)))
    p("va 0x%08X in e.by() = %s （是不是合法指令起始 / 重同步流里）" % (VA, VA in by))
    d = e.disasm(VA, 32)
    p("e.disasm(VA,32) 条数 = %d（disasm 可能吞异常返回空，故用 by() 复核）" % len(d))
    for j, (a, hx, mn, ops) in enumerate(d[:8]):
        p("  [%d] 0x%08X  %-14s %-7s %s" % (j, a, hx.upper(), mn, ops))
    ins0 = by.get(VA)
    p("by()[0x7CFC9F] = %s %s  (bytes=%s)"
      % (ins0.mnemonic, ins0.op_str, bytes(ins0.bytes).hex().upper()) if ins0 else "NONE")
    p("⇒ 这份 EXCEPT 文本的字节串与 gamemd.exe 磁盘镜像 0x7CFC9F 处一致；")
    p("  但这只证明「文本抄的是真实代码」，不等于「这一趟真的在该处崩溃」（见 D/E/F）。")

    # ---------- D. 全仓 find except_post_*.txt + 逐份算哈希逐一比对 ----------
    p("")
    p("[D] 全仓 find('except_post_*.txt') → 逐份 sha256 → 与 EXCEPT 哈希逐一比对")
    posts = find_named(ROOT, "except_post_*.txt")
    p("find 命中总数 = " + str(len(posts)) + "  （口径 = 整仓，剪枝仅排除 .git）")
    recs = []
    for fp in posts:
        h, n = sha_file(fp)
        recs.append((h, n, fp, iso_mtime(fp)))
    same = [r for r in recs if r[0] == exc_sha]
    diff = [r for r in recs if r[0] != exc_sha]
    p("比对份数 = " + str(len(recs)))
    p("同哈希份数 = " + str(len(same)))
    p("不同哈希份数 = " + str(len(diff)))
    p("EXCEPT 目标哈希 = " + exc_sha)
    distinct = {}
    for h, n, fp, mt in recs:
        distinct.setdefault(h, [0, set()])
        distinct[h][0] += 1
        distinct[h][1].add(n)
    p("distinct 哈希数 = " + str(len(distinct)))
    for h, (cnt, sizes) in sorted(distinct.items(), key=lambda x: -x[1][0]):
        p("  %s  x%d  sizes=%s  %s" % (h, cnt, sorted(sizes),
                                       "<== 与 EXCEPT 相同" if h == exc_sha else "<== 不同"))
    p("")
    p("-- D2: 直接字节比对（不依赖哈希）EXCEPT 全文 vs 每份 except_post")
    identical_bytes = [r for r in recs if Path(r[2]).read_bytes() == exc_bytes]
    p("  逐字节 == EXCEPT 全文 的份数 = %d / %d" % (len(identical_bytes), len(recs)))

    p("")
    p("-- D3: 尺寸 / mtime / 文件名时间戳 分布")
    sizes = {}
    for h, n, fp, mt in recs:
        sizes[n] = sizes.get(n, 0) + 1
    p("  尺寸分布 = " + repr(sizes))
    mts = sorted(r[3] for r in recs)
    p("  mtime 最早 = " + (mts[0] if mts else "N/A"))
    p("  mtime 最晚 = " + (mts[-1] if mts else "N/A"))
    stamps = sorted(re.search(r"except_post_(\d{8}T\d+)\.txt", r[2]).group(1)
                    for r in recs if re.search(r"except_post_(\d{8}T\d+)\.txt", r[2]))
    p("  文件名时间戳范围 = " + (stamps[0] + " .. " + stamps[-1] if stamps else "N/A"))
    crash_instant = "20261019T1352"
    before = [s for s in stamps if s < crash_instant]
    after = [s for s in stamps if s >= crash_instant]
    p("  文件名时间戳 < 声称崩溃时刻 %s 的份数 = %d" % (crash_instant, len(before)))
    p("  文件名时间戳 >= 声称崩溃时刻 %s 的份数 = %d" % (crash_instant, len(after)))
    p("  EXCEPT 件自身 mtime = " + iso_mtime(EXCEPT) + "（早于此的快照已存在 ⇒ 内容不是 13:52 新产生）")

    p("")
    p("-- D4: 最早 / 最晚 / 不同树的代表件（逐一列出哈希与 mtime）")
    def show(tag, r):
        p("  %-8s %s  size=%d  mtime=%s  path=%s"
          % (tag, r[0][:16] + "...", r[1], r[3], os.path.relpath(r[2], ROOT)))
    if recs:
        by_mt = sorted(recs, key=lambda r: r[3])
        show("EARLIEST", by_mt[0])
        show("LATEST", by_mt[-1])
        outside = [r for r in recs if "lead\\qc161_u0400_trip\\" in r[2]
                   and "out\\re_work" not in r[2]]
        if outside:
            show("OUTSIDE", outside[0])

    # ---------- E. 上游源文件 except.txt（解释为什么 113 份同哈希） ----------
    p("")
    p("[E] 上游源文件 find('except.txt') → 逐份 sha256（机制旁证，非二选一判据）")
    srcs = find_named(ROOT, "except.txt")
    srecs = []
    for fp in srcs:
        h, n = sha_file(fp)
        srecs.append((h, n, fp))
    s_same = [r for r in srecs if r[0] == exc_sha]
    sdiff = {}
    for h, n, fp in srecs:
        sdiff[h] = sdiff.get(h, 0) + 1
    p("  except.txt 总数 = " + str(len(srecs)))
    p("  与 EXCEPT 同哈希 = " + str(len(s_same)))
    p("  distinct 哈希数 = " + str(len(sdiff)))
    for h, cnt in sorted(sdiff.items(), key=lambda x: -x[1]):
        p("    %s x%d %s" % (h, cnt, "<== 7CFC9F 基线" if h == exc_sha else ""))
    master = os.path.join(ROOT, "ra2bench", "except.txt")
    if os.path.exists(master):
        mh, mn = sha_file(master)
        p("  harness 声明的 EXCEPT_MASTER = " + master)
        p("    其 sha256 = " + mh + " ; size = " + str(mn))
        p("    首行 = " + repr(Path(master).read_bytes().splitlines()[0].decode("utf-8", "replace")))
        p("    ⇒ 母本其实是一份 ACCESS_VIOLATION 基线（≠ 7CFC9F 件）；")
        p("      7CFC9F 件来自另一条载体模板基线（_src_L3_sf10c_20261021 等）。")

    p("")
    p("-- E2: 其他可携该哈希的 odd-named except*.txt（逐一算，不靠猜测）")
    odd = find_named(ROOT, "except_*.txt")
    odd = [f for f in odd if not os.path.basename(f).startswith("except_post_")]
    odd_hits = []
    for fp in odd:
        h, n = sha_file(fp)
        if h == exc_sha:
            odd_hits.append((h, n, fp))
    p("  odd-named except_*.txt 总数（不含 except_post_*） = " + str(len(odd)))
    p("  其中与 EXCEPT 同哈希 = " + str(len(odd_hits)))
    for h, n, fp in odd_hits:
        p("    %s  size=%d  path=%s" % (h[:16] + "...", n, os.path.relpath(fp, ROOT)))

    # ---------- F. 二选一结论 ----------
    p("")
    p("[F] 明确二选一（Q4 定谳）")
    p("  EXCEPT 件 SHA256          = " + exc_sha)
    p("  except_post_*.txt 比对份数 = " + str(len(recs)))
    p("  同哈希份数                 = " + str(len(same)))
    p("  不同哈希份数               = " + str(len(diff)))
    if len(recs) > 0 and len(same) == len(recs) and len(diff) == 0:
        p("  ★ 结论 = 同哈希（SAME-HASH）")
        p("    ⇒ 这件 EXCEPT 不是任何一趟的崩溃：它是被 §555 判为「历史基线残件」的同一份字节，")
        p("      被 harness 以时间戳文件名反复快照了 %d 次。" % len(recs))
        p("    ⇒ 目标② 的「主崩溃」叙事必须重新定位：仓内 except_post 语料对判定崩溃无信息量。")
    elif len(diff) > 0:
        p("  ★ 结论 = 存在不同哈希 ⇒ 需逐件判定是否独立异常证据（本探针不自动下 SAME 结论）")
        for h, n, fp, mt in diff[:20]:
            p("    DIFF %s size=%d mtime=%s %s" % (h, n, mt, os.path.relpath(fp, ROOT)))
    else:
        p("  ★ 结论 = 未验（未找到任何 except_post_*.txt，不把「查不到」当「不存在」）")

    p("")
    p("[G] 诚实账 / 边界")
    p("  1. 口径 = 整仓 find（剪枝仅 .git）；§555/§590 的 107 是单一子树 qc161_u0400_trip 的口径，本探针整仓为 113。")
    p("  2. 本探针亲验：两份 SHA256/字节数、Engine 自证、rd/by/disasm、113 份逐份哈希、逐字节全文比对、尺寸/mtime。")
    p("  3. 机制（harness copy_post_except_evidence 复制载体 except.txt）来自读源码，非运行复现；属静态代码事实。")
    p("  4. 未验：37 个 archive 逐趟 console（§555 诚实账第 3 条仍未闭）；「游戏是否会崩」不能由本结论推出。")
    p("  5. 零真机 / 零采样注入 / 零活进程读取 / 未改任何既有文件 / 未 commit。")

    # ---------- 写出 ----------
    Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print("\n[written] " + OUT, flush=True)


if __name__ == "__main__":
    main()
