import io

from rich.table import Table, Column

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Footer, TextLog, Static, Label

from vm import VirtualMachine, VMState, OpCode, OpCodeArguments

OPCODE_NAMES = [str(c).split(".")[1] for c in OpCode]

class VMStatus(Static):
    pos = reactive(0)
    registers = reactive([])
    stack = reactive([])

    def render(self) -> str:
        table = Table.grid()
        table.add_column(width=20)
        table.add_column()
        table.add_row("Position", str(self.pos))
        table.add_row("Stack", str(self.stack))
        table.add_row("Registers", str(self.registers))
        return table

class VMDebugger(App):

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "step", "Step"),
    ]

    def __init__(self, vm: VirtualMachine):
        super().__init__()

        self.vm = vm

        self.output_buffer = io.StringIO()
        self.vm.stdout = self.output_buffer

    def compose(self) -> ComposeResult:
        yield Header()
        yield VMStatus()
        yield Footer()

    def action_quit(self) -> None:
        self.exit()

    def action_step(self) -> None:
        self.vm.step()
        status_widget = self.query_one(VMStatus)
        status_widget.pos = self.vm.pos
        status_widget.registers = self.vm.registers
        status_widget.stack = self.vm.stack
        pass


if __name__ == "__main__":
    VM = VirtualMachine.from_binary("challenge.bin")
    VMD = VMDebugger(VM)
    VMD.run()
