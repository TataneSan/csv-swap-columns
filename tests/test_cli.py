import csv
import io
import subprocess
import sys
import unittest
import tempfile
import os


def run(args, inp=None, files=None):
    cmd = [sys.executable, "-m", "csv_swap_columns"] + args
    return subprocess.run(cmd, input=inp, capture_output=True, text=True)


class TestSwapColumns(unittest.TestCase):
    def make_csv(self, text):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w") as f:
            f.write(text)
        return path

    def test_swap_by_name(self):
        p = self.make_csv("name,age,city\nAlice,30,Paris\nBob,25,Lyon\n")
        r = run([p, "name", "age"])
        self.assertEqual(r.returncode, 0)
        rows = list(csv.reader(io.StringIO(r.stdout)))
        self.assertEqual(rows[0], ["age", "name", "city"])
        os.unlink(p)

    def test_swap_by_index(self):
        p = self.make_csv("name,age,city\nAlice,30,Paris\n")
        r = run([p, "0", "2"])
        self.assertEqual(r.returncode, 0)
        rows = list(csv.reader(io.StringIO(r.stdout)))
        self.assertEqual(rows[0], ["city", "age", "name"])
        os.unlink(p)

    def test_negative_index(self):
        p = self.make_csv("a,b,c\n1,2,3\n")
        r = run([p, "0", "-1"])
        self.assertEqual(r.returncode, 0)
        rows = list(csv.reader(io.StringIO(r.stdout)))
        self.assertEqual(rows[0], ["c", "b", "a"])
        os.unlink(p)

    def test_move(self):
        p = self.make_csv("a,b,c\n1,2,3\n")
        r = run([p, "a", "c", "--move"])
        self.assertEqual(r.returncode, 0)
        rows = list(csv.reader(io.StringIO(r.stdout)))
        self.assertEqual(rows[0], ["b", "c", "a"])
        os.unlink(p)

    def test_no_header(self):
        p = self.make_csv("1,2,3\n4,5,6\n")
        r = run([p, "0", "1", "--no-header"])
        self.assertEqual(r.returncode, 0)
        rows = list(csv.reader(io.StringIO(r.stdout)))
        self.assertEqual(rows[0], ["2", "1", "3"])
        os.unlink(p)

    def test_gate_columns(self):
        p = self.make_csv("a,b\n1,2\n")
        r = run([p, "a", "b", "--require-columns", "5"])
        self.assertEqual(r.returncode, 2)
        os.unlink(p)

    def test_gate_rows(self):
        p = self.make_csv("a,b\n1,2\n")
        r = run([p, "a", "b", "--require-rows", "5"])
        self.assertEqual(r.returncode, 2)
        os.unlink(p)


if __name__ == "__main__":
    unittest.main()
