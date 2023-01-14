from enum import IntEnum
from collections import namedtuple
import readline
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

VMState = namedtuple("VMState", ["program", "registers", "stack", "pos"])

class VirtualMachine:
    def __init__(self, program, stdin=sys.stdin, stdout=sys.stdout):
        self.program = program
        self.registers = [0] * 8
        self.stack = []
        self.pos = 0

        self.input_buffer = ""
        self.output_buffer = ""
        self.stdin = stdin
        self.stdout = stdout

    def __repr__(self):
        return f"VM(pos={self.pos})"

    @classmethod
    def from_binary(self, fname):
        with open(fname, "rb") as f:
            buf = f.read()

        program = [b[0] for b in struct.iter_unpack("<H", buf)]

        return VirtualMachine(program)

    @classmethod
    def from_state(self, state):
        VM = VirtualMachine(list(state.program))
        VM.registers = list(state.registers)
        VM.stack = list(state.stack)
        VM.pos = state.pos

        return VM

    def get_state(self):
        memory = tuple(self.program)
        registers = tuple(self.registers)
        stack = tuple(self.stack)

        return VMState(memory, registers, stack, self.pos)

    def read_instruction(self):
        op = self.program[self.pos]

        match op:
            case OpCode.HALT | OpCode.RET | OpCode.NOOP:
                nargs = 0
            case OpCode.PUSH | OpCode.POP | OpCode.JMP | OpCode.CALL | OpCode.OUT | OpCode.IN:
                nargs = 1
            case OpCode.SET | OpCode.JT | OpCode.JF | OpCode.NOT | OpCode.RMEM | OpCode.WMEM:
                nargs = 2
            case OpCode.EQ | OpCode.GT | OpCode.ADD | OpCode.MULT | OpCode.MOD | OpCode.AND | OpCode.OR:
                nargs = 3
            case _:
                raise ValueError(f"Unknown instruction: {op}")

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
            return False

        if len(self.output_buffer) > 0 and op != OpCode.OUT:
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
                    self.input_buffer = self.stdin.readline()

                self.registers[args[0] % SIZE] = ord(self.input_buffer[0])
                self.input_buffer = self.input_buffer[1:]

            case OpCode.NOOP:
                pass

            case _:
                raise ValueError(f"Unknown instruction: {op}")

        return True

    def run(self):
        running = self.step()

        while running:
            running = self.step()

        return running

VM = VirtualMachine.from_binary("challenge.bin")
