import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

from csv_swap_columns.cli import main


def run(argv, stdin_text=""):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(stdin_text)):
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCsvSwapColumns(unittest.TestCase):
    def test_swap_by_name(self):
        code, out, _ = run(["--a", "a", "--b", "c"], "a,b,c\n1,2,3\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "c,b,a\n3,2,1\n")

    def test_swap_by_index(self):
        code, out, _ = run(["--a", "1", "--b", "2"], "a,b\n1,2\n")
        self.assertEqual(out, "b,a\n2,1\n")

    def test_no_header(self):
        code, out, _ = run(
            ["--a", "2", "--b", "3", "--no-header"], "1,2,3\n")
        self.assertEqual(out, "1,3,2\n")

    def test_same_column(self):
        code, _, err = run(["--a", "1", "--b", "1"], "a,b\n")
        self.assertEqual(code, 1)

    def test_unknown_column(self):
        code, _, err = run(["--a", "zzz", "--b", "a"], "a,b\n")
        self.assertEqual(code, 1)
        self.assertIn("unknown column", err)

    def test_check_fail(self):
        code, _, err = run(["--a", "a", "--b", "b", "--check"], "a,b\n")
        self.assertEqual(code, 2)

    def test_ragged_row(self):
        # rows short of a column index stay untouched
        code, out, _ = run(["--a", "1", "--b", "3"], "a,b,c\n1,2\n")
        self.assertIn("1,2", out)

    def test_json(self):
        code, out, _ = run(["--a", "a", "--b", "b", "--json"], "a,b\n1,2\n")
        rep = json.loads(out)
        self.assertTrue(rep["would_change"])
        self.assertEqual(rep["column_a"]["index"], 1)


if __name__ == "__main__":
    unittest.main()
