import time
import urwid

from vm import VirtualMachine

class InputBuffer():
    def __init__(self, input_widget):
        self.input_widget = input_widget

    def readline(self):
        self.input_widget.focus()

class OutputBuffer(urwid.ListWalker):
    def __init__(self):
        self.lines = []
        self.focus = 0

    def get_focus(self):
        return self._get_line_at(self.focus)

    def set_focus(self, focus):
        self.focus = focus
        self._modified()

    def get_next(self, pos: int):
        return self._get_line_at(pos + 1)

    def get_prev(self, pos: int):
        return self._get_line_at(pos - 1)

    def _get_line_at(self, pos: int):
        if pos < 0 or len(self.lines) == 0:
            return None, None

        if pos < len(self.lines):
            return self.lines[pos], pos

        return self.lines[-1], pos

    def write(self, data: str):
        new_lines = data.splitlines()
        for l in new_lines:
            text = urwid.Text(l)
            self.lines.append(text)

        self._modified()

def main(vm):
    div = urwid.Divider()

    header = urwid.LineBox(urwid.Text("Debugger"))

    position_text = urwid.Text(f"Position: {vm.pos}")
    registers_text = urwid.Text(f"Registers: {vm.registers}")
    stack_text = urwid.Text(f"Stack: {vm.stack}")
    nsteps_text = urwid.Text(f"Steps: {vm.nsteps}")
    status_widget = urwid.LineBox(
        urwid.Pile([position_text, registers_text, stack_text, nsteps_text]),
        title="Status"
    )

    output_walker = OutputBuffer()
    output_widget = urwid.ListBox(output_walker)
    output_widget_box = urwid.LineBox(output_widget, title="Output")

    input_widget = urwid.Edit("")
    input_widget_box = urwid.LineBox(input_widget, title="Input")

    status_line = urwid.Text("")
    status_line_box = urwid.LineBox(status_line)

    button_quit = urwid.Button("(q)uit")
    button_step = urwid.Button("(s)tep")
    button_run = urwid.Button("(r)un")
    footer = urwid.LineBox(
        urwid.Columns([button_quit, div, button_step, div, button_run])
    )

    pile = urwid.Pile([
        header,
        status_widget,
        (30, output_widget_box),
        input_widget_box,
        status_line_box,
        footer,
    ])
    top = urwid.Filler(pile, valign="top")

    def update_status():
        position_text.set_text(f"Position: {vm.pos}")
        registers_text.set_text(f"Registers: {vm.registers}")
        stack_text.set_text(f"Stack: {vm.stack}")
        nsteps_text.set_text(f"Steps: {vm.nsteps}")

        loop.draw_screen()

    def vm_step():
        running = vm.step()
        update_status()

    def vm_run():
        running = vm.step()
        while running:
            running = vm.step()
            if vm.nsteps % 100 == 0:
                update_status()

            if vm.nsteps > 750000:
                break

    def show_or_exit(key):
        match key:
            case "q":
                raise urwid.ExitMainLoop()
            case "s":
                vm_step()
            case "r":
                vm_run()
            case _:
                status_line.set_text(f"You pressed: {repr(key)}")

    loop = urwid.MainLoop(top, unhandled_input=show_or_exit)
    loop.screen.set_terminal_properties(colors=256)

    vm.stdout = output_walker

    loop.run()

if __name__ == "__main__":
    VM = VirtualMachine.from_binary("challenge.bin")
    main(VM)
