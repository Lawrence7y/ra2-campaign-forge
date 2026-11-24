# -*- coding: utf-8 -*-
"""r102a_holes.py —— 门禁「永远通过」两个洞的行为级实测（沙箱变异，不碰真门禁）

问题（R101 EC8 ④ 遗留）：check_disc.py 的 C11「是否真回跑」在 31 行里到底能对几行 FAIL？
两项先天豁免看起来存在：
  洞 1 冻结摘帽：DISC_UNVERIFIABLE.tsv 里 12 行声称「有（后续轮回跑）」但产不出合规自述行，
        C11 对它们走 c11_declared（不 FAIL）。去掉冻结位是否立刻 12/12 FAIL？
  洞 2 写无即免检：col7 以「无」开头者直接 c11_unver += 1 并 continue，
        即「只要声明没回跑过，就永远不需要回跑」。同一行把 col7 从「有」改成「无」
        是否从 FAIL 变 PASS？

方法：把门禁整套放进沙箱根（只 symlink 真产物，仅复制 3 个可变态：
check_disc.py / DISC_RECHECK.tsv / DISC_UNVERIFIABLE.tsv），逐个变异跑子进程看退出码。
所有断言带正反控：
  POS  原样沙箱必须 exit 0（否则后面所有对比无意义）
  M1  把 id 3 的产物路径改指「缺该自述行」的临时文件 ⇒ 必须 exit 1（证明变异通道有效）
  M2  在 M1 基础上只把 id 3 的 col7 改成「无」⇒ 必须 exit 0（同格翻转 ⇒ 洞 2 成立）
  M3  清空冻结档（并把 FREEZE_SHA256 改到新 sha，绕过防篡改）⇒ 必须恰好 12 行 C11 FAIL
  M4  把 14 行「无」全改成「有」⇒ 必须恰好 14 行 C11 FAIL（证明 0/14 曾产出合规自述行）
  M5  对 claims-none 行破坏 C7（路径指向不存在文件）⇒ 必须 C7 FAIL（证明只豁免 C11，不豁免 C7）
反控 NC1：M1 若不 exit 1，则 M2 的 exit 0 无信息（先证明该格能让判据翻转）。
"""
import io, os, re, shutil, subprocess, sys, json

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
SBX = '/tmp/r102_sbx'
OUT = os.path.join('/home/t628/projects/ra2-campaign-forge', '_r102')
checks = []
def ck(name, ok, detail=''):
    checks.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})
    return ok

def build_sandbox():
    """重建沙箱：真树整体 symlink，仅 3 个可变态用副本覆盖。
    R102 自错 1：初版只链了 lead/，漏掉 ROOT 顶层条目 —— id 31 的产物路径
    是 ROOT 相对的 _r94\falsify_r94.py，导致 POS 原样沙箱就 C7 FILE_MISSING。
    教训：沙箱必须把 ROOT 的**每一个**顶层条目都处置掉（链接或排除），不能只链关心的那一支。"""
    if os.path.isdir(SBX):
        shutil.rmtree(SBX)
    os.makedirs(SBX)
    SKIP = {R14REL.split(os.sep)[0], '_r102'}      # lead/ 单独处理；自身产物目录排除
    for e in os.listdir(REAL):
        if e in SKIP:
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(SBX, e))
    os.makedirs(os.path.join(SBX, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e == 'next_re_20261117_r14':
            continue
        os.symlink(os.path.join(REAL, 'lead', e), os.path.join(SBX, 'lead', e))
    os.makedirs(os.path.join(SBX, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        src = os.path.join(REAL, R14REL, e)
        dst = os.path.join(SBX, R14REL, e)
        if e in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
            shutil.copy2(src, dst)          # 可变态：真副本
        else:
            os.symlink(src, dst)            # 其余：不复制、不落地
    return os.path.join(SBX, R14REL)

def run_gate(tag):
    """跑沙箱子进程门禁，返回 (exit, fails[], stdout)。"""
    p = subprocess.run([sys.executable, os.path.join(SBX, R14REL, 'check_disc.py')],
                       capture_output=True, text=True, cwd=SBX)
    fails = [l.strip()[len('FAIL  '):] for l in p.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    return p.returncode, fails, p.stdout

def read_tsv(path):
    txt = io.open(path, encoding='utf-8', newline='').read()
    return [l.split('\t') for l in txt.split('\n') if l], txt.endswith('\n')

def write_tsv(path, rows, nl):
    io.open(path, 'w', encoding='utf-8', newline='').write(
        '\n'.join('\t'.join(r) for r in rows) + ('\n' if nl else ''))

def ids_failing_c11(fails):
    out = []
    for f in fails:
        m = re.match(r'C11 id (\d+) ', f)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)

def main():
    os.makedirs(OUT, exist_ok=True)
    build_sandbox()
    dr = os.path.join(SBX, R14REL, 'DISC_RECHECK.tsv')
    uv = os.path.join(SBX, R14REL, 'DISC_UNVERIFIABLE.tsv')
    gate = os.path.join(SBX, R14REL, 'check_disc.py')
    dr0, nl_dr = read_tsv(dr)
    uv0, nl_uv = read_tsv(uv)
    ck('S0 沙箱 DISC_RECHECK 行数=31+表头', len(dr0) == 32, len(dr0))

    # ---------- POS 原样 ----------
    rc, fails, so = run_gate('pos')
    ck('POS 原样沙箱 exit 0', rc == 0, 'exit=%d fails=%s' % (rc, fails[:4]))

    # 三个分桶（从真表算，不猜）
    hdr, body = dr0[0], dr0[1:]
    n_hdr = len(hdr)
    ck('S1 表 7 列', n_hdr == 7, n_hdr)
    claim_you = [int(r[0]) for r in body if r[6].strip().startswith('有')]
    claim_none = [int(r[0]) for r in body if r[6].strip().startswith('无')]
    frozen = [int(r[0]) for r in uv0[1:] if r and r[0].strip().isdigit()]
    ck('S2 分桶总数闭合 31', len(claim_you) + len(claim_none) == 31,
       '%d+%d' % (len(claim_you), len(claim_none)))
    ck('S3 冻结 12', len(frozen) == 12, frozen)
    ck('S4 claim有 17', len(claim_you) == 17, claim_you)
    ck('S5 claim无 14', len(claim_none) == 14, claim_none)
    ck('S6 冻结 ⊆ claim有', set(frozen) <= set(claim_you), sorted(set(frozen) - set(claim_you)))

    # C11_LANDABLE 与「无」的交集（门禁自己的常量说这些应当可落地）
    LANDABLE = {3, 4, 11, 12, 13, 14, 15, 17, 22, 26, 27, 28}
    land_none = sorted(LANDABLE & set(claim_none))
    ck('S7 LANDABLE∩claim无 = 7', land_none == [11, 12, 13, 14, 15, 17, 26], land_none)

    # ---------- M1 正控：id 3 产物满足 C7 但缺 discipline 3 自述行 ----------
    # R102 自错 2：初版把 id 3 指向一个空文件，结果 C7 的 grep 也一起失败，
    # 「翻转变异」就不是唯一对应的了 —— 违反纪律 32（反控必须打在判据真正读到的那一格）。
    # 正确做法：产物是 anchor_check.txt 的副本，只删掉 discipline=3 那一行 ⇒ C7 仍过、只 C11 翻。
    prod3 = os.path.join(SBX, 'r102_prod3.txt')
    src_prod = os.path.join(REAL, R14REL, 'R17_R61_FACTINDEX_V58', 'anchor_check.txt')
    ptxt = io.open(src_prod, encoding='utf-8', errors='replace').read()
    kept = [l for l in ptxt.split('\n')
            if not (l.startswith('DISC_RECHECK ') and 'discipline=3 ' in l)]
    io.open(prod3, 'w', encoding='utf-8', newline='').write('\n'.join(kept))
    ck('M1-pre id3 产物仍有 C7 的 grep 锚、且已无 discipline=3 自述行',
       bool(re.search(r'池未加载\(未核验\)\s+0', '\n'.join(kept)))
       and not any(l.startswith('DISC_RECHECK ') and 'discipline=3 ' in l for l in kept))
    m1 = [list(r) for r in dr0]
    for r in m1:
        if r[0] == '3':
            r[4] = 'r102_prod3.txt'        # 相对 ROOT
    write_tsv(dr, m1, nl_dr)
    rc1, f1, so1 = run_gate('m1')
    c11_1 = ids_failing_c11(f1)
    c7_1 = [x for x in f1 if x.startswith('C7 id 3')]
    ck('M1 正控：id3 指「C7 过但无自述行」产物 ⇒ exit 1、C11 id3 FAIL、C7 id3 不 FAIL',
       rc1 == 1 and c11_1 == [3] and not c7_1,
       'exit=%d C11fails=%s C7id3=%s' % (rc1, c11_1, c7_1))

    # ---------- M2 同格翻转：只改 col7 为「无」 ----------
    m2 = [list(r) for r in m1]
    for r in m2:
        if r[0] == '3':
            r[6] = '无（仅立条当轮自带）'
    write_tsv(dr, m2, nl_dr)
    rc2, f2, _ = run_gate('m2')
    ck('M2 洞 2：同一行只把 col7 改成「无」⇒ exit 0（写无即免检）',
       rc2 == 0 and 3 not in ids_failing_c11(f2), 'exit=%d fails=%s' % (rc2, f2[:3]))

    # ---------- M3 冻结摘帽：清空冻结档 + 同步改 FREEZE_SHA256 ----------
    write_tsv(dr, dr0, nl_dr)                       # 还原 DISC_RECHECK
    empty_uv = [uv0[0]]                             # 只留表头
    write_tsv(uv, empty_uv, nl_uv)
    new_sha = __import__('hashlib').sha256(io.open(uv, 'rb').read()).hexdigest()
    gsrc = io.open(gate, encoding='utf-8').read()
    gsrc2 = re.sub(r"FREEZE_SHA256 = '[0-9a-f]{64}'",
                   "FREEZE_SHA256 = '%s'" % new_sha, gsrc)
    io.open(gate, 'w', encoding='utf-8', newline='').write(gsrc2)
    ck('M3-pre 沙箱门禁 FREEZE_SHA256 已同步', new_sha in gsrc2, new_sha[:16])
    rc3, f3, so3 = run_gate('m3')
    c11_3 = ids_failing_c11(f3)
    ck('M3 洞 1：清空冻结档 ⇒ 恰好 12 行 C11 FAIL 且集合等于冻结 12',
       rc3 == 1 and c11_3 == sorted(frozen), 'exit=%d fails=%s' % (rc3, c11_3))

    # 反控 NC2：冻结档原样但不去改 sha ⇒ 必须被判 TAMPERED（防无声摘帽）
    shutil.copy2(os.path.join(REAL, R14REL, 'DISC_UNVERIFIABLE.tsv'), uv)
    write_tsv(uv, empty_uv, nl_uv)                  # 清空但门禁里 sha 仍是新 sha（=被清空后那份）
    # 还原成「真档 + 旧 sha」：把真档写回但门禁 sha 保持新 sha
    shutil.copy2(os.path.join(REAL, R14REL, 'DISC_UNVERIFIABLE.tsv'), uv)
    rc4, f4, _ = run_gate('nc2')
    tamper = any('TAMPERED' in x for x in f4)
    ck('NC2 反控：冻结档与门禁常量不符 ⇒ 必须 TAMPERED', rc4 == 1 and tamper, f4[:2])
    shutil.copy2(os.path.join(REAL, R14REL, 'check_disc.py'), gate)   # 复原门禁

    # ---------- M4 14 行「无」全改「有」 ----------
    m4 = [list(r) for r in dr0]
    for r in m4[1:]:
        if int(r[0]) in claim_none:
            r[6] = '有（后续轮回跑）'
    write_tsv(dr, m4, nl_dr)
    rc5, f5, _ = run_gate('m4')
    c11_5 = ids_failing_c11(f5)
    ck('M4 14 行改「有」⇒ 恰好这 14 行 C11 FAIL（0/14 曾产出合规自述行）',
       rc5 == 1 and c11_5 == sorted(claim_none), 'exit=%d C11fails=%s' % (rc5, c11_5))

    # ---------- M5 C7 仍对 claims-none 生效 ----------
    m5 = [list(r) for r in dr0]
    for r in m5:
        if r[0] == '11':
            r[4] = 'r102_missing_product.tsv'      # 不存在
    write_tsv(dr, m5, nl_dr)
    rc6, f6, _ = run_gate('m5')
    c7 = [x for x in f6 if x.startswith('C7 id 11')]
    ck('M5 claims-none 行仍受 C7 约束（路径不存在 ⇒ C7 FAIL）',
       rc6 == 1 and bool(c7), 'exit=%d C7id11=%s' % (rc6, c7))

    # ---------- 收尾：还原并复跑 ----------
    write_tsv(dr, dr0, nl_dr)
    shutil.copy2(os.path.join(REAL, R14REL, 'DISC_UNVERIFIABLE.tsv'), uv)
    rc7, f7, _ = run_gate('restore')
    ck('POS2 还原后 exit 0（沙箱未留痕）', rc7 == 0, 'exit=%d fails=%s' % (rc7, f7[:3]))

    # 汇总
    summary = {
        'claim_you': len(claim_you), 'claim_none': len(claim_none), 'frozen': len(frozen),
        'can_fail_c11': sorted(set(claim_you) - set(frozen)),
        'cannot_fail_c11_frozen': sorted(frozen),
        'cannot_fail_c11_declared_none': sorted(claim_none),
        'landable_but_declared_none': land_none,
        'm3_c11_fail_ids': c11_3, 'm4_c11_fail_ids': c11_5,
        'n_checks': len(checks), 'n_fail': sum(1 for c in checks if not c['ok']),
        'checks': checks,
    }
    json.dump(summary, io.open(os.path.join(OUT, 'r102a_holes.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for c in checks:
        print('%-4s %s | %s' % ('PASS' if c['ok'] else 'FAIL', c['name'], c['detail'][:120]))
    print('n_checks=%d n_fail=%d' % (summary['n_checks'], summary['n_fail']))
    print('可 FAIL(C11) 行 = %s' % summary['can_fail_c11'])
    print('冻结豁免 = %d 行；写无豁免 = %d 行；合计不可 FAIL = %d / 31'
          % (len(frozen), len(claim_none), len(frozen) + len(claim_none)))
    return 0 if summary['n_fail'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
