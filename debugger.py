import urwid
from typing import Tuple

from vm import VirtualMachine, VirtualMachineStatus

SCREEN_UPDATE_INTERVAL = 100

class OutputBuffer(urwid.ListWalker):
    def __init__(self):
        self.lines = [urwid.Text("")]
        self.focus = 0

    def __len__(self) -> int:
        return len(self.lines)

    def get_focus(self) -> Tuple[urwid.Edit, int] | Tuple[None, None]:
        return self._get_line_at(self.focus)

    def set_focus(self, focus: int) -> None:
        self.focus = focus
        self._modified()

    def get_next(self, pos: int) -> Tuple[urwid.Edit, int] | Tuple[None, None]:
        return self._get_line_at(pos + 1)

    def get_prev(self, pos: int) -> Tuple[urwid.Edit, int] | Tuple[None, None]:
        return self._get_line_at(pos - 1)

    def _get_line_at(self, pos: int) -> Tuple[urwid.Edit, int] | Tuple[None, None]:
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

        self.header = urwid.LineBox(urwid.Text("Debugger"))

        # Status widget
        self.text_position = urwid.Text(f"Position: {vm.pos}")
        self.text_registers = urwid.Text(f"Registers: {vm.registers}")
        self.text_stack = urwid.Text(f"Stack: {vm.stack}")
        self.text_ncycles = urwid.Text(f"Steps: {vm.ncycles}")
        self.text_vmstatus = urwid.Text(f"Status: {str(vm.status)}")
        self.status_widget = urwid.LineBox(
            urwid.Pile([
                self.text_position,
                self.text_registers,
                self.text_stack,
                self.text_ncycles,
                self.text_vmstatus,
            ]),
            title="Status"
        )

        # stdout
        output_walker = OutputBuffer()
        self.output_widget = urwid.ListBox(output_walker)

        # stdin
        self.input_widget = urwid.Edit("")

        # status line
        self.status_line = urwid.Text("")

        # footer
        self.footer = urwid.LineBox(
            urwid.Columns([
                urwid.Button("(q)uit"),
                urwid.Button("(s)tep"),
                urwid.Button("(r)un"),
            ])
        )

        self.main_pile = urwid.Pile([
            self.header,
            self.status_widget,
            (30, urwid.LineBox(self.output_widget, title="Output")),
            urwid.LineBox(self.input_widget, title="Input"),
            urwid.LineBox(self.status_line),
            self.footer,
        ])
        self.top = urwid.Filler(self.main_pile, valign="top")

        self.loop = urwid.MainLoop(self.top, unhandled_input=self.unhandled_input)
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
            case "enter":
                if self.main_pile.focus_position == 3 and self.vm.status != VirtualMachineStatus.FINISHED:
                    text = self.input_widget.get_edit_text() + "\n"
                    self.vm.input_buffer = text
                    self.main_pile.focus_position = 2
                    self.vm_run()
            case "esc":
                self.main_pile.focus_position = 2
            case _:
                self.status_line.set_text(f"You pressed: {repr(key)}")

    def vm_step(self) -> None:
        self.vm.step()
        self.update_status_widget()

    def vm_run(self) -> None:
        if self.vm.status == VirtualMachineStatus.FINISHED:
            return

        running = self.vm.step()
        while running:
            running = self.vm.step()

            if self.vm.ncycles % SCREEN_UPDATE_INTERVAL == 0:
                self.update_status_widget()

        self.update_status_widget()

        if self.vm.status == VirtualMachineStatus.EXPECTING_INPUT:
            self.input_widget.set_edit_text("")
            self.main_pile.focus_position = 3

    def update_status_widget(self, force_update : bool = True) -> None:
        self.text_position.set_text(f"Position: {self.vm.pos}")
        self.text_registers.set_text(f"Registers: {self.vm.registers}")
        self.text_stack.set_text(f"Stack: {self.vm.stack}")
        self.text_ncycles.set_text(f"Cycles: {self.vm.ncycles}")
        self.text_vmstatus.set_text(f"Status: {str(self.vm.status)}")

        self.output_widget.set_focus(len(self.output_widget.body))

        if force_update:
            self.loop.draw_screen()

if __name__ == "__main__":
    VM = VirtualMachine.from_binary("challenge.bin")
    VMD = VMDebugger(VM)
    VMD.loop.run()
