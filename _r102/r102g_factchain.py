#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102g_factchain.py —— R101 待办⑦「5 个旧版本目录缺 SUPERSEDED」的前提核验与改正

R101 待办⑦原文：「FACT_INDEX v5.32 之前的 5 个旧版本目录仍无 SUPERSEDED.md 标记，
须按 R49/R51 标记链纪律补齐并重指向 v5.32」。

本脚本对该前提做机械核验。三处前提都不成立或需改写：

  P1 「5 个旧版本目录」—— 盘上以 FACT_INDEX 为名的目录共 7 个，但其中**只有 3 个真的含
     FACT_INDEX.tsv**（v530 / v531 / v532）。另 4 个（V53 / V58 / V511 / R88_T1）**根本不含
     索引本体**，只含辅助证据（anchor_check.txt / CHANGES.md / REPORT.md / lead_byte_checks.tsv）。
     把辅助证据目录标成「本目录已作废、请勿引用」会**抹掉现行索引引用的证据**。

  P2 「5 个」这个数与盘上任何一组都对不上：索引本体目录 3 个、辅助目录 4 个、合计 7 个。

  P3 真有缺口的是 **v5.29 整目录消失**：_r65/make_v530.py 的第 9 行以
     R17_R100_FACTINDEX_V529 为输入，该目录现在不存在，R17_LEAD_BASELINE 里也无任何
     v529 备份。这是**链断裂**，不是「缺标记」。

  P4 而 v530 / v531 是否该标 SUPERSEDED，取决于现行 v532 是否**引用它们作为证据路径**。
     若引用，标 SUPERSEDED 会让现行索引指向一个自称作废的目录 —— 那是制造矛盾。

结论方向：本项**不能**按原待办执行（会破坏证据链 / 会抹掉辅助证据）。正确处置是
① 只对「索引本体且未被现行版引用」的目录标 SUPERSEDED；
② 辅助证据目录改用另一种标记语（不是「作废」，是「非索引本体，属 vX 的辅助证据」）；
③ v5.29 的消失如实登记为不可恢复，不伪造。
本脚本只做核验与登记，不擅自写任何 SUPERSEDED.md（那需要单独一卡 + 跨家族审计）。
"""
import hashlib, io, json, os, re, sys

R14 = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
OUT = '/home/t628/projects/ra2-campaign-forge/_r102'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def main():
    os.makedirs(OUT, exist_ok=True)
    dirs = sorted(d for d in os.listdir(R14) if re.match(r'^R17_R\d+.*_FACT', d) or
                  re.match(r'^R17_R\d+_T1_FACTINDEX$', d))
    info = {}
    for d in dirs:
        p = os.path.join(R14, d)
        if not os.path.isdir(p):
            continue
        files = sorted(os.listdir(p))
        has_tsv = 'FACT_INDEX.tsv' in files
        n_rows = None
        sha = None
        if has_tsv:
            t = io.open(os.path.join(p, 'FACT_INDEX.tsv'), encoding='utf-8').read()
            n_rows = len([l for l in t.split('\n') if l]) - 1
            sha = hashlib.sha256(io.open(os.path.join(p, 'FACT_INDEX.tsv'), 'rb').read()).hexdigest()[:16]
        info[d] = {'files': files, 'has_index': has_tsv, 'rows': n_rows, 'sha16': sha,
                   'has_superseded': any('SUPERSEDED' in f for f in files)}

    idx = {d: v for d, v in info.items() if v['has_index']}
    aux = {d: v for d, v in info.items() if not v['has_index']}
    ck('P0 以 FACT_INDEX 为名的目录数 = 7', len(info) == 7, sorted(info))
    ck('P1 真含索引本体的目录 = 3（v530/v531/v532）', len(idx) == 3, sorted(idx))
    ck('P2 不含索引本体的辅助目录 = 4', len(aux) == 4, sorted(aux))
    ck('P3 原待办说的「5 个旧版本目录」与盘上任何一组都不符（3/4/7 ≠ 5）',
       5 not in (len(idx), len(aux), len(info)), '3 / 4 / 7')

    # v5.29 是否真的消失
    v529 = os.path.join(R14, 'R17_R100_FACTINDEX_V529')
    ck('P4 v5.29 目录不存在（_r65/make_v530.py 第 9 行的输入）', not os.path.isdir(v529), v529)
    mk = io.open(os.path.join(R14, '_r65', 'make_v530.py'), encoding='utf-8').read()
    ck('P5 make_v530.py 确实以 V529 为 SRC', 'R17_R100_FACTINDEX_V529' in mk, '')
    bak = [f for f in os.listdir(os.path.join(R14, 'R17_LEAD_BASELINE'))
           if re.search(r'v529|V529', f, re.I)]
    ck('P6 R17_LEAD_BASELINE 无任何 v529 备份 ⇒ 不可恢复（不伪造）', bak == [], bak)

    # 现行 v532 是否引用 v530/v531 作为证据路径
    cur = idx.get('R17_R104_FACTINDEX_V532')
    ck('P7 现行版 = v532 且 54 行', cur is not None and cur['rows'] == 54,
       cur and (cur['rows'], cur['sha16']))
    curtxt = io.open(os.path.join(R14, 'R17_R104_FACTINDEX_V532', 'FACT_INDEX.tsv'),
                     encoding='utf-8').read()
    ref530 = curtxt.count('R17_R102_FACTINDEX_V530')
    ref531 = curtxt.count('R17_R103_FACTINDEX_V531')
    ck('P8 现行 v532 引用 v530 的次数（>0 则不可标作废）', True, ref530)
    ck('P9 现行 v532 引用 v531 的次数（>0 则不可标作废）', True, ref531)

    # 辅助目录被现行版引用的次数
    aux_refs = {d: curtxt.count(d) for d in aux}
    ck('P10 四个辅助目录里被现行版引用的个数', True, aux_refs)

    # 全树范围：这些目录还被谁引用（决定能否标作废）
    allref = {}
    for d in list(idx) + list(aux):
        n = 0
        for root, _, fs in os.walk(R14):
            if root.startswith(os.path.join(R14, d)):
                continue
            for f in fs:
                if not f.endswith(('.md', '.tsv', '.py', '.txt')):
                    continue
                try:
                    t = io.open(os.path.join(root, f), encoding='utf-8', errors='ignore').read()
                except Exception:
                    continue
                n += t.count(d)
        allref[d] = n
    ck('P11 每个目录的全树引用次数（>0 的一律不得标「作废」）', True, allref)

    # 结论表
    verdict = []
    for d, v in sorted(info.items()):
        if d == 'R17_R104_FACTINDEX_V532':
            act = 'CURRENT 现行版，不动'
        elif not v['has_index']:
            act = 'AUX 辅助证据目录，不是索引本体 ⇒ 不标 SUPERSEDED，改标「辅助证据」'
        elif allref.get(d, 0) > 0:
            act = 'REFERENCED 索引本体但被引用 %d 次 ⇒ 标 SUPERSEDED 会制造矛盾，须先解引用' % allref[d]
        else:
            act = 'SUPERSEDABLE 可标 SUPERSEDED'
        verdict.append({'dir': d, 'has_index': v['has_index'], 'rows': v['rows'],
                        'sha16': v['sha16'], 'refs_all_tree': allref.get(d, 0),
                        'action': act})

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'dirs': info, 'verdict': verdict, 'v529_missing': not os.path.isdir(v529),
               'v532_refs': {'v530': ref530, 'v531': ref531}, 'aux_refs': aux_refs,
               'all_tree_refs': allref,
               'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks},
              io.open(os.path.join(OUT, 'r102g_factchain.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print()
    for v in verdict:
        print('%-34s refs=%-4d %s' % (v['dir'], v['refs_all_tree'], v['action']))
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
