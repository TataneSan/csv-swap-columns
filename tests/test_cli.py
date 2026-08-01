import io
import json
import sys
import unittest
from contextlib import redirect_stdout

from csv_swap_columns import cli


def run(argv, stdin_text):
    old = sys.stdin
    sys.stdin = io.StringIO(stdin_text)
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            code = cli.main(argv)
    finally:
        sys.stdin = old
    return code, out.getvalue()


class TestSwap(unittest.TestCase):
    def test_swap_by_name(self):
        code, out = run(["--columns", "a,c", "-"], "a,b,c\n1,2,3\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "c,b,a\n3,2,1\n")

    def test_swap_by_index(self):
        code, out = run(["--columns", "1,3", "-"], "a,b,c\n1,2,3\n")
        self.assertEqual(out, "c,b,a\n3,2,1\n")

    def test_self_swap_error(self):
        code, _ = run(["--columns", "a,a", "-"], "a,b\n1,2\n")
        self.assertEqual(code, 1)

    def test_unknown_column(self):
        code, _ = run(["--columns", "a,z", "-"], "a,b\n1,2\n")
        self.assertEqual(code, 1)

    def test_check(self):
        code, _ = run(["--columns", "a,b", "--check", "-"], "a,b\n1,2\n")
        self.assertEqual(code, 0)

    def test_json(self):
        code, out = run(["--columns", "a,c", "--json", "-"], "a,b,c\n1,2,3\n")
        d = json.loads(out)
        self.assertEqual(d["swapped"], ["a", "c"])
        self.assertEqual(d["positions"], [1, 3])


if __name__ == "__main__":
    unittest.main()
