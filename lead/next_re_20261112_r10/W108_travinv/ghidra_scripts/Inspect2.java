// W108 · second pass: (a) disambiguate the -noanalysis decompile output, which showed
// two different offsets for the "map context" base (0x13c vs 0x3c) at the same
// instruction; (b) decompile 0x0047D2B0 (the "remove from cell" callee that follows
// the unlink call) so we know whether IT can free anything still referenced.

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;

public class Inspect2 extends GhidraScript {
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
        Function f = currentProgram.getFunctionManager().getFunctionAt(addr(va));
        if (f == null) f = currentProgram.getFunctionManager().getFunctionContaining(addr(va));
        if (f == null) return "// no function at " + hex(va) + "\n";
        DecompInterface dec = new DecompInterface();
        dec.toggleCCode(true);
        dec.openProgram(currentProgram);
        DecompileResults dr = dec.decompileFunction(f, 150, monitor);
        String body = (dr != null && dr.decompileCompleted())
                ? dr.getDecompiledFunction().getC()
                : "// DECOMPILE FAILED for " + hex(va) + "\n";
        dec.dispose();
        return "//////////////// " + hex(f.getEntryPoint().getOffset()) + "  " + f.getName()
               + "  body " + f.getBody().getMinAddress() + ".." + f.getBody().getMaxAddress() + "\n" + body;
    }

    @Override
    public void run() throws Exception {
        StringBuilder sb = new StringBuilder();

        sb.append("=== 0x0047D2B0 (called right after the unlink, with ecx=cell, push -1) ===\n");
        sb.append(decompile(0x0047D2B0L)).append("\n\n");

        sb.append("=== 0x0048DEE0 (first call in the function, sets up asStack_884 coordinate list) ===\n");
        sb.append(decompile(0x0048DEE0L)).append("\n\n");

        writeFile("step12_callees.txt", sb.toString());
    }
}
