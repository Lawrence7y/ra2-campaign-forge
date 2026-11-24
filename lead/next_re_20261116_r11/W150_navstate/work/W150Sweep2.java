// W150 part 2: screen-stack array, mode 1/2/5 screen dialogs, and the unresolved
// front-end code region 0x5EF2A0..0x5EFF80 that writes mode 1/2.
// @category W150
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W150Sweep2 extends GhidraScript {

    Address addr(long v) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);
    }

    String fnTag(Function f) {
        if (f == null) return "-";
        return String.format("%08x(sz=%d)", f.getEntryPoint().getOffset(), f.getBody().getNumAddresses());
    }

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // ---- PART A: every instruction that mentions the screen array / its count ----
        long[] arr = { 0x00A83C9CL, 0x00A83CA8L, 0x00A83D4CL, 0x00A8DB30L, 0x00A8B24CL,
                       0x00A8B230L, 0x00887048L, 0x00887640L };
        println("### PARTA ARRAY/STATE GLOBAL REFS (full instruction text)");
        for (long g : arr) {
            Address a = addr(g);
            println(String.format("### AG %08x", g));
            ReferenceIterator it = rm.getReferencesTo(a);
            TreeSet<String> lines = new TreeSet<>();
            while (it.hasNext()) {
                Reference r = it.next();
                Instruction ins = getInstructionContaining(r.getFromAddress());
                if (ins == null) continue;
                Function cf = fm.getFunctionContaining(r.getFromAddress());
                lines.add(String.format("AG|%08x|%s|%08x|%s|%s", g,
                        r.getFromAddress().toString(),
                        cf == null ? 0L : cf.getEntryPoint().getOffset(),
                        r.getReferenceType().isWrite() ? "W" : "R",
                        ins.toString().replace('\t', ' ')));
            }
            println("### AG " + String.format("%08x", g) + " n=" + lines.size());
            for (String s : lines) println(s);
        }

        // ---- PART B: which function owns 0x5EF2A0..0x5EFF80, and its strings ----
        println("### PARTB REGION 0x5EF2A0..0x5EFF80");
        for (long probe = 0x5EF2A0L; probe < 0x5EF420L; probe += 0x10) {
            Instruction i = getInstructionAt(addr(probe));
            Function f = fm.getFunctionContaining(addr(probe));
            println(String.format("PB|%08x|fn=%s|%s", probe, fnTag(f),
                    i == null ? "<no insn>" : i.toString()));
        }
        // string refs anywhere in 0x5EF2A0..0x5EFF80
        println("### PARTB STRINGS in region");
        TreeSet<String> seen = new TreeSet<>();
        for (long va = 0x5EF2A0L; va < 0x5EFF80L; va++) {
            Instruction ins = getInstructionAt(addr(va));
            if (ins == null) continue;
            for (Reference r : ins.getReferencesFrom()) {
                Address to = r.getToAddress();
                if (to == null) continue;
                Data d = getDataAt(to);
                if (d == null || !d.hasStringValue()) continue;
                Object v = d.getValue();
                if (v == null) continue;
                String s = v.toString();
                boolean ok = s.length() >= 4;
                for (int k = 0; ok && k < s.length(); k++) {
                    char c = s.charAt(k);
                    if (c < 0x20 || c > 0x7E) ok = false;
                }
                if (!ok) continue;
                seen.add(String.format("PBSTR|%08x|%s", ins.getAddress().getOffset(), s));
            }
        }
        for (String s : seen) println(s);
        println("### PARTB nstrings=" + seen.size());

        // ---- PART C: the screen dialog functions of mode 1/2/5 ----
        long[] dec = { 0x5113F0L, 0x512760L, 0x512680L, 0x5117D0L,
                       0x5B49B0L, 0x5B77E0L, 0x6AE2C0L,
                       0x55CFD0L, 0x48D080L, 0x48CFD0L,
                       0x6851F0L, 0x67E440L, 0x531CC0L };
        println("### PARTC DECOMPILED");
        for (long d : dec) {
            Function f = fm.getFunctionContaining(addr(d));
            if (f == null) { println("### no fn at " + d); continue; }
            println("### DEC " + String.format("%08x", f.getEntryPoint().getOffset())
                    + " size=" + f.getBody().getNumAddresses());
            DecompileResults res = di.decompileFunction(f, 90, monitor);
            if (res == null || !res.decompileCompleted()) { println("   (failed)"); continue; }
            for (String s : res.getDecompiledFunction().getC().split("\n")) println("C| " + s);
            println("### ENDDEC");
        }
        println("### ALLDONE2");
    }
}
