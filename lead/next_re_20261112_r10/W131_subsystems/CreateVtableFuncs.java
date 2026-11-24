// W131: create functions at every vtable slot target that Ghidra left undefined.
// @category W131
//
// Why: 4,339 of the 6,256 distinct vtable slot targets are in undefined space
// (verified: zero are interiors of existing functions). A vtable slot is proof
// that the target is a function entry, so leaving them undefined makes the
// function atlas incomplete (it covered only 64% of .text bytes).
//
// Input: a text file with one hex VA per line (addresses already filtered to
// code-range and to those without a function).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.util.*;

public class CreateVtableFuncs extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) { println("usage: CreateVtableFuncs.java <addrlist.txt>"); return; }
        File in = new File(args[0]);
        if (!in.exists()) { println("missing " + in); return; }

        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace as = currentProgram.getAddressFactory().getDefaultAddressSpace();

        int total = 0, created = 0, existed = 0, failed = 0;
        List<String> fails = new ArrayList<>();
        BufferedReader br = new BufferedReader(new FileReader(in));
        String line;
        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            total++;
            long va;
            try { va = Long.parseLong(line.replace("0x", "").replace("0X", ""), 16); }
            catch (NumberFormatException e) { failed++; continue; }
            Address a = as.getAddress(va);
            if (a == null) { failed++; fails.add(line + ":no-address"); continue; }
            if (fm.getFunctionAt(a) != null) { existed++; continue; }
            try {
                // disassemble, then create the function
                disassemble(a);
                Function f = createFunction(a, null);
                if (f != null) created++;
                else { failed++; fails.add(line + ":createFunction-null"); }
            } catch (Exception e) {
                failed++;
                fails.add(line + ":" + e.getClass().getSimpleName());
            }
        }
        br.close();
        println("### CREATE total=" + total + " created=" + created
                + " existed=" + existed + " failed=" + failed);
        for (int i = 0; i < Math.min(fails.size(), 30); i++) println("   FAIL " + fails.get(i));
        println("### fnmanager now=" + fm.getFunctionCount());
    }
}
