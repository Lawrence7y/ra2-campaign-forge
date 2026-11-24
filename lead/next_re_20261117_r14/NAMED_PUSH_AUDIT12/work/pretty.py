import re
def name_pretty(m):
    if not m: return m
    p = m.split("@")
    if len(p) >= 3 and p[0].lstrip(".").startswith("?AV?$TClassFactory"):
        return "TClassFactory<%s>" % p[1]
    return m
if __name__ == "__main__":
    for t in (".?AV?$TClassFactory@VFactoryClass@@@@", ".?AV?$TClassFactory@VParticleSystemTypeClass@@@@", ".?AVFactoryClass@@"):
        print(t, "->", name_pretty(t))
