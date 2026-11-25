# -*- coding: utf-8 -*-
"""R127b: 给 LEAD_LOCK 补 GW2 / GX 两段（规则 D 的采纳证据与自错记录）。

GV 段已经写了「断言与收口」，但采纳的那条证据（两个固定参数包装器）与两条自错
（S-177 pSelf、S-178 读早了审计报告）还没进 LEAD_LOCK。本脚本把它们插到 GV 与 GY 之间。

纪律：wx 独占备份 -> 断言旧 sha256 与旧 CR -> 断言插入文本零反引号 -> 单次写入
-> 回读校验（sha、CR=137、两段标记存在、段序 GV < GW2 < GX < GY）。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')

# 本次写入前 LEAD_LOCK 的 sha（r127f 写完之后的状态）
EXPECT_SHA = 'a5c2c5b6366b0eb6'
EXPECT_CR = 137
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

INS = '''
GW2. 采纳审计员一条我原来漏掉的硬证据（H10，已复算）：存在两个「固定参数包装器」直接 call QI 体 —— 0x4f6930 是 push ecx / lea eax,[esp] / push eax / push 0x7e36c0 / push 0x89a29c / call 0x429360 / mov eax,[esp] / pop ecx / ret 4；0x429550 是 mov eax,[esp+8] / push eax / push 0x7e9b20 / push 0xb0c110 / call 0x6cf430 / ret 8。IID 与对象都写死、只留出参，比 vtable 槽更直接：证明这两个 IID 确实是交给这两个 QI 体去比的。反控：同一判据对 0x429480（IClassFactory::CreateInstance 的包装器，push 0x7e36c0 后 call [ecx]）给否。

GX. 本轮自错再补两条。S-177：r127h 的 H6 第一版用「COL 的 +20 处 pSelf 必须等于 COL 自身地址」当校验，但该构建所有 COL 的 +20 全为 0（0x80b730 的 24 字节是 00 00 00 00 与 30 27 84 00 20 b7 80 00 00 00 00 00），判据恒假。改用 signature(0/1) + pTypeDescriptor(+12) + pClassDescriptor(+16) 三个字段定位。S-178：我把审计员**中途**落盘的 7215 字节版本当成最终报告，据此写了 H6/H7 两条「裁决分歧」；回收最终版（273 行 / 11111 字节）后它自己已把 RTTI 解析改对，两条分歧都不存在。教训：必须等 wait_subagents 返回再读报告，不拿中途快照当结论。

'''


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    assert '`' not in INS, '插入文本含反引号'
    old = io.open(LOCK, 'rb').read()
    dst = os.path.join(BK, 'r127b_LEAD_LOCK.%s.bak' % TS)
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        os.write(fd, old)
    finally:
        os.close(fd)
    assert sha16(old) == EXPECT_SHA, '旧 sha %s != %s' % (sha16(old), EXPECT_SHA)
    assert old.count(b'\r') == EXPECT_CR, '旧 CR %d != %d' % (old.count(b'\r'), EXPECT_CR)

    txt = old.decode('utf-8')
    i_gv = txt.find('GV. ')
    i_gy = txt.find('GY. ')
    assert i_gv > 0 and i_gy > i_gv, 'GV/GY 定位失败 (%d, %d)' % (i_gv, i_gy)
    new_txt = txt[:i_gy] + INS.lstrip('\n') + '\n' + txt[i_gy:]
    nb = new_txt.encode('utf-8')

    with io.open(LOCK, 'wb') as f:
        f.write(nb)
    rb = io.open(LOCK, 'rb').read()
    assert rb == nb, '回读不一致'
    assert rb.count(b'\r') == EXPECT_CR, '新 CR %d != %d' % (rb.count(b'\r'), EXPECT_CR)

    rt = rb.decode('utf-8')
    a, b2, c, d = (rt.find('GV. '), rt.find('GW2. '), rt.find('GX. '),
                   rt.find('GY. '))
    assert -1 < a < b2 < c < d, '段序错: GV=%d GW2=%d GX=%d GY=%d' % (a, b2, c, d)
    print('  WROTE LEAD_LOCK  sha %s -> %s  CR=%d  bytes %d -> %d  LF %d -> %d'
          % (sha16(old), sha16(rb), rb.count(b'\r'), len(old), len(rb),
             old.count(b'\n'), rb.count(b'\n')))


if __name__ == '__main__':
    main()
