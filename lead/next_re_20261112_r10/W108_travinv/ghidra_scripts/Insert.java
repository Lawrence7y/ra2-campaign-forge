// W108 · Insertion side of the cell chain: FUN_0047E8A0 writes BOTH +0xE4 and +0xE8.
// Decompile it and its callers so we can say which head a node can land on, and
// therefore whether UNLINK's whichChain argument (always obj+0x8C) can ever disagree.

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.util.*;

public class Insert extends GhidraScript {
    Address addr(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    static String hex(long v) { return String.format("0x%08X", v); }

    void writeFile(String name, String content) throws IOException {
        File dir = new File(System.getenv("W108_EVID"));
        if (dir == null || !dir.exists())
            dir = new File("D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r10\\W108_travinv\\EVIDENCE");
        File f = new File(dir, name);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(f), "UTF-8")) { w.write(content); }
        println("wrote " + f.getAbsolutePath() + " (" + content.length() + " chars)");
    }

    String decompile(long va) {
        Function f = currentProgram.getFunctionManager().getFunctionContaining(addr(va));
        if (f == null) return "// no fn at " + hex(va) + "\n";
        DecompInterface dec = new DecompInterface();
        dec.toggleCCode(true);
        dec.openProgram(currentProgram);
        DecompileResults dr = dec.decompileFunction(f, 150, monitor);
        String body = (dr != null && dr.decompileCompleted())
                ? dr.getDecompiledFunction().getC() : "// DECOMPILE FAILED " + hex(va) + "\n";
        dec.dispose();
        return "//////////////// " + hex(f.getEntryPoint().getOffset()) + " " + f.getName() + "\n" + body;
    }

    @Override
    public void run() throws Exception {
        StringBuilder sb = new StringBuilder();

        sb.append("=== insertion fn 0x0047E8A0 (writes BOTH +0xE4 at 0x0047e91f and +0xE8 at 0x0047e90b) ===\n");
        sb.append(decompile(0x0047E8A0L)).append("\n");

        // who calls the inserter
        sb.append("\n=== call sites of 0x0047E8A0 ===\n");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(addr(0x0047E8A0L));
        FunctionManager fm = currentProgram.getFunctionManager();
        int n = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Address from = r.getFromAddress();
            Function f = fm.getFunctionContaining(from);
            sb.append("  call@").append(from).append("  in ")
              .append(f == null ? "?" : hex(f.getEntryPoint().getOffset())).append("\n");
            n++;
        }
        sb.append("  total = ").append(n).append("\n");

        // instruction listing of the inserter region (to read the chain selection)
        sb.append("\n=== instruction listing 0x0047E8A0 .. 0x0047E950 ===\n");
        for (long va = 0x0047E8A0L; va < 0x0047E950L; ) {
            Instruction ins = currentProgram.getListing().getInstructionAt(addr(va));
            if (ins == null) {
                Instruction nx = currentProgram.getListing().getInstructionAfter(addr(va));
                if (nx == null) break;
                va = nx.getAddress().getOffset();
                continue;
            }
            sb.append(ins.getAddress()).append("  ").append(ins.toString()).append("\n");
            va = ins.getAddress().add(ins.getLength()).getOffset();
        }

        writeFile("step19_insert.txt", sb.toString());
    }
}
