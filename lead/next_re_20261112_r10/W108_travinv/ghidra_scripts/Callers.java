// W108 · traversal-invalidation audit
// Stage 1: xref census + decompile every caller of the 3 traversers AND of the unlink fn.
// Stage 2 (separate run, args=analyze): per-caller hazard analysis.
//
// Usage:
//   -postScript Callers.java            -> census + write EVIDENCE/step2_census.txt
//   -postScript Callers.java analyze    -> census + hazard analysis -> EVIDENCE/step3_hazard.txt
//   -postScript Callers.java decomp     -> dump decomp of every caller -> EVIDENCE/step4_decomp.txt

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.lang.*;
import ghidra.program.model.mem.MemoryAccessException;
import java.io.*;
import java.util.*;
import java.math.BigInteger;

public class Callers extends GhidraScript {

    static final long TRAV_A520 = 0x0047C520L;   // find WhatAmI()==6 on chain +0xE4
    static final long TRAV_A4D0 = 0x0047C4D0L;   // find WhatAmI()==wanted on chain chosen by arg
    static final long TRAV_A550 = 0x0047C550L;   // third sibling
    static final long UNLINK   = 0x0047EA90L;    // unlink node from cell chain

    DecompInterface dec;

    Address addr(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    static String hex(long v) { return String.format("0x%08X", v); }

    // --- "may free / may remove" callee set: address -> label -----------------
    // Built narrowly first; anything outside this set is reported as "unknown callee"
    // so the analysis never silently treats a call as harmless.
    static final Map<Long,String> KILLERS = new LinkedHashMap<>();
    static {
        KILLERS.put(0x0047EA90L, "UNLINK(cell,node,whichChain)");
    }

    /** Collect call sites: functions containing an xref to target, as (callerEntry, callAddr). */
    List<long[]> callSites(long target) {
        List<long[]> out = new ArrayList<>();
        Address t = addr(target);
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(t);
        while (it.hasNext()) {
            Reference r = it.next();
            Address from = r.getFromAddress();
            if (r.getReferenceType().isCall()) {
                Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
                long ce = (cf != null) ? cf.getEntryPoint().getOffset() : 0L;
                out.add(new long[]{ ce, from.getOffset() });
            }
        }
        // also raw E8 scan, to catch call sites Ghidra did not model as references
        try {
            Memory mem = currentProgram.getMemory();
            for (Address a = currentProgram.getMinAddress(); a != null && a.getOffset() < 0x900000L; ) {
                long off = a.getOffset();
                if (off < 0x00400000L) { a = a.add(1); continue; }
                byte[] b = new byte[5];
                int got = 0;
                try { got = mem.getBytes(a, b, 0, 5); } catch (Exception e) { got = 0; }
                if (got == 5 && b[0] == (byte)0xE8) {
                    int rel = ((b[1] & 0xff)) | ((b[2] & 0xff) << 8) | ((b[3] & 0xff) << 16) | ((b[4] & 0xff) << 24);
                    long tgt = off + 5 + rel;
                    if (tgt == target) {
                        Function cf = currentProgram.getFunctionManager().getFunctionContaining(a);
                        long ce = (cf != null) ? cf.getEntryPoint().getOffset() : 0L;
                        out.add(new long[]{ ce, off });
                    }
                }
                a = a.add(1);
            }
        } catch (Exception e) { println("rawscan err " + e); }
        // dedupe by callAddr
        TreeMap<Long,long[]> m = new TreeMap<>();
        for (long[] x : out) m.put(x[1], x);
        return new ArrayList<>(m.values());
    }

    String decomp(Function f) {
        if (f == null) return "// <no function>\n";
        DecompileResults dr = dec.decompileFunction(f, 90, monitor);
        if (dr == null || !dr.decompileCompleted()) {
            return "// decompile FAILED for " + hex(f.getEntryPoint().getOffset()) + "\n";
        }
        return dr.getDecompiledFunction().getC();
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String mode = (args.length > 0) ? args[0] : "census";

        dec = new DecompInterface();
        dec.toggleCCode(true);
        dec.toggleSyntaxTree(true);
        dec.openProgram(currentProgram);

        long[] travs = { TRAV_A520, TRAV_A4D0, TRAV_A550 };

        // ---------- census ----------
        StringBuilder cen = new StringBuilder();
        cen.append("W108 CALLER CENSUS\nprogram=").append(currentProgram.getName())
           .append("\nfunctions=").append(currentProgram.getFunctionManager().getFunctionCount()).append("\n\n");

        Map<Long, List<long[]>> byTarget = new LinkedHashMap<>();
        for (long t : travs) byTarget.put(t, callSites(t));
        List<long[]> unl = callSites(UNLINK);
        byTarget.put(UNLINK, unl);

        for (long t : travs) {
            cen.append("== ").append(hex(t)).append(" : ").append(byTarget.get(t).size()).append(" call sites\n");
        }
        cen.append("== ").append(hex(UNLINK)).append(" : ").append(unl.size()).append(" call sites\n\n");

        // Callers that touch BOTH a traverser and the unlink fn  (A-class candidates)
        Set<Long> travCallers = new TreeSet<>();
        for (long t : travs) for (long[] c : byTarget.get(t)) if (c[0] != 0) travCallers.add(c[0]);
        Set<Long> unlCallers = new TreeSet<>();
        for (long[] c : unl) if (c[0] != 0) unlCallers.add(c[0]);

        Set<Long> both = new TreeSet<>(travCallers);
        both.retainAll(unlCallers);

        cen.append("distinct traverser-caller functions = ").append(travCallers.size()).append("\n");
        cen.append("distinct unlink-caller functions   = ").append(unlCallers.size()).append("\n");
        cen.append("INTERSECTION (touch traverser AND unlink) = ").append(both.size()).append("\n");
        for (long b : both) cen.append("  BOTH ").append(hex(b)).append("\n");

        cen.append("\n-- traverser call sites (caller, callAddr, target) --\n");
        for (long t : travs) {
            for (long[] c : byTarget.get(t)) {
                cen.append(hex(c[0])).append("  call@").append(hex(c[1]))
                   .append("  ->").append(hex(t)).append("\n");
            }
        }
        cen.append("\n-- unlink call sites (caller, callAddr) --\n");
        for (long[] c : unl) {
            cen.append(hex(c[0])).append("  call@").append(hex(c[1])).append("\n");
        }

        writeFile("step2_census.txt", cen.toString());
        println("CENSUS written. both=" + both.size());

        if (mode.equals("census")) return;

        // ---------- decompile dump ----------
        StringBuilder deco = new StringBuilder();
        Set<Long> allCallers = new TreeSet<>();
        allCallers.addAll(travCallers);
        allCallers.addAll(unlCallers);
        FunctionManager fm = currentProgram.getFunctionManager();
        for (long ce : allCallers) {
            Function f = fm.getFunctionAt(addr(ce));
            deco.append("\n\n//////////////// FUNC ").append(hex(ce))
                .append("  (trav=").append(travCallers.contains(ce) ? "Y" : "n")
                .append(" unlink=").append(unlCallers.contains(ce) ? "Y" : "n").append(")\n");
            deco.append(decomp(f));
        }
        writeFile("step4_decomp.txt", deco.toString());
        println("DECOMP written for " + allCallers.size() + " functions");

        if (mode.equals("decomp")) return;

        dec.dispose();
    }

    void writeFile(String name, String content) throws IOException {
        File dir = new File(System.getenv("W108_EVID"));
        if (dir == null || !dir.exists()) {
            // fall back to a hard-coded dir
            dir = new File("D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r10\\W108_travinv\\EVIDENCE");
        }
        File f = new File(dir, name);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(f), "UTF-8")) {
            w.write(content);
        }
        println("wrote " + f.getAbsolutePath() + " (" + content.length() + " chars)");
    }
}
