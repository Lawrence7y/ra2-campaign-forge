import shlex

argv = [r'D:\Project\ra2-campaign-forge\out\x.py', r'--target-map', r'D:\a\b.MAP']

old = "python " + " ".join(argv)          # 旧 quote()：无反斜杠/空格 ⇒ 不加引号
new = "python " + " ".join('"%s"' % a for a in argv)  # 加双引号

for name, cmd in (("OLD(unquoted)", old), ("NEW(quoted)", new)):
    toks = shlex.split(cmd, posix=True)
    got = toks[1:]
    print("%-14s cmd=%s" % (name, cmd))
    print("   split=%r" % (got,))
    print("   match=%s" % (got == argv))
    print()
