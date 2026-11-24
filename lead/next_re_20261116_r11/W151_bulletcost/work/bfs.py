# -*- coding: utf-8 -*-
"""W151: call-graph BFS helpers.
  python bfs.py from 0x55D360 3            -> reachable set within depth 3
  python bfs.py isect 0x55D360 3 work/slot5c_funcs.txt
  python bfs.py to 0x4666e0                -> reverse reachability (who can reach it), depth 8
"""
import os, sys, collections

ROOT = r"D:\Project\ra2-campaign-forge"
W = os.path.join(ROOT, r"lead\next_re_20261116_r11\W151_bulletcost\work")

E = collections.defaultdict(set)
R = collections.defaultdict(set)
for line in open(os.path.join(W, "edges.tsv"), encoding="utf-8"):
    p = line.split()
    if len(p) != 3:
        continue
    a, b = int(p[0], 16), int(p[1], 16)
    E[a].add(b)
    R[b].add(a)


def nm(a):
    return "0x%08x" % a


def bfs(g, root, depth):
    dist = {root: 0}
    q = collections.deque([root])
    while q:
        u = q.popleft()
        if dist[u] >= depth:
            continue
        for v in g.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


cmd = sys.argv[1]
if cmd == "from":
    root = int(sys.argv[2], 16); d = int(sys.argv[3])
    dist = bfs(E, root, d)
    print("reachable from %s within %d: %d funcs" % (nm(root), d, len(dist)))
    for dep in range(d + 1):
        nodes = sorted(k for k, v in dist.items() if v == dep)
        if dep <= 1:
            print(" depth %d (%d): %s" % (dep, len(nodes), " ".join(nm(x) for x in nodes)))
        else:
            print(" depth %d (%d)" % (dep, len(nodes)))
elif cmd == "isect":
    root = int(sys.argv[2], 16); d = int(sys.argv[3])
    tgt = [int(x.strip(), 16) for x in open(sys.argv[4]) if x.strip()]
    dist = bfs(E, root, d)
    hit = [t for t in tgt if t in dist]
    miss = [t for t in tgt if t not in dist]
    print("intersect reachable(%s,%d) with %d targets: %d hit / %d total" % (nm(root), d, len(tgt), len(hit), len(tgt)))
    for t in sorted(hit, key=lambda x: dist[x]):
        print("   HIT  %s depth=%d" % (nm(t), dist[t]))
    print("  -- not reachable within depth --")
    print("   " + " ".join(nm(t) for t in miss))
elif cmd == "to":
    t = int(sys.argv[2], 16); d = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    dist = bfs(R, t, d)
    print("can reach %s within %d: %d funcs" % (nm(t), d, len(dist)))
    for dep in range(min(d, 3) + 1):
        nodes = sorted(k for k, v in dist.items() if v == dep)
        print(" depth %d (%d): %s" % (dep, len(nodes), " ".join(nm(x) for x in nodes[:40])))
