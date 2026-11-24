// W164: disassemble around [EAX+0x5C] calls in Unit/Infantry AI + frame-throttle region in FootClass AI
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class W164_LocoCall extends GhidraScript {
    void dump(long s, long e, String title) throws Exception {
        AddressFactory af=currentProgram.getAddressFactory();
        Address st=af.getDefaultAddressSpace().getAddress(s), en=af.getDefaultAddressSpace().getAddress(e);
        println("=== "+title+" ===");
        InstructionIterator ii=currentProgram.getListing().getInstructions(new AddressSet(st,en),true);
        while(ii.hasNext()){Instruction ins=ii.next(); println("  "+ins.getAddress()+": "+ins.toString());}
    }
    public void run() throws Exception {
        dump(0x007361D0L,0x00736230L,"Unit AI around CALL [EAX+0x5C] @0x736210");
        dump(0x0051BB40L,0x0051BB90L,"Infantry AI around CALL [EAX+0x5C] @0x51BB7A");
        dump(0x004DA530L,0x004DA5A0L,"FootClass AI entry (gate + throttle)");
    }
}
