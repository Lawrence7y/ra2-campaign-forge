import hashlib, sys, os
for p in sys.argv[1:]:
    h = hashlib.sha256()
    n = 0
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
            n += len(chunk)
    print(h.hexdigest(), n, os.path.abspath(p))
