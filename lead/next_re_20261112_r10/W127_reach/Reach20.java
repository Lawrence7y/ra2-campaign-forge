// W127: static reachability of the 20 no-NULL-check call sites of FUN_00724730
// @category W127
//
// Goal: for each of the 20 "mov ecx,[0x887368]; call 0x724730" sites (ledger §821-2),
// determine the enclosing function and whether it is reachable from the interactive
// message pump / the known crash entry FUN_004fc0b0.
//
// Method (deliberately semantics-free, no heuristics):
//   1. build the complete call graph from Ghidra references (call + cross-function jump)
//   2. find anchors: functions referencing PeekMessageA / GetMessageA / DispatchMessageA,
//      plus the known crash entry 0x004fc0b0
//   3. forward-BFS from anchors -> reachable function set + depth
//   4. upward-BFS from each site's enclosing function -> shortest path to a root
//   5. classify roots by whether the entry address is stored as a dword in .rdata/.data
//      (i.e. reachable only through a vtable / function pointer)

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class Reach20 extends GhidraScript {

    // load sites and their call addresses, ledger §821-2 (already re-verified by capstone)
    static final long[] LOADS = {
        0x00654405L, 0x006ABFF4L, 0x006AC031L, 0x006D0613L, 0x006D0629L,
        0x006D0659L, 0x006D0896L, 0x006D08A8L, 0x006D0935L, 0x006D09ECL,
        0x006D127CL, 0x006D12F1L, 0x006D1367L, 0x006D13DCL, 0x006D153AL,
        0x006D1551L, 0x006D15FAL, 0x006D1627L, 0x006D16BBL, 0x006D16D2L
    };
    static final long[] CALLS = {
        0x00654413L, 0x006AC00BL, 0x006AC03EL, 0x006D0619L, 0x006D0634L,
        0x006D0664L, 0x006D089DL, 0x006D08B3L, 0x006D0940L, 0x006D09FAL,
        0x006D1293L, 0x006D1308L, 0x006D137EL, 0x006D13F3L, 0x006D1541L,
        0x006D155CL, 0x006D1605L, 0x006D1632L, 0x006D16C2L, 0x006D16DDL
    };
    static final long FUN_DEL   = 0x00724730L;
    static final long CRASH_ENTRY = 0x004FC0B0L;

    FunctionManager fm;
    Map<Long, Set<Long>> up   = new HashMap<>();  // callee -> callers
    Map<Long, Set<Long>> down = new HashMap<>();  // caller -> callees
    Set<Long> funcPtrSet = new HashSet<>();       // entries stored as dwords in data

    Address addr(long va) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
    }

    long keyOf(Function f) {
        return f == null ? -1L : f.getEntryPoint().getOffset();
    }

    String nm(long k) {
        return "FUN_" + String.format("%08x", k);
    }

    void addEdge(long a, long b) {
        if (a < 0 || b < 0 || a == b) return;
        down.computeIfAbsent(a, x -> new HashSet<>()).add(b);
        up.computeIfAbsent(b, x -> new HashSet<>()).add(a);
    }

    // ---- 1. call graph ----------------------------------------------------
    void buildGraph() {
        Listing lst = currentProgram.getListing();
        int insnCount = 0, callEdges = 0, jmpEdges = 0;
        InstructionIterator it = lst.getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            insnCount++;
            for (Reference r : ins.getReferencesFrom()) {
                boolean isCall = r.getReferenceType().isCall();
                boolean isJmp  = r.getReferenceType().isJump();
                if (!isCall && !isJmp) continue;
                Address to = r.getToAddress();
                Function ft = fm.getFunctionAt(to);
                if (ft == null) ft = fm.getFunctionContaining(to);
                if (ft == null) continue;                       // import / external
                Function ff = fm.getFunctionContaining(ins.getAddress());
                if (ff == null) continue;
                long a = keyOf(ff), b = keyOf(ft);
                if (a == b) continue;                            // intra-function
                addEdge(a, b);
                if (isCall) callEdges++; else jmpEdges++;
            }
        }
        println("### GRAPH instructions=" + insnCount + " callEdges=" + callEdges
                + " xfuncJumpEdges=" + jmpEdges + " nodes=" + fm.getFunctionCount());
    }

    // ---- 2. function pointers stored in data (vtable slots etc.) ----------
    void buildFuncPtrs() {
        Memory mem = currentProgram.getMemory();
        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String n = blk.getName();
            if (!n.equals(".rdata") && !n.equals(".data")) continue;
            long start = blk.getStart().getOffset();
            long sz = blk.getSize();
            for (long off = 0; off + 4 <= sz; off += 4) {
                Address a = addr(start + off);
                long v;
                try { v = mem.getInt(a) & 0xffffffffL; } catch (Exception e) { continue; }
                if (v < 0x00401000L || v > 0x00900000L) continue;
                if ((v & 3) != 0) continue;
                Function f = fm.getFunctionAt(addr(v));
                if (f != null) funcPtrSet.add(v);
            }
        }
        println("### FUNCPTR entries stored in .rdata/.data: " + funcPtrSet.size());
    }

    // ---- 3. anchors ------------------------------------------------------
    Set<Long> findAnchorFunctions(String[] externals) {
        Set<Long> out = new LinkedHashSet<>();
        SymbolTable st = currentProgram.getSymbolTable();
        ReferenceManager rm = currentProgram.getReferenceManager();
        for (SymbolIterator si = st.getAllSymbols(true); si.hasNext(); ) {
            Symbol s = si.next();
            String name = s.getName();
            boolean match = false;
            for (String e : externals) if (e.equalsIgnoreCase(name)) match = true;
            if (!match) continue;
            Address ea = s.getAddress();
            if (!ea.isExternalAddress()) continue;
            for (Reference r : rm.getReferencesTo(ea)) {
                Function cf = fm.getFunctionContaining(r.getFromAddress());
                if (cf != null) out.add(keyOf(cf));
            }
        }
        return out;
    }

    // ---- 4. forward BFS from a root set --------------------------------
    Map<Long, Integer> forwardBfs(Set<Long> roots, int maxDepth) {
        Map<Long, Integer> dist = new LinkedHashMap<>();
        ArrayDeque<Long> q = new ArrayDeque<>();
        for (Long r : roots) { if (dist.put(r, 0) == null) q.add(r); }
        while (!q.isEmpty()) {
            Long cur = q.poll();
            int d = dist.get(cur);
            if (d >= maxDepth) continue;
            Set<Long> cs = down.get(cur);
            if (cs == null) continue;
            for (Long c : cs) {
                if (!dist.containsKey(c)) { dist.put(c, d + 1); q.add(c); }
            }
        }
        return dist;
    }

    // ---- 5. shortest upward path to a root -----------------------------
    void upReport(long seed, int maxDepth) {
        Map<Long, Long> parent = new HashMap<>();
        Map<Long, Integer> dist = new HashMap<>();
        ArrayDeque<Long> q = new ArrayDeque<>();
        parent.put(seed, null); dist.put(seed, 0); q.add(seed);
        Long bestRoot = null;
        List<Long> roots = new ArrayList<>();
        int maxDist = 0;
        while (!q.isEmpty()) {
            Long cur = q.poll();
            int d = dist.get(cur);
            maxDist = Math.max(maxDist, d);
            Set<Long> ps = up.get(cur);
            if (ps == null || ps.isEmpty()) { roots.add(cur); if (bestRoot == null) bestRoot = cur; continue; }
            if (d >= maxDepth) { roots.add(cur); continue; }
            for (Long p : ps) {
                if (!dist.containsKey(p)) { dist.put(p, d + 1); parent.put(p, cur); q.add(p); }
            }
        }
        if (bestRoot == null) { println("    UP: (no root reached within depth)"); return; }
        ArrayDeque<String> chain = new ArrayDeque<>();
        Long c = bestRoot;
        while (c != null) {
            Function f = fm.getFunctionAt(addr(c));
            String tag = (f == null) ? "" : (" size=" + f.getBody().getNumAddresses());
            boolean vta = funcPtrSet.contains(c);
            chain.addFirst(nm(c) + (vta ? "[fnptr]" : "") + tag);
            c = parent.get(c);
        }
        println("    UP shortest: " + String.join("  <-  ", chain) + "   (rootDepth)");
        println("    UP roots reached: " + roots.size() + "  maxUpDepth=" + maxDist);
        for (Long r : roots) {
            if (r.equals(bestRoot)) continue;
            Function f = fm.getFunctionAt(addr(r));
            println("       alt root " + nm(r) + " size=" + (f == null ? -1 : f.getBody().getNumAddresses())
                    + (funcPtrSet.contains(r) ? " [fnptr]" : ""));
        }
    }

    void directCallers(long k, int cap) {
        Set<Long> ps = up.get(k);
        if (ps == null || ps.isEmpty()) { println("    DIRECT callers: (none)"); return; }
        StringBuilder sb = new StringBuilder();
        int n = 0;
        for (Long p : ps) {
            if (n++ >= cap) { sb.append(" ..."); break; }
            sb.append(nm(p)).append(funcPtrSet.contains(p) ? "[fnptr]" : "").append(" ");
        }
        println("    DIRECT callers (" + ps.size() + "): " + sb);
    }

    public void run() throws Exception {
        fm = currentProgram.getFunctionManager();
        buildGraph();
        buildFuncPtrs();

        // anchors
        Set<Long> pump = findAnchorFunctions(new String[]{"PeekMessageA", "GetMessageA",
                "DispatchMessageA", "TranslateMessage"});
        Set<Long> regclass = findAnchorFunctions(new String[]{"RegisterClassA", "RegisterClassExA",
                "CreateWindowExA"});
        println("### ANCHOR pump(idle/msg loop)   = " + pump.size() + " " + pump);
        println("### ANCHOR window-class/create   = " + regclass.size() + " " + regclass);
        println("### ANCHOR crash entry "+nm(CRASH_ENTRY)+" exists="
                + (fm.getFunctionAt(addr(CRASH_ENTRY)) != null));

        Set<Long> allAnchors = new LinkedHashSet<>(pump);
        allAnchors.addAll(regclass);
        allAnchors.add(CRASH_ENTRY);

        Map<Long, Integer> fwdFromPump  = forwardBfs(pump, 40);
        Map<Long, Integer> fwdFromAll   = forwardBfs(allAnchors, 40);
        Map<Long, Integer> fwdFromCrash = forwardBfs(new HashSet<>(Arrays.asList(CRASH_ENTRY)), 40);
        println("### FWD reachable from pump      : " + fwdFromPump.size());
        println("### FWD reachable from allAnchor : " + fwdFromAll.size());
        println("### FWD reachable from crashEntry: " + fwdFromCrash.size());

        println("");
        println("### SITES ###");
        Set<Long> distinct = new LinkedHashSet<>();
        for (int i = 0; i < LOADS.length; i++) {
            Function f = fm.getFunctionContaining(addr(CALLS[i]));
            long k = keyOf(f);
            distinct.add(k);
            String pos = (k >= 0 && k <= CALLS[i]) ? ("+" + Long.toHexString(CALLS[i] - k)) : "?";
            println("--- site#" + (i + 1) + " load=0x" + Long.toHexString(LOADS[i])
                    + " call=0x" + Long.toHexString(CALLS[i])
                    + "  FN=" + (k < 0 ? "<none>" : nm(k)) + " off=" + pos
                    + (f != null ? " size=" + f.getBody().getNumAddresses() : ""));
            if (k < 0) continue;
            directCallers(k, 12);
            Integer dp = fwdFromPump.get(k), da = fwdFromAll.get(k), dc = fwdFromCrash.get(k);
            println("    REACH from pump=" + (dp == null ? "NO" : ("YES d=" + dp))
                    + "  from allAnchor=" + (da == null ? "NO" : ("YES d=" + da))
                    + "  from crashEntry=" + (dc == null ? "NO" : ("YES d=" + dc)));
            upReport(k, 12);
        }
        println("");
        println("### DISTINCT enclosing functions: " + distinct.size() + " " + distinct);
    }
}
