// Smoke test for R11 card projects: proves the copied project opens and the
// function manager / listing are intact. Prints counts + one known function.
//@category R11
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;

public class Smoke11 extends GhidraScript {
    @Override
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        int total = 0;
        for (Function f : fm.getFunctions(true)) { total++; }
        println("### program = " + currentProgram.getName());
        println("### imageBase = " + currentProgram.getImageBase());
        println("### funcTotal = " + total);
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x0055D360L);
        Function f = fm.getFunctionContaining(a);
        println("### fn@0x55D360 = " + (f == null ? "null" : f.getName() + " size=" + f.getBody().getNumAddresses()));
    }
}
