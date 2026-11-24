import io, os, json

ROOT = r'D:\Project\ra2-campaign-forge'
LIMIT = 1024 * 1024
targets = [
    ('mesh_imm32.json', 5693169),
    ('sweep.json', 1631944),
    ('e8_sites_audit.json', 1365087),
    ('scan_mine.json', 1365365),
]
for bn, expect in targets:
    ap = None
    for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
        if bn in fs:
            ap = os.path.join(dp, bn); break
    if not ap:
        print('%s MISSING' % bn); continue
    size = os.path.getsize(ap)
    print('=== %s (%d B)' % (bn, size))
    # 读前 1 MiB 与全量，比结构
    head = io.open(ap, encoding='utf-8', errors='replace').read(LIMIT)
    full = io.open(ap, encoding='utf-8', errors='replace').read()
    print('   前 1 MiB 字符数 = %d ; 全量 = %d ; 尾部未读 = %d (%.1f%%)'
          % (len(head), len(full), len(full) - len(head), 100.0 * (len(full) - len(head)) / len(full)))
    # 前 1MiB 里的地址密度 vs 尾部
    import re
    RX = re.compile(r'0x[0-9A-Fa-f]{6,8}|\b[0-9A-Fa-f]{8}\b')
    h_n = len(RX.findall(head))
    t_n = len(RX.findall(full[len(head):]))
    print('   地址命中: 前 1 MiB = %d ; 尾部 = %d' % (h_n, t_n))
    # 结构：是不是 JSON，顶层是什么
    try:
        obj = json.loads(full)
        if isinstance(obj, dict):
            print('   顶层 dict keys = %s' % (list(obj.keys())[:6],))
        elif isinstance(obj, list):
            print('   顶层 list len = %d ; 首元素类型 = %s' % (len(obj), type(obj[0]).__name__ if obj else 'empty'))
    except Exception as e:
        print('   非合法整 JSON: %s' % str(e)[:60])
    print()
