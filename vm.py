import struct

class VirtualMachine:
    def __init__(self, program):
        self.program = program

        self.registers = [0] * 8
        self.stack = []

        self.pos = 0

    def __repr__(self):
        return f"VM(pos={self.pos})"

    @classmethod
    def from_binary(self, fname):
        with open(fname, "rb") as f:
            buf = f.read()

        program = [b[0] for b in struct.iter_unpack("<H", buf)]

        return VirtualMachine(program)

    def read_instruction(self):
        op = self.program[self.pos]

        match op:
            case 0 | 18 | 21: nargs = 0
            case 2 | 3 | 6 | 17 | 19 | 20: nargs = 1
            case 1 | 7 | 8 | 14 | 15 | 16: nargs = 2
            case 4 | 5 | 9 | 10 | 11 | 12 | 13: nargs = 3
            case _: raise ValueError(f"Unknown instruction: {op}")

        args = self.program[self.pos + 1 : self.pos + 1 + nargs]

        self.pos += nargs + 1

        return op, args

    def get_value(self, n):
        if n < 2**15:
            return n
        else:
            return self.registers[n % 2**15]

    def step(self):
        op, args = self.read_instruction()

        if op == 0:
            return False

        match op:
            case 1:
                self.registers[args[0] % 2**15] = self.get_value(args[1])
            case 2:
                self.stack.append(self.get_value(args[0]))
            case 3:
                self.registers[args[0] % 2**15] = self.stack.pop()
            case 4:
                if self.get_value(args[1]) == self.get_value(args[2]):
                    self.registers[args[0] % 2**15] = 1
                else:
                    self.registers[args[0] % 2**15] = 0
            case 5:
                if self.get_value(args[1]) > self.get_value(args[2]):
                    self.registers[args[0] % 2**15] = 1
                else:
                    self.registers[args[0] % 2**15] = 0
            case 6:
                self.pos = self.get_value(args[0])
            case 7:
                if self.get_value(args[0]) != 0:
                    self.pos = self.get_value(args[1])
            case 8:
                if self.get_value(args[0]) == 0:
                    self.pos = self.get_value(args[1])
            case 9:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % 2**15] = (b + c) % 2**15
            case 10:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % 2**15] = (b * c) % 2**15
            case 11:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % 2**15] = (b % c)
            case 12:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % 2**15] = b & c
            case 13:
                b = self.get_value(args[1])
                c = self.get_value(args[2])
                self.registers[args[0] % 2**15] = b | c
            case 14:
                self.registers[args[0] % 2**15] = 2**15 + (~self.get_value(args[1]))
            case 15:
                self.registers[args[0] % 2**15] = self.program[self.get_value(args[1])]
            case 16:
                self.program[self.get_value(args[0])] = self.get_value(args[1])
            case 17:
                self.stack.append(self.pos)
                self.pos = self.get_value(args[0])
            case 18:
                if len(self.stack) == 0:
                    return False
                self.pos = self.stack.pop()
            case 19:
                # TODO: buffer output
                print(chr(self.get_value(args[0])), end="")
            case 21:
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
