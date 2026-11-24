"""W178-PATCH: per-site patch-design facts extraction from core.json (no binary re-read)."""
import json, os, re
ROOT=r"D:\Project\ra2-campaign-forge"
CORE=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH","EVIDENCE","core.json")
core=json.load(open(CORE,encoding='utf-8'))

print("=== ATLAS-HOLE GAP VERIFICATION ===")
for s,n in core['gap_verification'].items(): print(s,n)

print("\n=== SITES: push / nop / this-load / call-bytes / host / reach ===")
for r in core['sites']:
    if 'error' in r: print(r['site'],'ERROR',r['error']); continue
    pushes=';'.join(p['text'] for p in r['pushes_before']) or '-'
    runs=';'.join(f"{x['va']:#x}x{x['length']}{x['byte']}" for x in r['nop_runs']) or '-'
    src=r['ecx_source'].split(' @')[0]
    print(f"{r['site']} host={r['fn']}({r['fn_size']}) src={r['fn_source']:28s} "
          f"reach={int(r['reachable'])} path={r['path_len']:3d} grade={r['host_grade']:14s} "
          f"push={pushes[:60]:60s} nop={runs:35s} this={src:40s} bytes={r['call_bytes']}")

print("\n=== SITES with NO push in 10 insns before call ===")
for r in core['sites']:
    if 'error' in r: continue
    if not r['pushes_before']:
        print("=== ",r['site'],"host",r['fn'])
        for x in r['prev']: print("   ",x)

print("\n=== SITES with nop run >=2 bytes ===")
for r in core['sites']:
    if 'error' in r: continue
    big=[x for x in r['nop_runs'] if x['length']>=2]
    if big:
        print("=== ",r['site'],"host",r['fn'],big)
        for x in r['prev']: print("   ",x)

print("\n=== 0x6CD8CD ===")
s6=core['s6']
for k in ('site','fn','fn_size','boundary','eax_source','ecx_source','reachable','path_len','jump_table','callers','dword_count','crash_va','crash_insn'):
    print(f"  {k}={s6[k]}")
print("  prev:")
for x in s6['prev']: print("   ",x)
print("  branches:")
for b in s6['branches'][:12]: print("   ",b['text'],'->',[hex(t) for t in b['targets']])

print("\n=== GLOBAL NULL writers ===")
for g,p in core['globals'].items():
    print(" ",g,"writes",len(p['mem_writes']),"imm_loads",len(p['imm_loads']))
    for w in p['mem_writes']: print("    ",w['text'])
    for e in p['writers']: print("       fn",e['writer_fn'],"callers",[hex(x) for x in e['callers'][:8]])
