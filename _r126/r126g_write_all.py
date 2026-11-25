# -*- coding: utf-8 -*-
"""R126: 把本轮记录写进四件套，并先按 260 行阈值归档看板最早两段。

每个目标文档的纪律（与 R125 一致）：
  wx 独占备份 -> 断言旧 sha256 与旧 CR 与登记值一致 -> 断言新写入文本零反引号
  -> 单次写入 -> 回读校验（sha、CR、行数、新段存在）

看板归档：STATUS_BOARD.md 现有 261 行，>= 260 阈值，先把最早的两段整段搬到
BOARD_ARCHIVE.md 末尾，再追加第 126 轮记录。归档后断言 BOARD_ARCHIVE CR 仍 2952、
STATUS_BOARD CR 仍 0。
"""
import io, os, sys, hashlib, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BK = os.path.join(R14, 'R17_LEAD_BASELINE')
RC = os.path.join(R14, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
BRD = os.path.join(R14, 'STATUS_BOARD.md')
ARC = os.path.join(R14, 'BOARD_ARCHIVE.md')

EXPECT = {
    RC:  ('c3c3b4c245b16d19', 1081),
    LED: ('03c773e13f40fc08', 337),
    LOCK: ('d3d70987e35dca18', 137),
    BRD: ('695c5a6a377d5c9d', 0),
    ARC: ('38ec0269c23806ab', 2952),
}

TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def backup(path, tag):
    data = io.open(path, 'rb').read()
    dst = os.path.join(BK, 'r126_%s.%s.bak' % (tag, TS))
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL)   # wx 独占创建
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return dst, data


def assert_baseline(path, tag):
    dst, data = backup(path, tag)
    want_sha, want_cr = EXPECT[path]
    got_sha, got_cr = sha16(data), data.count(b'\r')
    assert got_sha == want_sha, '%s sha %s != %s' % (tag, got_sha, want_sha)
    assert got_cr == want_cr, '%s CR %d != %d' % (tag, got_cr, want_cr)
    return dst, data


def write_checked(path, new_bytes, tag, want_cr, extra=None, check_bt=True):
    # 反引号纪律只约束本轮新写的文字，不约束从看板逐字搬进归档的旧正文。
    if check_bt:
        assert b'`' not in new_bytes, '%s 新文本含反引号' % tag
    old = io.open(path, 'rb').read()
    with io.open(path, 'wb') as f:
        f.write(new_bytes)
    rb = io.open(path, 'rb').read()
    assert rb == new_bytes, '%s 回读不一致' % tag
    assert rb.count(b'\r') == want_cr, '%s CR %d != %d' % (tag, rb.count(b'\r'), want_cr)
    if extra:
        extra(rb)
    print('  WROTE %-8s sha %s -> %s  CR=%d  bytes %d -> %d'
          % (tag, sha16(old), sha16(rb), rb.count(b'\r'), len(old), len(rb)))
    return rb


# ================= 1. 看板归档（先归档后追加） =================
brd_bak, brd = assert_baseline(BRD, 'STATUS_BOARD')
arc_bak, arc = assert_baseline(ARC, 'BOARD_ARCHIVE')

text = brd.decode('utf-8')
lines = text.split('\n')
assert lines and lines[-1] == '', '看板末行应为空行'
# 段首 = 以 '## ' 开头的行；找最早两段的起点
sec_idx = [i for i, ln in enumerate(lines) if ln.startswith('## ')]
assert len(sec_idx) >= 3, '看板里可见段数 %d < 3，无法按阈值归档' % len(sec_idx)
cut = sec_idx[2]                       # 第三段的起点，前两段整段搬走
moved = '\n'.join(lines[:cut]).rstrip('\n')
rest = '\n'.join(lines[cut:])
assert moved and rest, '归档切割后有空段'

arc_new = (arc.decode('utf-8').rstrip('\n') + '\n\n' + moved + '\n')
write_checked(ARC, arc_new.encode('utf-8'), 'ARCHIVE', 2952, check_bt=False)

brd_new = rest
assert len(brd_new.split('\n')) <= 300, '归档后看板仍超 300 行'
write_checked(BRD, brd_new.encode('utf-8'), 'BOARD-ARC', 0)

# ================= 2. 第 126 轮看板段 =================
SEC_BOARD = '''
## 🟢 R17 第 126 轮（2026-11-25 02:0x–03:0x）· 推翻 R124/R125 台账两条「不可分」，取得 0x7e9b40 = IFlyControl；并纠正我自己两处误定名

### 一 · 起点：R125 留下的两条「不可分」各自都有字节反例

R125 台账 GK 末段写着「0x7e9b40 仍与 0x7f7c70/0x7f7c80 这对不可分」「0x7f7cf0 在 IStream 与 ISequentialStream 间仍不可分」。本轮两条都用字节推翻。

0x7e9b40 的解：AircraftClass 的 QueryInterface 体在 0x414290，先 call 0x410260 委派给基类，只有基类失败才比自己的 IID。0x4142b1 是 mov edi, 0x7e9b40，比对成功后的分支在 0x4142c1 是 lea eax, [ebx + 0x6c0]，紧接着 0x4142c8 是 mov dword ptr [ebp], eax。也就是说 0x7e9b40 对应的子对象在 this + 0x6c0。

AircraftClass 的 RTTI 有 18 条基类。mdisp 恰为 0x6c0 的是两条：.?AUIFlyControl@@ 与一个 .?AUIUnknown@@，这是多继承子对象的标准配对（每个接口子对象都带自己的 IUnknown）。剔除 IUnknown 后唯一，就是 IFlyControl。全量 954 个类里 mdisp 0x6c0 只出现这一处。

### 二 · 为什么 R124 会把它和 IPersist 家族混在一起

同一个类的 RTTI 在 mdisp 0 处并排有 .?AUIPersistStream@@ 与 .?AUIPersist@@。这两个接口自己没有次对象偏移，所以在任何类里它们都是 mdisp 0 —— R124 用的「出参 this 调整值 == RTTI mdisp」在这两个名字上恒有两条候选，结构上永远分不开。R124 把它们记成「三条记录完全对称」，这是对的；但把 0x7e9b40 也归进这一组是错的，它走的是 0x6c0 那条路。

### 三 · 0x7f7cf0 那条「不可分」的表述本身无依据

0x7f7cf0 的 16 字节是 0000000C-0000-0000-C000-000000000046，即标准 IID_IStream。IID_ISequentialStream 是 0C733A30-2A1C-11CE-ADE5-00AA0044773D，它的 16 字节在整份映像里出现 0 次，连 Data1 (0x0C733A30) 也出现 0 次（正控：IStream 的 Data1 0x0000000C 出现 539 次）。所以「在 IStream 与 ISequentialStream 之间不可分」不是测不出，而是那个候选根本不在映像里。

### 四 · GUID 池与孪生的全量普查（R125 只做了两个 IID）

按两种 Data4 模式（OLE 系 d4 全 8 字节是模式、MIDL 系后 6 字节才是模式）起步，得到 65 个 GUID 窗口：55 个在 .rdata、10 个在 .data。整份映像里 16 字节完全相同的「孪生」共 9 对，每对都是一个 .rdata 配一个 .data。标准 OLE 前缀（Data1 <= 0x1FF、Data2/Data3 全零）恰 10 处、6 个不同 Data1：0x0、0x1、0xC、0x109、0x10C、0x13A；其中 4 个各有 .rdata 与 .data 两处，0x1 与 0x13A 只有 .rdata 一处。

口径陷阱（反控已跑）：把两种模式统一按 k-8 起算会整体偏移两字节，错口径下 0x7e36c0 与 0x7e9b20 都解不出来。

### 五 · 孪生形态分离能推多远（对抗性自审）

形式 R（mov edi 落在 QI 模板内）与形式 C（push 立即数）在 9 对上并非纯净分离：0x7f7c90 的 .rdata 侧形式 C 有 56 条、0x7f7c80 的 .rdata 侧有 60 条。反过来 .data 侧的形式 R 在全部 4 对上都是 0。所以能说的只有一句：.data 那份只被 push 引用，.rdata 那份两种都有。这不是「谁是 IPersist」的证据。

我也核了「.data 站点是否集中在少数函数」这个我原本以为会成立的预期 —— 不成立：0x818858 的 16 个站点落在 15 或 16 个函数、0x820270 的 8 个站点落在 8 个函数。

### 六 · 我这一轮自己犯的两处误定名（已改，记在案）

第一版机制把「mov ecx, 4 + mov edi, IID + repe cmpsd」当 QI 体，但调用方也会这么写：0x501805 与 0x44dedd 的 esi 来自 lea esi, [esp + 0x24]，是调用方把 GUID 副本放在栈上再比。据此我先把 0x7e9550 定成 INoticeSource、0x7e9a50 定成 ReferenceCounted。补上「esi 不得由 lea 取地址」这条后两个名字都消失。修正后剩下的三个名字全都是 .?AU 前缀（接口），没有 .?AV（类）混进来，这与 R124 的「.?AU 名字 26 个即 COM 接口」一致。

另一处：我给脚本写的「this+0x6c0 全映像应只有 2 处」是估计值，实测 10 处（1 处 QI 体写出参、9 处取子对象地址）。断言已改为实测值。

### 七 · 跨家族（规则 D）

审计员 hy4 task 251 succeeded，50 回合 / 11.28 分钟，派发预算 8.0 分钟 —— 超时为 OVERTIME，如实记。报告 _r126/audit/r126_audit_hy4.md 共 151 行、零反引号。数字逐条独立复算（r126d 10 项）：标准 OLE 前缀 10 处 6 个 Data1 一致；形式 R/C 八个数 4/0、0/16、4/60、0/8、91/56、0/9、1/0、0/2 逐个一致；0x7f7cd0 的 Data1 = 0xB196B284 一致；0x7f7c70 末字节翻转后命中 0 次一致。

它有两条我要改：其一，它的总结写「5 对加 1 个单点」，但它自己的表格是 10 处 —— 10 处只能蕴含 4 对加 2 单（0x7f7ca0 与 0x7f7d00 各只有 .rdata 一处）。我按它表格的数字复算是 4 对 2 单，采纳表格不采纳总结。其二，0x818858 的站点落在 15 还是 16 个函数，两支口径差 1（它的函数起点口径给 15，我用「前一条 ret」口径给 16），两个数都支持同一个结论（高度分散），我把断言写在分散度上而不是精确值上。

### 八 · 收口

r126a 11 + r126b 12 + r126c 10 + r126d 10 + r126e 8 + r126f 10 = 61 项断言全 PASS。全程 disasm_lite 流式扫描，未对整段 .text 开 detail=True；脚本带 timeout；收口前 ps 确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0，本轮不改门禁。

看板按 260 行阈值先归档最早两段（第 120 轮与第 124 轮整段搬到 BOARD_ARCHIVE.md），归档后看板 CR 仍 0、归档 CR 仍 2952。

### 九 · 未取得（不粉饰）

① 0x7f7c70 与 0x7f7c80 谁是 IPersist、谁是 IPersistStream 仍不由字节给出 —— 这两个接口在所有类里都占 mdisp 0，本轮没找到第三条内部记录能把它们分开。② 0x7e36c0 与 0x7e9b20 的 QI 体不被任何类的 slot0 引用，本方法对它们只能给出「查了哪些 IID」（都查 0x7f7c90），给不出接口名。③ 0x7e9b20 的 QI 体在 0x6cf478 处把出参写成 QI 返回值本身、不做 this 调整，故它的 this 偏移仍是 0。④ 0x7e9a50 等 49 个 .rdata IID 的站点都不落在任何类的 slot0 上，本方法对它们无解。⑤ 35 个静态容器的运行期元素值与计数。⑥ 共用模板展开的充分证明。⑦ 门禁 C11 其余四处永远通过子项、五条不可能行未裁定、窗口表未扩。
'''


def _assert_marker(b):
    assert b'R17 \xe7\xac\xac 126 \xe8\xbd\xae' in b, '看板回读未见第 126 轮段'


# 追加看板段
brd_now = io.open(BRD, 'rb').read().decode('utf-8')
assert '`' not in SEC_BOARD, 'SEC_BOARD 含反引号'
brd_final = brd_now.rstrip('\n') + '\n' + SEC_BOARD
n_lines = len(brd_final.split('\n'))
assert n_lines <= 300, '追加后看板 %d 行超过 300' % n_lines
write_checked(BRD, brd_final.encode('utf-8'), 'BOARD', 0,
              extra=lambda b: _assert_marker(b))

print('DONE')
