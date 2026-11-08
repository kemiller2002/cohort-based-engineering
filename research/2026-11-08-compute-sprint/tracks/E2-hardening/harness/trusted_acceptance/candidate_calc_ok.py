"""Correct candidate program (black-box CLI): calc.py add|mul A B ; calc.py rev TEXT."""
import sys


def main(argv):
    if len(argv) == 3 and argv[0] in ("add", "mul"):
        try:
            a, b = int(argv[1]), int(argv[2])
        except ValueError:
            print("not an integer", file=sys.stderr)
            return 2
        print(a + b if argv[0] == "add" else a * b)
        return 0
    if len(argv) == 2 and argv[0] == "rev":
        print(argv[1][::-1])
        return 0
    print("usage: calc.py add|mul A B | rev TEXT", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
