// W150: navigation/mode state census.
//   PART1  all refs (R/W) to a watchlist of game-state globals, with instruction text
//          and a disassembly context window around every WRITE.
//   PART2  aggregate census of WRITE refs and READ refs to every global in
//          [0xA70000,0xB90000), keyed by (global, containing function).
//   PART3  jump table dump for the 0x6474C7 mode dispatch.
//   PART4  decompiled C for a fixed list of functions.
// @category W150
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W150Sweep extends GhidraScript {

    final long[] WATCH = {
        0x00A8B238L, // "G_GAMEMODE" 0..5 mode selector
        0x00A8B230L, // "G_GAMELOGIC" big singleton pointer
        0x00A83D48L, // skip-frame-advance flag
        0x00A8D5F8L, // option flags (-ATTRACT bit 2)
        0x00A8ED84L, // logic frame counter
        0x00A8ED80L, // focus flag
        0x00A8E9A0L, // "G_INGAME" candidate
        0x00A8EDD8L, // exit state
        0x00AA0430L, // message pump counter
        0x00B73550L, // hwnd
        0x00B07784L, // target frame
        0x00B04880L  // -MPDEBUG flag
    };

    Address addr(long v) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);
    }

    String fnTag(Function f) {
        if (f == null) return "-";
        return String.format("%08x(sz=%d)", f.getEntryPoint().getOffset(), f.getBody().getNumAddresses());
    }

    String ctx(long center, int before, int after) {
        StringBuilder sb = new StringBuilder();
        Address a = addr(center);
        Instruction i = getInstructionAt(a);
        if (i == null) i = getInstructionContaining(a);
        if (i == null) return "   <no insn>";
        // walk back
        List<Instruction> back = new ArrayList<>();
        Instruction cur = i;
        for (int k = 0; k < before; k++) {
            Instruction p = getInstructionBefore(cur.getAddress());
            if (p == null) break;
            back.add(0, p);
            cur = p;
        }
        for (Instruction p : back) sb.append("   ctx| ").append(p.toString()).append("\n");
        sb.append("   CTX> ").append(i.toString()).append("\n");
        Instruction n = i;
        for (int k = 0; k < after; k++) {
            Instruction q = getInstructionAfter(n.getAddress());
            if (q == null) break;
            sb.append("   ctx| ").append(q.toString()).append("\n");
            n = q;
        }
        return sb.toString();
    }

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        println("### IMAGEBASE " + currentProgram.getImageBase());
        println("### FUNCTIONS " + fm.getFunctionCount());

        // ---------------- PART 1 ----------------
        println("### PART1 WATCHLIST REFS");
        for (long w : WATCH) {
            Address a = addr(w);
            int total = 0, nw = 0, nr = 0;
            ReferenceIterator it = rm.getReferencesTo(a);
            List<String> lines = new ArrayList<>();
            List<Long> writeSites = new ArrayList<>();
            while (it.hasNext()) {
                Reference r = it.next();
                Address from = r.getFromAddress();
                Instruction ins = getInstructionContaining(from);
                if (ins == null) continue;
                total++;
                boolean isW = r.getReferenceType().isWrite();
                if (isW) { nw++; writeSites.add(from.getOffset()); } else nr++;
                Function cf = fm.getFunctionContaining(from);
                lines.add(String.format("P1|%s|%08x|%08x|%s|%s|%s",
                        String.format("%08x", w), from.getOffset(),
                        cf == null ? 0L : cf.getEntryPoint().getOffset(),
                        isW ? "W" : "R",
                        r.getReferenceType().toString(),
                        ins.toString().replace('\t', ' ')));
            }
            Collections.sort(lines);
            println(String.format("### G %08x total=%d write=%d read=%d", w, total, nw, nr));
            for (String s : lines) println(s);
            // context windows around each write site
            for (Long ws : writeSites) {
                Function cf = fm.getFunctionContaining(addr(ws));
                println(String.format("P1WCTX|%08x|%08x|fn=%s", w, ws, fnTag(cf)));
                print(ctx(ws, 6, 10));
            }
        }

        // ---------------- PART 2 ----------------
        println("### PART2 GLOBAL CENSUS over [0xA70000,0xB90000)");
        long lo = 0xA70000L, hi = 0xB90000L;
        TreeMap<Long, TreeMap<Long, Integer>> wr = new TreeMap<>();
        TreeMap<Long, TreeMap<Long, Integer>> rd = new TreeMap<>();
        InstructionIterator iit = currentProgram.getListing().getInstructions(true);
        long ninsn = 0;
        while (iit.hasNext()) {
            Instruction ins = iit.next();
            ninsn++;
            Reference[] refs = ins.getReferencesFrom();
            if (refs.length == 0) continue;
            for (Reference r : refs) {
                Address to = r.getToAddress();
                if (to == null) continue;
                long t = to.getOffset();
                if (t < lo || t >= hi) continue;
                Function cf = fm.getFunctionContaining(ins.getAddress());
                long fe = cf == null ? 0L : cf.getEntryPoint().getOffset();
                boolean isW = r.getReferenceType().isWrite();
                TreeMap<Long, TreeMap<Long, Integer>> m = isW ? wr : rd;
                if (!m.containsKey(t)) m.put(t, new TreeMap<>());
                TreeMap<Long, Integer> f = m.get(t);
                f.put(fe, f.getOrDefault(fe, 0) + 1);
            }
        }
        println("### PART2 insns scanned = " + ninsn);
        for (Map.Entry<Long, TreeMap<Long, Integer>> e : wr.entrySet()) {
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<Long, Integer> f : e.getValue().entrySet())
                sb.append(String.format(" %08x:%d", f.getKey(), f.getValue()));
            println(String.format("P2W|%08x|nfn=%d|%s", e.getKey(), e.getValue().size(), sb.toString()));
        }
        for (Map.Entry<Long, TreeMap<Long, Integer>> e : rd.entrySet()) {
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<Long, Integer> f : e.getValue().entrySet())
                sb.append(String.format(" %08x:%d", f.getKey(), f.getValue()));
            println(String.format("P2R|%08x|nfn=%d|%s", e.getKey(), e.getValue().size(), sb.toString()));
        }

        // ---------------- PART 2b ----------------
        // every WRITE to a global in range where the stored value is an IMMEDIATE scalar.
        // This is the "which globals are enum/state variables" table: a global that only
        // ever receives a handful of distinct small constants is a state variable.
        println("### PART2b IMMEDIATE-VALUE WRITES to globals in [0xA70000,0xB90000)");
        InstructionIterator i2 = currentProgram.getListing().getInstructions(true);
        while (i2.hasNext()) {
            Instruction ins = i2.next();
            Reference[] refs = ins.getReferencesFrom();
            if (refs.length == 0) continue;
            for (Reference r : refs) {
                if (!r.getReferenceType().isWrite()) continue;
                Address to = r.getToAddress();
                if (to == null) continue;
                long t = to.getOffset();
                if (t < lo || t >= hi) continue;
                // immediate operand?  walk op objects looking for a small Scalar
                String imm = null;
                for (int oi = 0; oi < ins.getNumOperands(); oi++) {
                    Object[] oo = ins.getOpObjects(oi);
                    for (Object o : oo) {
                        if (o instanceof ghidra.program.model.scalar.Scalar) {
                            ghidra.program.model.scalar.Scalar sc = (ghidra.program.model.scalar.Scalar) o;
                            if (sc.getUnsignedValue() < 0x1000L) {
                                imm = String.format("0x%x", sc.getUnsignedValue());
                            }
                        }
                    }
                }
                if (imm == null) continue;
                Function cf = fm.getFunctionContaining(ins.getAddress());
                println(String.format("P2BI|%08x|%s|%08x|%s|%s", t, imm,
                        cf == null ? 0L : cf.getEntryPoint().getOffset(),
                        ins.getAddress().toString(),
                        ins.toString().replace('\t', ' ')));
            }
        }

        // ---------------- PART 2c ----------------
        // vtable identity xrefs: who mentions GScreenClass / GraphicMenu / ProgressScreen vtables
        println("### PART2c VTABLE XREFS (GScreenClass 0x7EA6FC, GraphicMenu 0x7EA5FC, ProgressScreen 0x7F0064)");
        long[] vts = { 0x007EA6FCL, 0x007EA5FCL, 0x007F0064L, 0x007EA604L, 0x007EA690L };
        for (long vt : vts) {
            Address va = addr(vt);
            ReferenceIterator vit = rm.getReferencesTo(va);
            int n = 0;
            println(String.format("### VT %08x", vt));
            while (vit.hasNext()) {
                Reference r = vit.next();
                n++;
                Instruction ins = getInstructionContaining(r.getFromAddress());
                Function cf = fm.getFunctionContaining(r.getFromAddress());
                println(String.format("P2CV|%08x|%08x|fn=%s|%s|%s", vt, r.getFromAddress().getOffset(),
                        fnTag(cf),
                        r.getReferenceType().toString(),
                        ins == null ? "?" : ins.toString().replace('\t', ' ')));
            }
            println(String.format("### VT %08x nrefs=%d", vt, n));
        }

        // ---------------- PART 3 ----------------
        println("### PART3 MODE DISPATCH JUMP TABLE @0x6475D8");
        for (int k = 0; k < 8; k++) {
            Address ea = addr(0x6475D8L + 4L * k);
            try {
                int v = getInt(ea);
                println(String.format("  jt[%d] @%08x = %08x", k, ea.getOffset(), v));
            } catch (Exception ex) {
                println("  jt[" + k + "] unreadable " + ex);
            }
        }

        // ---------------- PART 4 ----------------
        println("### PART4 DECOMPILED C");
        long[] dec = { 0x647260L, 0x48CCC0L, 0x52D9A0L };
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long d : dec) {
            Function f = fm.getFunctionContaining(addr(d));
            if (f == null) { println("### no fn at " + d); continue; }
            println("### DECOMP " + String.format("%08x", f.getEntryPoint().getOffset())
                    + " size=" + f.getBody().getNumAddresses());
            DecompileResults res = di.decompileFunction(f, 120, monitor);
            if (res == null || !res.decompileCompleted()) { println("   (failed)"); continue; }
            String[] ls = res.getDecompiledFunction().getC().split("\n");
            for (String s : ls) println("C| " + s);
            println("### ENDDECOMP");
        }
        // also decompile every function that writes 0xA8B238 more than once, or that is a
        // writer we have not seen: emit full C for writers of the mode selector.
        println("### PART4b WRITERS OF 0xA8B238 (decompiled)");
        Address modeA = addr(0x00A8B238L);
        LinkedHashSet<Long> writers = new LinkedHashSet<>();
        ReferenceIterator mit = rm.getReferencesTo(modeA);
        while (mit.hasNext()) {
            Reference r = mit.next();
            if (!r.getReferenceType().isWrite()) continue;
            Function cf = fm.getFunctionContaining(r.getFromAddress());
            if (cf != null) writers.add(cf.getEntryPoint().getOffset());
        }
        println("### writers distinct = " + writers.size());
        for (Long w : writers) {
            Function f = fm.getFunctionAt(addr(w.longValue()));
            if (f == null) continue;
            println("### DECOMPW " + String.format("%08x", w) + " size=" + f.getBody().getNumAddresses());
            DecompileResults res = di.decompileFunction(f, 90, monitor);
            if (res == null || !res.decompileCompleted()) { println("   (failed)"); continue; }
            String[] ls = res.getDecompiledFunction().getC().split("\n");
            for (String s : ls) println("W| " + s);
            println("### ENDDECOMPW");
        }
        println("### ALLDONE");
    }
}
