// W108 · Is 0x0047BBF0 a SECOND unlink function?  It writes both +0xE4 (0x47bc82) and
// +0xE8 (0x47bc88), which is exactly the unlink shape.  If it is, question (A) must be
// re-asked against ITS call sites, not only against 0x0047EA90.

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;

public class Unlink2 extends GhidraScript {
    Address addr(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    static String hex(long v) { return String.format("0x%08X", v); }

    void writeFile(String name, String c) throws IOException {
        File dir = new File(System.getenv("W108_EVID"));
        if (dir == null || !dir.exists())
            dir = new File("D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r10\\W108_travinv\\EVIDENCE");
        File f = new File(dir, name);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(f), "UTF-8")) { w.write(c); }
        println("wrote " + f.getAbsolutePath() + " (" + c.length() + " chars)");
    }

    String decompile(long va) {
        Function f = currentProgram.getFunctionManager().getFunctionContaining(addr(va));
        if (f == null) return "// no fn";
        DecompInterface dec = new DecompInterface();
        dec.toggleCCode(true);
        dec.openProgram(currentProgram);
        DecompileResults dr = dec.decompileFunction(f, 150, monitor);
        String b = (dr != null && dr.decompileCompleted()) ? dr.getDecompiledFunction().getC() : "// FAILED";
        dec.dispose();
        return "//////////////// " + hex(f.getEntryPoint().getOffset()) + "\n" + b;
    }

    void listing(StringBuilder sb, long a, long b) {
        sb.append("\n--- instructions ").append(hex(a)).append("..").append(hex(b)).append(" ---\n");
        for (long va = a; va < b; ) {
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
    }

    void xrefs(StringBuilder sb, long target, String label) {
        sb.append("\n=== call sites of ").append(label).append(" ").append(hex(target)).append(" ===\n");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(addr(target));
        FunctionManager fm = currentProgram.getFunctionManager();
        int n = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Function f = fm.getFunctionContaining(r.getFromAddress());
            sb.append("  call@").append(r.getFromAddress()).append("  in ")
              .append(f == null ? "?" : hex(f.getEntryPoint().getOffset())).append("\n");
            n++;
        }
        sb.append("  total = ").append(n).append("\n");
    }

    @Override
    public void run() throws Exception {
        StringBuilder sb = new StringBuilder();

        sb.append("=== 0x0047BBF0 (writes +0xE4 @0x47bc82 AND +0xE8 @0x47bc88) ===\n");
        sb.append(decompile(0x0047BBF0L));
        listing(sb, 0x0047BBF0L, 0x0047BD00L);

        sb.append("\n=== 0x0047BB60 (writes +0xE4 @0x47bba7) ===\n");
        listing(sb, 0x0047BB60L, 0x0047BBF0L);

        xrefs(sb, 0x0047BBF0L, "0x0047BBF0");
        xrefs(sb, 0x0047BB60L, "0x0047BB60");

        writeFile("step20_unlink2.txt", sb.toString());
    }
}
