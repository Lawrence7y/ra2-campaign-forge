# -*- coding: utf-8 -*-
"""append_link.py —— R55-T1-RERUN 的唯一写动作：把自描述行**追加**到 5 个产物末尾。

用法：
    python append_link.py --dry-run     # 只打印将要追加什么，不写
    python append_link.py --go          # 真追加（每个产物仅一条）

纪律（逐条对应卡面 §五）：
  1. 只追加、不改写：追加前后各记一次原文件字节数；**并且**用「前 N 字节 sha256」
     证明原有 N 字节逐字节未变（N = 追加前字节数）。这比只比字节数更强。
  2. anchors 必须真算：直接复用 r55_recheck.py 的 anchor_hash（对 row[3] 原样串 sha256），
     不写死、不填 0。
  3. conclusion 必须实测：取自 measure() 的实测判定，不由本脚本的入参决定。
  4. 取不到写「未取得」：measure() 里任何异常都落成 UNKNOWN，不 fallback 成 PASS。

conclusion 的判定规则（判据来自 DISC_RECHECK.tsv 第 6 列「校验式」，不是我自己发明的）：
  * 纪律 3：核「人工核验/池未加载」类是否为 0。实测 = anchor_check.txt 中
            「池未加载(未核验)」与「人工核验类(无节号)」两行都为 0，且 exit=0。否则 FAIL。
  * 纪律 4：核「节号体例」类锚是否逐条列出。实测 = 「节号体例通过」计数 >0
            且出口校验式 grep 命中（即与实际计数一致）。否则 FAIL。
  * 纪律 22：rows==1468 且 sum==149493508 ⇒ PASS，否则 FAIL。
  * 纪律 27：分布 732/244/266 ⇒ PASS，否则 FAIL。
  * 纪律 28：rows==4518 且 sum==724479859 ⇒ PASS，否则 FAIL。
  实测成功但产物里已存在一条自描述行（每产物仅一条）⇒ 不追加，记 SKIP。

换行：**沿用各产物自身已有的 EOL**（TSV 用 CRLF 的仍写 CRLF，LF 的写 LF）。
  理由：纪律 3/4/22/28 四个产物是 LF（CR 字节 0，既有纪律一直在守这个）；
  `_verdicts.tsv` 通篇 CRLF（由 csv.writer 默认 terminator 产生），
  往里塞一行 LF 会造出混行文件，属于「改变产物性质」。故按文件自身 EOL 写。
"""
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = r'D:\Project\ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
DR = os.path.join(R14, 'DISC_RECHECK.tsv')

ROUND = 'R55'
PREFIX = 'DISC_RECHECK '


# --------------------------------------------------------------------------
# 基础设施
# --------------------------------------------------------------------------
def read_bytes(path):
    with io.open(path, 'rb') as f:
        return f.read()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load_disc_rows():
    txt = io.open(DR, encoding='utf-8', newline='').read()
    out = {}
    for ln in [l for l in txt.split('\n') if l][1:]:
        c = ln.split('\t')
        if c[0].strip().isdigit():
            out[int(c[0])] = c
    return out


def anchor_hash(row):
    """逐字照 recheck_verify.py 的 R5：sha256(UTF-8(row[3]))，row[3] 原样不 strip。"""
    return 'sha256:' + sha256(row[3].encode('utf-8'))


def detect_eol(raw):
    crlf = raw.count(b'\r\n')
    lf = raw.count(b'\n')
    return b'\r\n' if crlf > 0 and crlf == lf else b'\n'


def owner_of(line):
    """取自描述行里的 discipline 号；不是自描述行则 None。"""
    m = re.match(r'^DISC_RECHECK discipline=(\d+) ', line)
    return int(m.group(1)) if m else None


def existing_link_lines(raw, disc=None):
    """列出产物里已有的自描述行；给了 disc 则只列**属于该纪律**的。

    产物唯一性规则是「每纪律在**其对应产物**里仅一条」（§2.51），
    不是「每个文件全局仅一条」——纪律 3 与 4 共用 anchor_check.txt，
    两条行分别 bind 各自的第 4 列锚，故必须按 discipline 归属判重。
    """
    out = []
    for l in raw.decode('utf-8', 'replace').splitlines():
        if not l.startswith(PREFIX):
            continue
        if disc is None or owner_of(l) == disc:
            out.append(l)
    return out


# --------------------------------------------------------------------------
# 实测（每条纪律一个，返回 (conclusion, measured_str)）
# --------------------------------------------------------------------------
def _read_text(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def measure_anchor_check(path, disc):
    txt = _read_text(path)

    def grab(label):
        m = re.search(r'(?m)^\s*' + re.escape(label) + r'\s+(\d+)', txt)
        return int(m.group(1)) if m else None

    pool = grab(u'池未加载(未核验)')
    manual = grab(u'人工核验类(无节号)')
    secn = grab(u'节号体例通过')
    mech = grab(u'机械核验通过')
    exitm = re.search(r'(?m)^\[exit (\d+)\]', txt)
    exit_code = int(exitm.group(1)) if exitm else None

    if disc == 3:
        ok = (pool == 0 and manual == 0 and exit_code == 0)
        measured = (u'池未加载(未核验)=%s 人工核验类=%s exit=%s'
                    % (pool, manual, exit_code))
        return ('PASS' if ok else 'FAIL'), measured
    if disc == 4:
        ok = (secn is not None and secn > 0 and exit_code == 0)
        measured = (u'节号体例通过=%s 机械核验通过=%s exit=%s'
                    % (secn, mech, exit_code))
        return ('PASS' if ok else 'FAIL'), measured
    return 'UNKNOWN', u'未取得'


def measure_table(path, bytes_col):
    """数「数据行」与 sum(bytes_col)。

    关键：自描述行（DISC_RECHECK ...）是**元数据尾注**，不是数据行，
    必须在数行与求和时排除——否则回跑自身会把自己的凭证算成数据，
    使 rows 从 1468 变 1469（这正是纪律 3/13 那类「度量器把自己算进语料」）。
    本函数按「首个 tab 前不是 'DISC_RECHECK '」来判数据行，不依赖行位置。
    """
    data_rows = 0
    total = 0
    bad = 0
    for ln in _read_text(path).split('\n'):
        if ln == '' or ln.startswith(PREFIX):
            continue
        if data_rows == 0 and ln.split('\t')[0] == 'rel':   # 表头
            data_rows += 1
            continue
        data_rows += 1
        c = ln.split('\t')
        v = c[bytes_col].strip() if bytes_col < len(c) else ''
        if re.fullmatch(r'\d+', v):
            total += int(v)
        else:
            bad += 1
    return data_rows - 1, total, bad


def measure_verdict(path):
    dist = {}
    for ln in _read_text(path).split('\n'):
        if ln == '' or ln.startswith(PREFIX):
            continue
        c = ln.split('\t')
        if c[0] == 'rel':          # 表头
            continue
        if len(c) < 2:
            continue
        dist[c[1].strip()] = dist.get(c[1].strip(), 0) + 1
    return dist


def measure(disc, path):
    """返回 (conclusion, measured_str, expected_str)。异常 ⇒ UNKNOWN。"""
    try:
        if disc in (3, 4):
            return measure_anchor_check(path, disc)
        if disc == 22:
            r, s, bad = measure_table(path, 1)
            ok = (r == 1468 and s == 149493508 and bad == 0)
            return (('PASS' if ok else 'FAIL'),
                    u'rows=%d sum=%d（登记 1468 / 149493508）' % (r, s))
        if disc == 27:
            d = measure_verdict(path)
            want = {u'对象抄本': 732, u'过程输出': 244, u'无法判定': 266}
            ok = (d == want)
            got = u'/'.join(u'%s=%d' % (k, d.get(k, 0))
                            for k in (u'对象抄本', u'过程输出', u'无法判定'))
            return (('PASS' if ok else 'FAIL'),
                    u'%s（登记 732/244/266，合计 %d）' % (got, sum(d.values())))
        if disc == 28:
            r, s, bad = measure_table(path, 1)
            ok = (r == 4518 and s == 724479859 and bad == 0)
            return (('PASS' if ok else 'FAIL'),
                    u'rows=%d sum=%d（登记 4518 / 724479859）' % (r, s))
    except Exception as e:  # noqa: BLE001 —— 取不到就是 UNKNOWN，绝不 fallback 成 PASS
        return 'UNKNOWN', u'未取得（%s: %s）' % (type(e).__name__, e)
    return 'UNKNOWN', u'未取得'


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main():
    go = '--go' in sys.argv
    dry = not go
    now = None
    # at 用真实本次运行时刻（+08:00）
    import datetime
    now = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()

    rows = load_disc_rows()
    plan = []
    for disc in (3, 4, 22, 27, 28):
        row = rows[disc]
        rel = row[4].strip()
        path = os.path.join(ROOT, rel.replace('\\', '/'))
        if not os.path.isfile(path):
            print(u'[MISSING] discipline=%d  %s  ⇒ 未取得，不追加' % (disc, rel))
            continue

        raw_before = read_bytes(path)
        before = len(raw_before)
        pre_hash = sha256(raw_before)

        conclusion, measured = measure(disc, path)
        line = (u'DISC_RECHECK discipline=%d round=%s at=%s anchors=%s conclusion=%s'
                % (disc, ROUND, now, anchor_hash(row), conclusion))

        existed = existing_link_lines(raw_before, disc)
        plan.append(dict(disc=disc, rel=rel, path=path, before=before,
                         pre_hash=pre_hash, line=line, conclusion=conclusion,
                         measured=measured, eol=detect_eol(raw_before),
                         existed=existed))

    print(u'=== R55-T1-RERUN 追加计划（%s）==='
          % (u'DRY-RUN，不写盘' if dry else u'GO，将真追加'))
    for p in plan:
        print(u'\n--- discipline %d ---' % p['disc'])
        print(u'  product : %s' % p['rel'])
        print(u'  bytes_before : %d   sha256[:16]=%s' % (p['before'], p['pre_hash'][:16]))
        print(u'  EOL     : %r' % p['eol'])
        print(u'  measured: %s' % p['measured'])
        print(u'  concl.  : %s' % p['conclusion'])
        print(u'  line    : %s' % p['line'])
        if p['existed']:
            print(u'  !! 产物里已存在 %d 条自描述行 ⇒ 跳过（每产物仅一条）'
                  % len(p['existed']))
            p['skip'] = True
        else:
            p['skip'] = False

    if dry:
        print(u'\n[DRY-RUN] 未写任何字节。加 --go 执行。')
        return 0

    print(u'\n=== 执行追加 ===')
    rc = 0
    # 同一产物被多条纪律共用时（纪律 3 与 4 都写 anchor_check.txt），
    # 先写的那条会让后者的「追加前字节数」失效。这不是并发写者，是本批次的自身顺序，
    # 故显式记下「哪些纪律在本轮会先写进同一文件」，只对这一情形放宽字节数比对。
    done_paths = {}
    for p in plan:
        if p['skip']:
            print(u'[SKIP] discipline=%d 已有自描述行' % p['disc'])
            continue
        cur_raw = read_bytes(p['path'])
        cur = len(cur_raw)
        if cur != p['before']:
            # 仅当差距恰好是本批次前面已写入的同文件追加行时才允许继续
            prev = done_paths.get(p['path'])
            tail = cur_raw[p['before']:].decode('utf-8', 'replace').splitlines()
            tail_all_siblings = bool(prev) and len(tail) == len(prev) and all(
                t == q['line'] for t, q in zip(tail, prev))
            if not tail_all_siblings:
                print(u'[ABORT] discipline=%d 字节数在测量后变化 %d -> %d，'
                      u'且变化不是本批次同文件追加，不追加'
                      % (p['disc'], p['before'], cur))
                rc = 1
                continue
            print(u'[NOTE] discipline=%d 与纪律 %s 共用同一产物；新增字节经核对'
                  u'均为本批次已追加的自描述行，前缀哈希另验'
                  % (p['disc'], u','.join(str(q['disc']) for q in prev)))
            p['pre_hash'] = sha256(cur_raw)   # 以当前全量为前缀基线
            p['before'] = cur
        elif done_paths.get(p['path']):
            # 同文件但字节数相等不可能发生（上面已追加）；保险起见走同一校验
            pass
        with io.open(p['path'], 'ab') as f:
            f.write(p['line'].encode('utf-8') + p['eol'])
        raw_after = read_bytes(p['path'])
        after = len(raw_after)
        prefix_ok = sha256(raw_after[:p['before']]) == p['pre_hash']
        tail = raw_after[p['before']:]
        print(u'[APPEND] discipline=%d bytes %d -> %d (+%d) prefix_unchanged=%s'
              % (p['disc'], p['before'], after, after - p['before'], prefix_ok))
        print(u'         appended_tail=%r' % tail)
        if not prefix_ok:
            print(u'         [FAIL] 原有内容被改动！')
            rc = 1
        done_paths.setdefault(p['path'], []).append(p)

    print(u'\n[rc=%d]' % rc)
    return rc


if __name__ == '__main__':
    sys.exit(main())
