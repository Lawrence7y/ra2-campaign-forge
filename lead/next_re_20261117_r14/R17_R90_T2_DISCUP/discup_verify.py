# -*- coding: utf-8 -*-
"""
discup_verify.py —— R49-T2-DISCUP 新校验式验证器

任务卡 R49-T2-DISCUP 要求实现新语法：
  exists                       产物文件存在（兼容旧式）
  bytes=<N>                    文件字节数 == N（兼容旧式）
  rows=<N>                     数据行数 == N（兼容旧式，减表头 1 行）
  grep=<regex>                 文件内正则命中 >= 1 次
  grepcount=<regex>=<N>        文件内正则命中次数 == N
  notgrep=<regex>              文件内正则命中 0 次

每个校验式形如：  <expr>[ ✓(注释)]   注释用首个空格切掉（与 check_disc.py 一致）。

用法：
  python discup_verify.py <tsv_path> [--row N] [--neg]
      --row N   只验证纪律号 N（默认全部）
      --neg     反控模式：把每条 grep=/grepcount=/notgrep= 的正则替换为
                必错形式（ZZZ_NOT_EXIST_ZZZ），断言验证器必须报 FAIL。
                若某条反控仍 PASS → 该条无判别力，应回退 exists。

退出码：0 = 全部符合预期；1 = 有 FAIL（或反控有「没 FAIL」的条目）。

接口说明（给 Lead 的 check_disc.py 调用，不修改 check_disc.py）：
  from discup_verify import verify_row
  ok, detail = verify_row(ROOT, path, expr)
      ROOT   = r'D:\\Project\\ra2-campaign-forge'
      path   = DISC_RECHECK.tsv 第 5 列（如 r'lead\\next_re_...\\anchor_check.txt'）
      expr   = 第 6 列校验式（含或不含 ✓(...) 注释均可）
      返回   = (bool, str)  ok=True 表示通过，detail 为可读明细。
  在 check_disc.py 的 run_expr(path, expr) 内，对 grep=/grepcount=/notgrep=
  三类分支直接 return verify_row(ROOT, path, expr) 即可；其余分支保持原样。

设计要点：
  - 正则一律用 Python re（re.finditer / re.findall），默认大小写敏感。
  - 读取文件用 utf-8 + errors='replace'，避免不可解码字节导致假 FAIL。
  - grepcount 对「同一行多次命中」按“命中次数”计（finditer 个数），不是“命中行数”。
    本任务选用的表达式均为「一行一次」，故两者等价；Q1 明细会注明。
"""
import io
import os
import re
import sys

# 与 check_disc.py 相同的根
ROOT = r'D:\Project\ra2-campaign-forge'
NEG_TOKEN = 'ZZZ_NOT_EXIST_ZZZ'   # 反控用必错正则（正常产物不应出现）


def _read(p):
    return io.open(p, encoding='utf-8', errors='replace', newline='').read()


def _resolve(path):
    return os.path.join(ROOT, path.replace('\\', '/'))


def _strip_note(expr):
    """去掉 ✓(...) 注释：按首个空格切（与 check_disc.py 一致）。"""
    return expr.strip().split(' ')[0]


def check(clause, text):
    """解析单条子句并返回 (ok: bool|None, detail: str)。
       ok=None 表示「无校验式 / 不参与」；True/False 为判定。
    """
    if clause == 'exists':
        return True, 'exists'
    if clause == 'none':
        return None, 'none'
    m = re.fullmatch(r'bytes=(\d+)', clause)
    if m:
        # 字节数需在调用处用文件；这里用传入 text 的长度是不对的，改由 verify_row 处理
        return None, 'BYTES_NEED_FILE'
    m = re.fullmatch(r'rows=(\d+)', clause)
    if m:
        return None, 'ROWS_NEED_TEXT'
    m = re.fullmatch(r'grep=(.*)', clause, re.S)
    if m:
        pat = m.group(1)
        n = len(re.findall(pat, text))
        return (n >= 1), 'grep hits=%d' % n
    m = re.fullmatch(r'grepcount=(.*)=(\d+)', clause, re.S)
    if m:
        pat, want = m.group(1), int(m.group(2))
        n = len(re.findall(pat, text))
        return (n == want), 'grepcount hits=%d want=%d' % (n, want)
    m = re.fullmatch(r'notgrep=(.*)', clause, re.S)
    if m:
        pat = m.group(1)
        n = len(re.findall(pat, text))
        return (n == 0), 'notgrep hits=%d want=0' % n
    return False, 'BAD_EXPR:' + clause


def verify_row(ROOT_OVERRIDE, path, expr):
    """供 check_disc.py 调用的稳定接口：返回 (ok: bool|None, detail: str)。"""
    root = ROOT_OVERRIDE or ROOT
    ap = _resolve(path) if root == ROOT else os.path.join(root, path.replace('\\', '/'))
    if not os.path.isfile(ap):
        return False, 'FILE_MISSING'
    clause = _strip_note(expr)

    m = re.fullmatch(r'bytes=(\d+)', clause)
    if m:
        actual = os.path.getsize(ap)
        return (actual == int(m.group(1))), 'bytes=%d want=%s' % (actual, m.group(1))
    m = re.fullmatch(r'rows=(\d+)', clause)
    if m:
        # 与 check_disc.py 完全一致：for line in f 计数（末尾 \n 不产生额外空行），再减 1 去表头
        with io.open(ap, encoding='utf-8', errors='replace', newline='') as f:
            n = 0
            for _ in f:
                n += 1
        data_lines = n - 1
        return (data_lines == int(m.group(1))), 'rows=%d want=%s' % (data_lines, m.group(1))

    text = _read(ap)
    ok, detail = check(clause, text)
    return ok, detail


def make_negative(expr):
    """反控：按任务卡 Q4 的原形，把提取式改成「必错形式」 grep=ZZZ_NOT_EXIST_ZZZ。
       正常产物不含该 token ⇒ 0 命中 ⇒ 校验器必须报 FAIL。
       统一使用同一必错形式，便于逐条对照、避免人为挑选。
    """
    return 'grep=' + NEG_TOKEN


def load_rows(tsv):
    txt = _read(tsv)
    raw = [l for l in txt.split('\n') if l]
    return [l.split('\t') for l in raw[1:]]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    tsv = args[0]
    only_row = None
    neg = False
    i = 1
    while i < len(args):
        if args[i] == '--row':
            only_row = int(args[i + 1]); i += 2
        elif args[i] == '--neg':
            neg = True; i += 1
        else:
            i += 1

    rows = load_rows(tsv)
    print('TSV=%s rows=%d neg=%s' % (tsv, len(rows), neg))
    total = passed = failed = 0
    neg_applicable = neg_failed = 0
    for r in rows:
        if len(r) != 7:
            print('  BADCOLS', r[0] if r else '?', len(r)); continue
        num, path, expr = r[0], r[4].strip(), r[5].strip()
        if only_row is not None and num != str(only_row):
            continue
        clause = _strip_note(expr)
        is_new = clause.startswith(('grep=', 'grepcount=', 'notgrep='))
        if neg:
            if not is_new:
                continue
            neg_applicable += 1
            w = make_negative(expr)
            ok, detail = verify_row(ROOT, path, w)
            did_fail = (ok is False)
            if did_fail:
                neg_failed += 1
            print('  NEG 纪律%s %-42s -> %s (%s)' % (
                num, w, 'FAIL(OK)' if did_fail else 'PASS(!!NO DISCRIMINATION)', detail))
        else:
            total += 1
            ok, detail = verify_row(ROOT, path, expr)
            if ok is True:
                passed += 1
            else:
                failed += 1
            print('  %-4s 纪律%s %-28s %s' % ('PASS' if ok is True else ('SKIP' if ok is None else 'FAIL'),
                                              num, clause[:28], detail))
    if neg:
        print('NEG 汇总: 适用 %d 条 ; 确实 FAIL %d 条' % (neg_applicable, neg_failed))
        sys.exit(0 if neg_failed == neg_applicable else 1)
    print('汇总: %d 条 ; PASS %d ; FAIL %d' % (total, passed, failed))
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
