import io
import itertools

from vm import VirtualMachine

steps = [
    "take tablet",
    "use tablet",
    "doorway",
    "north",
    "north",
    "bridge",
    "continue",
    "down",
    "east",
    "take empty lantern",
    "west",
    "west",
    "passage",
    "ladder",
    "west",
    "south",
    "north",
    "take can",
    "use can",
    "use lantern",
    "west",
    "ladder",
    "darkness",
    "continue",
    "west",
    "west",
    "west",
    "west",
]

steps_ruin = [
    # enter ruin
    "north",
    "take red coin",
    "north",
    # puzzle: _ + _ * _^2 + _^3 - _ = 399
    "east",
    "take concave coin",
    "down",
    "take corroded coin",
    "up",
    "west",
    # back at the puzzle
    "west",
    "take blue coin",
    "up",
    "take shiny coin",
    "down",
    "east",
    "inv",
    # back at the puzzle
    "use blue coin",
    "use red coin",
    "use shiny coin",
    "use concave coin",
    "use corroded coin",
    "north",
    "take teleporter",
    "use teleporter",
    "take business card",
    "take strange book",
]

COINS = ["use red coin", "use corroded coin", "use shiny coin", "use concave coin", "use blue coin"]

def solve_puzzle():
    outcomes = {}

    def kill():
        raise EOFError

    for coins in itertools.permutations(COINS):
        VM = VirtualMachine.from_binary("challenge.bin")

        input_buf = InputBuffer(steps + list(coins), callback=kill)
        output_buf = io.StringIO()

        VM.stdin = input_buf
        VM.stdout = output_buf

        try:
            VM.run()
        except EOFError:
            res = output_buf.getvalue()
            print(coins)
            print(res.splitlines()[-5:])
            outcomes[coins] = res
            continue

    return [k for k, v in outcomes.items() if v.splitlines()[-3].find("you hear") > 0][0]

class InputBuffer():
    def __init__(self, values, callback=input):
        self.values = iter(values)
        self.callback = callback

    def readline(self):
        try:
            val = next(self.values)
        except StopIteration:
            val = self.callback()

        return val + "\n"

if __name__ == "__main__":
    VM = VirtualMachine.from_binary("challenge.bin")

    input_buf = InputBuffer(steps + steps_ruin)
    VM.stdin = input_buf

    VM.run()
