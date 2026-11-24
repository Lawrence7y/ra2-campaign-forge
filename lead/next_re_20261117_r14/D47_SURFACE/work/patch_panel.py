import io
sa = open('surface.py', encoding='utf-8').read()
pb = open('work/panel_base.py', encoding='utf-8').read()
start = pb.index('SUB_RE = re.compile')
end = pb.index("if __name__ == '__main__':")
blk = pb[start:end]
sa = sa.rstrip() + "\n\n\n# --------------------------------------------------------------------- panel columns\n" + blk
open('surface.py', 'w', encoding='utf-8').write(sa)
print('appended', len(blk), 'chars')
