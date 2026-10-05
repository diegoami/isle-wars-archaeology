// T26 (U32): the counts and addresses `tools/static/ghidra_import.py` records from a Ghidra project.
//
// Run by `analyzeHeadless ... -postScript T26Report.java <report file> [<needle>...]`. It writes a
// plain report of numbers, addresses and function names to the file named by the first argument,
// which is in the machine-local static folder, never in a checkout. It prints no instruction, no
// disassembly and no decompiled code: only what a record may hold (rule 18).
//
// For each needle (text) it lists where the bytes occur in the program, the references Ghidra found
// to that address, and the instructions that carry the string's 16-bit offset as an immediate (a
// real-mode program names a string by its offset in a data segment, which Ghidra does not always
// turn into a reference), each with the function that holds it.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class T26Report extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            throw new IllegalArgumentException("the first argument is the report file");
        }
        try (PrintWriter out = new PrintWriter(args[0], "UTF-8")) {
            Memory memory = currentProgram.getMemory();
            int instructions = 0;
            InstructionIterator all = currentProgram.getListing().getInstructions(true);
            while (all.hasNext()) {
                all.next();
                instructions++;
            }
            out.println("language=" + currentProgram.getLanguageID());
            out.println("compiler_spec=" + currentProgram.getCompilerSpec().getCompilerSpecID());
            out.println("format=" + currentProgram.getExecutableFormat());
            out.println("functions=" + currentProgram.getFunctionManager().getFunctionCount());
            out.println("instructions=" + instructions);
            out.println("memory_blocks=" + memory.getBlocks().length);
            for (MemoryBlock block : memory.getBlocks()) {
                out.println("block " + block.getName() + " " + block.getStart() + " " + block.getSize());
            }
            for (int i = 1; i < args.length; i++) {
                needle(out, memory, args[i]);
            }
        }
    }

    private void needle(PrintWriter out, Memory memory, String text) throws Exception {
        byte[] bytes = text.getBytes(StandardCharsets.US_ASCII);
        byte[] mask = new byte[bytes.length];
        for (int i = 0; i < mask.length; i++) {
            mask[i] = (byte) 0xFF;
        }
        List<Address> hits = new ArrayList<>();
        Address from = memory.getMinAddress();
        while (from != null) {
            Address hit = memory.findBytes(from, bytes, mask, true, monitor);
            if (hit == null) {
                break;
            }
            hits.add(hit);
            from = hit.next();
        }
        out.println("needle " + text + " hits=" + hits.size());
        for (Address hit : hits) {
            out.println("  at " + hit + " offset=0x" + Long.toHexString(hit.getOffset() & 0xFFFF));
            for (Reference ref : getReferencesTo(hit)) {
                Function f = getFunctionContaining(ref.getFromAddress());
                out.println("    reference from " + ref.getFromAddress() + " in "
                        + (f == null ? "no function" : f.getName() + " at " + f.getEntryPoint()));
            }
            long wanted = hit.getOffset() & 0xFFFF;
            InstructionIterator it = currentProgram.getListing().getInstructions(true);
            while (it.hasNext()) {
                Instruction insn = it.next();
                for (int op = 0; op < insn.getNumOperands(); op++) {
                    Scalar scalar = insn.getScalar(op);
                    if (scalar != null && scalar.getUnsignedValue() == wanted) {
                        Function f = getFunctionContaining(insn.getAddress());
                        out.println("    immediate in " + insn.getAddress() + " in "
                                + (f == null ? "no function" : f.getName() + " at " + f.getEntryPoint()));
                    }
                }
            }
        }
    }
}
