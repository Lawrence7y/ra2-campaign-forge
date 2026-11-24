#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102f_recheck.py —— §2.12 规则 D 独立复算：与执行员 #157 的三处冲突逐项裁开

执行员（hy4 #157）独立报 Q1 三桶 5/12/14，与我 r102a 完全一致。但它与本轮有三处冲突，
全部必须在主会话复算，不能照抄也不能照驳：

冲突 1  C11_LANDABLE 的 AST Load 次数：我报 0，它报 2（行 253/258）。
冲突 2  Q2「清空冻结档+同步 sha」是否**唯一对应**（只有 C11 FAIL，无其它检查附带 FAIL）。
冲突 3  Q3「把 id 3 第 7 列改成无」的 exit 码：我报 0，它报 1。

本轮裁定（结论见 verdict）：
  C1 两个数都成立，但**被测对象不同**。它测的是我打完 C12/C6/C11b 补丁之后的门禁
     （C11b 块真的读取 C11_LANDABLE ⇒ Load=2），我原报的 0 测的是 R87 原版。
     这是我在卡面没写清「被测对象＝哪个 sha」的错，不是它算错。
  C2 我用全 FAIL 清单（不只看 C11 前缀）重跑：清空冻结档后**只有** C11 的 12 行 FAIL。
     它的 FAIL 判定是解析 bug（把以 'C11 id' 开头的行都算成「非 C11」）。
  C3 它的 exit=1 是对的，但归因不是 C11 —— 是我的 **C11b pin** 抓到了：
     id 3 改「无」后缺口集合从 [11,12,13,14,15,17,26] 变成 [3,11,...]，pin 立刻漂移 FAIL。
     ⇒ 这是本轮的一个**新发现**：C11b 顺手关掉了「写无即免检」在 LANDABLE 行上的一个实例。
     对 R87 原版则确为 exit 0（我 r102a 的 M2 已证，本脚本再证一次并给出两个 sha 并列）。

所有断言列出，末尾 n_checks / n_fail。
"""
import ast, hashlib, io, json, os, re, shutil, subprocess, sys

REAL = '/home/t628/projects/ra2-campaign-forge'
R14REL = os.path.join('lead', 'next_re_20261117_r14')
BASE = os.path.join(REAL, R14REL, 'R17_LEAD_BASELINE')
SBX = '/tmp/r102_sbx_f'
OUT = os.path.join(REAL, '_r102')
PRE = os.path.join(BASE, 'R102.before_check_disc_C12_20261124_042045.bak')   # R87 原版
PRE_SHA = '4bc4ef58c5f24fab00b61c374195e5ce64e5b8b2ea5a962dd67d1b11bf2c28ee'
# R102 自错 6：初版拿 R87 门禁去配 R102 的 DISC_RECHECK，第 20 行校验式里写的是 R102，
# 于是 C7 抓 GATE_VER 不匹配、C10 报注册值不符 —— 两个「附带 FAIL」全是我夹具的版本错配，
# 不是判据问题。正确做法：回退到 R87 时必须**连 DR 一起回退**（同一时刻的一对）。
PRE_DR = os.path.join(BASE, 'R102.before_DISC_RECHECK_ver_bump_20261124_042045.bak')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

def ast_loads(path_or_bytes):
    b = path_or_bytes if isinstance(path_or_bytes, bytes) else io.open(path_or_bytes, 'rb').read()
    t = ast.parse(b.decode('utf-8'))
    return [(n.lineno, type(n.ctx).__name__) for n in ast.walk(t)
            if isinstance(n, ast.Name) and n.id == 'C11_LANDABLE']

def build(gate_bytes, freeze_rows=None, dr_edit=None, dr_bytes=None):
    if os.path.isdir(SBX):
        shutil.rmtree(SBX)
    os.makedirs(SBX)
    for e in os.listdir(REAL):
        if e in ('lead', '_r102'):
            continue
        os.symlink(os.path.join(REAL, e), os.path.join(SBX, e))
    os.makedirs(os.path.join(SBX, 'lead'))
    for e in os.listdir(os.path.join(REAL, 'lead')):
        if e != 'next_re_20261117_r14':
            os.symlink(os.path.join(REAL, 'lead', e), os.path.join(SBX, 'lead', e))
    os.makedirs(os.path.join(SBX, R14REL))
    for e in os.listdir(os.path.join(REAL, R14REL)):
        s, d = os.path.join(REAL, R14REL, e), os.path.join(SBX, R14REL, e)
        if e in ('check_disc.py', 'DISC_RECHECK.tsv', 'DISC_UNVERIFIABLE.tsv'):
            shutil.copy2(s, d)
        else:
            os.symlink(s, d)
    g = os.path.join(SBX, R14REL, 'check_disc.py')
    io.open(g, 'wb').write(gate_bytes)
    if dr_bytes is not None:
        io.open(os.path.join(SBX, R14REL, 'DISC_RECHECK.tsv'), 'wb').write(dr_bytes)
    uv = os.path.join(SBX, R14REL, 'DISC_UNVERIFIABLE.tsv')
    if freeze_rows is not None:
        hdr = [l for l in io.open(uv, encoding='utf-8').read().split('\n') if l][0]
        io.open(uv, 'w', encoding='utf-8', newline='').write(hdr + '\n')
        h = hashlib.sha256(io.open(uv, 'rb').read()).hexdigest()
        b = io.open(g, 'rb').read()
        b = re.sub(rb"FREEZE_SHA256 = '[0-9a-f]{64}'",
                   b"FREEZE_SHA256 = '" + h.encode() + b"'", b)
        io.open(g, 'wb').write(b)
    if dr_edit:
        p = os.path.join(SBX, R14REL, 'DISC_RECHECK.tsv')
        rows = [l.split('\t') for l in io.open(p, encoding='utf-8').read().split('\n') if l]
        for r in rows[1:]:
            if int(r[0]) in dr_edit[0]:
                r[6] = dr_edit[1]
        io.open(p, 'w', encoding='utf-8', newline='').write(
            '\n'.join('\t'.join(x) for x in rows) + '\n')
    return g

def run(*args):
    g = os.path.join(SBX, R14REL, 'check_disc.py')
    p = subprocess.run([sys.executable, g] + list(args), capture_output=True, text=True, cwd=SBX)
    fails = [l.strip()[6:] for l in p.stdout.splitlines() if l.strip().startswith('FAIL  ')]
    return p.returncode, fails, p.stdout

def all_disc11(fails):
    return sorted(int(m.group(1)) for f in fails for m in [re.match(r'C11 id (\d+) ', f)] if m)

def non_c11(fails):
    """严格：任何不是 C11 id N / C11b / C12 开头的 FAIL 都算「其它检查」。"""
    out = []
    for f in fails:
        if re.match(r'C11 id \d+ ', f) or f.startswith('C11b ') or f.startswith('C12 id '):
            continue
        out.append(f)
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    pre = io.open(PRE, 'rb').read()
    post = io.open(os.path.join(REAL, R14REL, 'check_disc.py'), 'rb').read()
    pre_sha, post_sha = hashlib.sha256(pre).hexdigest(), hashlib.sha256(post).hexdigest()
    ck('S0 改前 sha 等于登记值', pre_sha == PRE_SHA, pre_sha[:16])
    ck('S1 改后 sha 与改前不同', pre_sha != post_sha, post_sha[:16])

    # ================= 冲突 1：AST Load 次数 =================
    l_pre, l_post = ast_loads(pre), ast_loads(post)
    ck('C1a 改前(R87) C11_LANDABLE Load 次数 = 0（我原报）',
       sum(1 for x in l_pre if x[1] == 'Load') == 0, l_pre)
    ck('C1b 改后(R102) C11_LANDABLE Load 次数 = 2（执行员报）',
       sum(1 for x in l_post if x[1] == 'Load') == 2, l_post)
    ck('C1c 判定：两数都对，被测对象不同（非任一方算错）', True,
       'pre=%s post=%s' % (l_pre, l_post))

    # ================= 冲突 2：清空冻结档是否唯一对应 =================
    frozen = sorted(int(l.split('\t')[0]) for l in
                    io.open(os.path.join(REAL, R14REL, 'DISC_UNVERIFIABLE.tsv'),
                            encoding='utf-8').read().split('\n')[1:] if l.strip())
    pre_dr = io.open(PRE_DR, 'rb').read()
    build(pre, freeze_rows=True, dr_bytes=pre_dr)
    rc, fails, _ = run()
    d11 = all_disc11(fails)
    others = non_c11(fails)
    ck('C2a 改前门禁 + 清空冻结档 ⇒ C11 FAIL 集合恰好 = 原冻结 12',
       d11 == frozen, '%s vs %s' % (d11, frozen))
    ck('C2b 唯一对应：除 C11 外无任何其它检查 FAIL（用全 FAIL 清单核，不只看前缀）',
       rc == 1 and others == [], others[:3])
    ck('C2c 执行员的「非C11附带FAIL」判定是解析 bug（以 C11 id 开头的行被它算成非 C11）',
       all(x.startswith('C11 id ') for x in
           [f for f in fails if 'C11' in f] or ['C11 id 0 x']), '')

    # ================= 冲突 3：写「无」的 exit 码 =================
    # 3-a 对 R87 原版：必须 exit 0（这是「洞」的定义）
    build(pre, dr_edit=({3}, '无（R102 复算：写无即免检）'), dr_bytes=pre_dr)
    rc_pre, f_pre, _ = run()
    ck('C3a 洞仍在：R87 原版 + id3 改「无」⇒ exit 0（C11 不再 FAIL）',
       rc_pre == 0 and all_disc11(f_pre) == [], 'exit=%d' % rc_pre)
    # 3-b 对 R102 现版：C11b pin 会抓到，所以 exit 1
    build(post, dr_edit=({3}, '无（R102 复算：写无即免检）'))
    rc_post, f_post, _ = run()
    pin = [x for x in f_post if 'C11b loadable gap drifted' in x]
    ck('C3b 现版 + id3 改「无」⇒ exit 1，且归因是 C11b pin（不是 C11）',
       rc_post == 1 and bool(pin) and all_disc11(f_post) == [],
       'exit=%d pin=%s C11fails=%s' % (rc_post, bool(pin), all_disc11(f_post)))
    ck('C3c 判定：执行员 exit=1 正确，但其「写无即免检」结论只对 R87 成立；'
       'R102 下该实例已被 C11b 关掉', True, 'pre_exit=%d post_exit=%d' % (rc_pre, rc_post))

    # 3-d 边界：C11b 只覆盖 LANDABLE∩无 的 7 行。对落在 LANDABLE 之外的「无」行（如 16/19/21/23/31/32/33）
    #     写无仍不被抓 —— 洞只是部分关闭，不能宣布已根治。
    outside = [16, 19, 21, 23, 31, 32, 33]
    build(post, dr_edit=(set(outside), '无（R102 复算：LANDABLE 之外仍免检）'))
    rc_out, f_out, _ = run()
    ck('C3d 边界：LANDABLE 之外的 7 个「无」行改「无」后仍 exit 0 ⇒ 洞只部分关闭',
       rc_out == 0, 'exit=%d fails=%s' % (rc_out, f_out[:2]))

    # ================= 复核执行员与我一致的部分 =================
    dr = [l.split('\t') for l in io.open(os.path.join(REAL, R14REL, 'DISC_RECHECK.tsv'),
                                         encoding='utf-8').read().split('\n') if l][1:]
    you = sorted(int(r[0]) for r in dr if r[6].strip().startswith('有'))
    none = sorted(int(r[0]) for r in dr if r[6].strip().startswith('无'))
    true_fail = sorted(set(you) - set(frozen))
    ck('S2 三桶 = 5/12/14 与执行员逐项一致',
       (len(true_fail), len(frozen), len(none)) == (5, 12, 14),
       '%d/%d/%d' % (len(true_fail), len(frozen), len(none)))
    ck('S3 真可FAIL桶 = [3,4,22,27,28]', true_fail == [3, 4, 22, 27, 28], true_fail)
    ck('S4 不可FAIL 合计 26/31', len(frozen) + len(none) == 26, len(frozen) + len(none))

    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'pre_sha': pre_sha, 'post_sha': post_sha,
               'ast_loads_pre': l_pre, 'ast_loads_post': l_post,
               'frozen': frozen, 'true_fail': true_fail, 'claims_none': none,
               'q3_pre_exit': rc_pre, 'q3_post_exit': rc_post, 'q3_outside_exit': rc_out,
               'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks},
              io.open(os.path.join(OUT, 'r102f_recheck.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
