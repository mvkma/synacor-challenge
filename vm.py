from enum import IntEnum
from collections import namedtuple
import struct
import sys

SIZE = 2**15

class OpCode(IntEnum):
    HALT =  0
    SET  =  1
    PUSH =  2
    POP  =  3
    EQ   =  4
    GT   =  5
    JMP  =  6
    JT   =  7
    JF   =  8
    ADD  =  9
    MULT = 10
    MOD  = 11
    AND  = 12
    OR   = 13
    NOT  = 14
    RMEM = 15
    WMEM = 16
    CALL = 17
    RET  = 18
    OUT  = 19
    IN   = 20
    NOOP = 21

OpCodeArguments = {
    OpCode.HALT: 0,
    OpCode.RET:  0,
    OpCode.NOOP: 0,
    OpCode.PUSH: 1,
    OpCode.POP:  1,
    OpCode.JMP:  1,
    OpCode.CALL: 1,
    OpCode.OUT:  1,
    OpCode.IN:   1,
    OpCode.SET:  2,
    OpCode.JT:   2,
    OpCode.JF:   2,
    OpCode.NOT:  2,
    OpCode.RMEM: 2,
    OpCode.WMEM: 2,
    OpCode.EQ:   3,
    OpCode.GT:   3,
    OpCode.ADD:  3,
    OpCode.MULT: 3,
    OpCode.MOD:  3,
    OpCode.AND:  3,
    OpCode.OR:   3,
}

class VirtualMachineStatus(IntEnum):
    FINISHED        = 0
    RUNNING         = 1
    EXPECTING_INPUT = 2

VMState = namedtuple("VMState", ["program", "registers", "stack", "pos", "status"])

class VirtualMachine:
    def __init__(self, program, stdin=sys.stdin, stdout=sys.stdout, break_on_input=False):
        self.program = program
        self.registers = [0] * 8
        self.stack = []
        self.pos = 0

        self.input_buffer = ""
        self.output_buffer = ""
        self.stdin = stdin
        self.stdout = stdout
        self.ncycles = 0

        self.break_on_input = break_on_input
        self.status = VirtualMachineStatus.RUNNING

    def __repr__(self):
        return f"VM(pos={self.pos})"

    @classmethod
    def from_binary(cls, fname):
        with open(fname, "rb") as f:
            buf = f.read()

        program = [b[0] for b in struct.iter_unpack("<H", buf)]

        return VirtualMachine(program)

    @classmethod
    def from_state(cls, state):
        VM = VirtualMachine(list(state.program))
        VM.registers = list(state.registers)
        VM.stack = list(state.stack)
        VM.pos = state.pos
        VM.status = state.status

        return VM

    def get_state(self):
        memory = tuple(self.program)
        registers = tuple(self.registers)
        stack = tuple(self.stack)

        return VMState(memory, registers, stack, self.pos, self.status)

    def read_instruction(self):
        op = self.program[self.pos]
        nargs = OpCodeArguments[op]

        args = self.program[self.pos + 1 : self.pos + 1 + nargs]

        self.pos += nargs + 1

        return op, args

    def get_value(self, n):
        if n < SIZE:
            return n
        else:
            return self.registers[n % SIZE]

    def step(self):
        op, args = self.read_instruction()

        if op == OpCode.HALT:
            self.status = VirtualMachineStatus.FINISHED
            return False

        if len(self.output_buffer) > 0 and self.output_buffer[-1] == "\n":
            print(self.output_buffer, end="", file=self.stdout)
            self.output_buffer = ""

        match op:
            case OpCode.SET:
                self.registers[args[0] % SIZE] = self.get_value(args[1])

            case OpCode.PUSH:
                self.stack.append(self.get_value(args[0]))

            case OpCode.POP:
                self.registers[args[0] % SIZE] = self.stack.pop()

            case OpCode.EQ:
                if self.get_value(args[1]) == self.get_value(args[2]):
                    self.registers[args[0] % SIZE] = 1
                else:
                    self.registers[args[0] % SIZE] = 0

            case OpCode.GT:
                if self.get_value(args[1]) > self.get_value(args[2]):
                    self.registers[args[0] % SIZE] = 1
                else:
                    self.registers[args[0] % SIZE] = 0

            case OpCode.JMP:
                self.pos = self.get_value(args[0])

            case OpCode.JT:
                if self.get_value(args[0]) != 0:
                    self.pos = self.get_value(args[1])

            case OpCode.JF:
                if self.get_value(args[0]) == 0:
                    self.pos = self.get_value(args[1])

            case OpCode.ADD:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % SIZE] = (b + c) % SIZE

            case OpCode.MULT:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % SIZE] = (b * c) % SIZE

            case OpCode.MOD:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % SIZE] = (b % c)

            case OpCode.AND:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % SIZE] = b & c

            case OpCode.OR:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % SIZE] = b | c

            case OpCode.NOT:
                self.registers[args[0] % SIZE] = SIZE + (~self.get_value(args[1]))

            case OpCode.RMEM:
                self.registers[args[0] % SIZE] = self.program[self.get_value(args[1])]

            case OpCode.WMEM:
                self.program[self.get_value(args[0])] = self.get_value(args[1])

            case OpCode.CALL:
                self.stack.append(self.pos)
                self.pos = self.get_value(args[0])

            case OpCode.RET:
                if len(self.stack) == 0:
                    return False
                self.pos = self.stack.pop()

            case OpCode.OUT:
                self.output_buffer += chr(self.get_value(args[0]))

            case OpCode.IN:
                if len(self.input_buffer) == 0:

                    if self.break_on_input:
                        self.pos -= 2
                        self.status = VirtualMachineStatus.EXPECTING_INPUT
                        return False

                    self.input_buffer = self.stdin.readline()

                self.registers[args[0] % SIZE] = ord(self.input_buffer[0])
                self.input_buffer = self.input_buffer[1:]

            case OpCode.NOOP:
                pass

            case _:
                raise ValueError(f"Unknown instruction: {op}")

        self.ncycles += 1

        return True

    def run(self):
        self.status = VirtualMachineStatus.RUNNING

        running = self.step()

        while running:
            running = self.step()

        return running

VM = VirtualMachine.from_binary("challenge.bin")
