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

        match op:
            case 0:
                return False
            case 19:
                # TODO: buffer output
                print(chr(self.get_value(args[0])), end="")
                return True
            case 21:
                 return True
            case _:
                 raise ValueError(f"Unknown instruction: {op}")

    def run(self):
        running = self.step()

        while running:
            running = self.step()

        return running
