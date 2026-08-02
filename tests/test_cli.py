import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from csv_swap_columns.cli import main, resolve


def run_cli(argv, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    import sys as _sys
    old = _sys.stdin
    _sys.stdin = io.StringIO(stdin)
    code = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
    finally:
        _sys.stdin = old
    return code, out.getvalue(), err.getvalue()


CSV = "a,b,c\n1,2,3\n4,5,6\n"


class TestResolve(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(resolve("1", ["a", "b"], False, 2), 0)
        self.assertEqual(resolve("-1", ["a", "b"], False, 2), 1)

    def test_name(self):
        self.assertEqual(resolve("b", ["a", "b"], False, 2), 1)

    def test_unknown(self):
        with self.assertRaises(KeyError):
            resolve("z", ["a", "b"], False, 2)

    def test_zero(self):
        with self.assertRaises(ValueError):
            resolve("0", ["a", "b"], False, 2)


class TestCli(unittest.TestCase):
    def test_swap_by_name(self):
        code, out, _ = run_cli(["a", "c"], stdin=CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out, "c,b,a\n3,2,1\n6,5,4\n")

    def test_swap_by_index(self):
        code, out, _ = run_cli(["1", "3"], stdin=CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "c,b,a")

    def test_negative_index(self):
        code, out, _ = run_cli(["a", "-1"], stdin=CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "c,b,a")

    def test_move(self):
        code, out, _ = run_cli(["--move", "a", "c"], stdin=CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "b,c,a")

    def test_no_header(self):
        code, out, _ = run_cli(["--no-header", "1", "3"], stdin=CSV)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "c,b,a")

    def test_delimiter_sniff(self):
        code, out, _ = run_cli(["a", "c"], stdin="a;b;c\n1;2;3\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "c;b;a\n3;2;1\n")

    def test_same_column(self):
        code, _, err = run_cli(["a", "a"], stdin=CSV)
        self.assertEqual(code, 2)

    def test_unknown_column(self):
        code, _, err = run_cli(["z", "a"], stdin=CSV)
        self.assertEqual(code, 2)
        self.assertIn("unknown column", err)

    def test_require_columns(self):
        code, _, err = run_cli(["a", "c", "--require-columns", "5"], stdin=CSV)
        self.assertEqual(code, 2)
        self.assertIn("required >= 5", err)

    def test_require_rows(self):
        code, _, err = run_cli(["a", "c", "--require-rows", "5"], stdin=CSV)
        self.assertEqual(code, 2)

    def test_in_place(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write(CSV)
            path = fh.name
        try:
            code, out, _ = run_cli(["a", "c", path, "--in-place"])
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            with open(path) as fh:
                self.assertEqual(fh.read(), "c,b,a\n3,2,1\n6,5,4\n")
        finally:
            os.unlink(path)

    def test_json_report(self):
        code, _, err = run_cli(["a", "c", "--json"], stdin=CSV)
        self.assertEqual(code, 0)
        import json
        report = json.loads(err)
        self.assertEqual(report["columns"], [1, 3])


if __name__ == "__main__":
    unittest.main()
