import urwid
from typing import Tuple, List

from vm import VirtualMachine, VirtualMachineStatus, OpCode, OpCodeArguments

SCREEN_UPDATE_INTERVAL = 1000

OPCODE_NAMES = [str(op).split(".")[1] for op in OpCode]

PALETTE = [
    ("opcode", "light blue", "black", ()),
    ("args", "light green", "black", ()),
    ("pos", "yellow", "black", ()),
    ("brk", "light red", "black", ()),
    ("label", "dark gray", "black", ()),
]

NUM_PADDING = 6

def disassemble_next(vm: VirtualMachine, pos: int) -> Tuple[str, List[int], int]:
    op = vm.program[pos]
    nargs = OpCodeArguments[op]
    args = vm.program[pos + 1 : pos + 1 + nargs]

    return (OPCODE_NAMES[op], args, pos + nargs + 1)

def disassemble_prev(vm: VirtualMachine, pos: int) -> Tuple[str, List[int], int]:
    k = 1
    while vm.program[pos - k] not in range(22):
        k += 1

    pos = pos - k

    op = vm.program[pos]
    nargs = OpCodeArguments[op]
    args = vm.program[pos + 1 : pos + 1 + nargs]

    return (OPCODE_NAMES[op], args, pos)

def disassemble(vm: VirtualMachine) -> List[Tuple[int, int, List[int]]]:
    pos = 0
    asm = []
    while pos < len(vm.program):
        op = vm.program[pos]
        nargs = OpCodeArguments.get(op, 0)
        args = vm.program[pos + 1 : pos + 1 + nargs]
        asm.append((pos, op, args))
        pos += nargs + 1

    return asm

class DisassemblyWalker(urwid.ListWalker):
    def __init__(self, vm: VirtualMachine, breakpoints: set):
        self.vm = vm
        self.breakpoints = breakpoints

        self.asm = disassemble(self.vm)
        self.focus = 0
        self.reset()

    def reset(self) -> None:
        self.asm = disassemble(self.vm)

        i = 0
        for vmpos, _, _ in self.asm:
            if vmpos == self.vm.pos:
                break
            i += 1

        self.set_focus(max(0, i - 2))

    def get_focus(self) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(self.focus)

    def set_focus(self, focus: int) -> None:
        self.focus = focus
        self._modified()

    def get_next(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(pos + 1)

    def get_prev(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(pos - 1)

    def _get_line_at(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        if pos < 0 or pos >= len(self.asm) or len(self.asm) == 0:
            return None, None

        vmpos, opcode, args = self.asm[pos]
        if opcode in range(22):
            opcode = OPCODE_NAMES[opcode]

        mpos = ">" if vmpos == self.vm.pos else " "
        mbrk = "o" if vmpos in self.breakpoints else " "

        text = urwid.Text([("brk", mpos),
                           ("brk", mbrk),
                           " ",
                           ("pos", str(vmpos).rjust(NUM_PADDING)),
                           ("opcode", str(opcode).rjust(NUM_PADDING)),
                           ("args", "".join(str(a).rjust(NUM_PADDING) for a in args)),
                           ])

        return text, pos

class OutputBuffer(urwid.ListWalker):
    def __init__(self):
        self.lines = [urwid.Text("")]
        self.focus = 0

    def __len__(self) -> int:
        return len(self.lines)

    def get_focus(self) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(self.focus)

    def set_focus(self, focus: int) -> None:
        self.focus = focus
        self._modified()

    def get_next(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(pos + 1)

    def get_prev(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        return self._get_line_at(pos - 1)

    def _get_line_at(self, pos: int) -> Tuple[urwid.Text, int] | Tuple[None, None]:
        if pos < 0 or len(self.lines) == 0:
            return None, None

        if pos < len(self.lines):
            return self.lines[pos], pos

        return self.lines[-1], pos

    def write(self, data: str) -> None:
        final_newline = self.lines.pop()

        new_lines = data.splitlines()
        for l in new_lines:
            text = urwid.Text(l)
            self.lines.append(text)

        self.lines.append(final_newline)

        self._modified()

class VMDebugger():
    def __init__(self, vm: VirtualMachine):
        self.vm = vm
        self.breakpoints = set()

        # Status widget
        self.text_position = urwid.Text(f"Position: {vm.pos}")
        self.text_ncycles = urwid.Text(f"Steps: {vm.ncycles}")
        self.text_vmstatus = urwid.Text(f"Status: {str(vm.status)}")
        self.text_breakpoints = urwid.Text(f"Breakpoints: {str(self.breakpoints)}")
        self.status_widget = urwid.LineBox(
            urwid.Pile([
                self.text_position,
                self.text_ncycles,
                self.text_vmstatus,
                self.text_breakpoints,
            ]),
            title="Status"
        )

        # stdout
        output_walker = OutputBuffer()
        self.output_widget = urwid.ListBox(output_walker)

        # stdin
        self.input_widget = urwid.Edit("")

        # disassembly
        self.disassembly_walker = DisassemblyWalker(self.vm, self.breakpoints)
        self.disassembly_widget = urwid.ListBox(self.disassembly_walker)

        # breakpoint entry
        self.breakpoint_widget = urwid.IntEdit("")

        # registers
        self.registers_line = urwid.Text([str(val).rjust(NUM_PADDING) for val in vm.registers])
        self.registers_widget = urwid.Pile([
            urwid.Text([("label", str(n).rjust(NUM_PADDING)) for n in range(len(vm.registers))]),
            self.registers_line
        ])

        # stack
        self.stack_widget = urwid.Text("")

        # status line
        self.status_line = urwid.Text("")

        # help text
        self.help_text = urwid.Text([
            "Commands: ", "[q]uit", " | ", "[r]un", " | ", "[s]tep", " | ", "[b]reakpoint"
        ])

        self.main_pile = urwid.Pile([
            self.status_widget,
            urwid.LineBox(self.registers_widget, title="Registers"),
            urwid.LineBox(self.stack_widget, title="Stack"),
            (15, urwid.LineBox(self.output_widget, title="Output")),
            urwid.LineBox(self.input_widget, title="Input"),
            (15, urwid.LineBox(self.disassembly_widget, title="Disassembly")),
            urwid.LineBox(self.breakpoint_widget, title="Breakpoint"),
            urwid.LineBox(self.status_line),
            urwid.LineBox(self.help_text),
        ])

        self.pile_indices = {
            "status": 0,
            "registers": 1,
            "stack": 2,
            "output": 3,
            "input": 4,
            "disassembly": 5,
            "breakpoint_input": 6,
            "status": 7,
        }

        self.top = urwid.Filler(self.main_pile, valign="top")
        self.loop = urwid.MainLoop(self.top, PALETTE, unhandled_input=self.unhandled_input)
        self.loop.screen.set_terminal_properties(colors=256)

        self.vm.stdout = output_walker
        self.vm.break_on_input = True

        self.update_status_widget(force_update=False)

    def unhandled_input(self, key: str) -> None:
        self.status_line.set_text(f"You pressed: {repr(key)}")

        match key:
            case "q":
                raise urwid.ExitMainLoop()
            case "s":
                self.vm_step()
            case "r":
                self.vm_run()
            case "b":
                self.main_pile.focus_position = self.pile_indices["breakpoint_input"]
            case "enter":
                if (self.main_pile.focus_position == self.pile_indices["input"] and
                    self.vm.status != VirtualMachineStatus.FINISHED):
                    text = self.input_widget.get_edit_text() + "\n"
                    self.vm.input_buffer = text
                    self.main_pile.focus_position = self.pile_indices["output"]
                    # self.vm_run()
                    self.vm_step()
                elif self.main_pile.focus_position == self.pile_indices["breakpoint_input"]:
                    pt = self.breakpoint_widget.value()
                    if pt in self.breakpoints:
                        self.breakpoints.remove(pt)
                    else:
                        self.breakpoints.add(pt)
                    self.update_status_widget()
            case "esc":
                self.main_pile.focus_position = self.pile_indices["output"]
            case _:
                self.status_line.set_text(f"You pressed: {repr(key)}")

    def vm_step(self) -> None:
        self.vm.step()
        self.update_status_widget()

    def vm_run(self) -> None:
        if self.vm.status == VirtualMachineStatus.FINISHED:
            return

        running = self.vm.step()
        while running and self.vm.pos not in self.breakpoints:
            running = self.vm.step()

            if self.vm.ncycles % SCREEN_UPDATE_INTERVAL == 0:
                self.update_status_widget()

        self.update_status_widget()

        if self.vm.status == VirtualMachineStatus.EXPECTING_INPUT:
            self.input_widget.set_edit_text("")
            self.main_pile.focus_position = self.pile_indices["input"]

    def update_status_widget(self, force_update : bool = True) -> None:
        self.text_position.set_text(["Position: ", ("pos", f"{self.vm.pos}")])
        self.text_ncycles.set_text(f"Cycles: {self.vm.ncycles}")
        self.text_vmstatus.set_text(f"Status: {str(self.vm.status)}")
        self.text_breakpoints.set_text(["Breakpoints: ", ("brk", f"{str(self.breakpoints)}")])

        self.registers_line.set_text([str(val).rjust(NUM_PADDING) for val in self.vm.registers])

        if len(self.vm.stack) > 0:
            self.stack_widget.set_text([str(val).rjust(NUM_PADDING) for val in self.vm.stack])
        else:
            self.stack_widget.set_text("")

        self.disassembly_walker.reset()
        self.disassembly_widget.set_focus_valign("top")

        self.output_widget.set_focus(len(self.output_widget.body))

        if force_update:
            self.loop.draw_screen()

if __name__ == "__main__":
    VM = VirtualMachine.from_binary("challenge.bin")
    VMD = VMDebugger(VM)
    VMD.loop.run()

    # 885 CALL 1723 [843, 1, 30000, 0, 0, 0, 0, 0] [887]

    # 1739 CALL  2125
    # 1741  SET 32769 16724
    # 1744 CALL  2125
    # ...
    # JF 32768 1730

    # 1766 RET [843, 1, 30000, 0, 0, 0, 0, 0] []

