import io
import json
import sys

from csv_swap_columns.cli import main, parse_order_args, sniff_delimiter


CSV = "name,age,city\nalice,30,paris\nbob,25,lyon\n"


def run_cli(argv, stdin_text=""):
    out, err = io.StringIO(), io.StringIO()
    old_out, old_err, old_in = sys.stdout, sys.stderr, sys.stdin
    sys.stdout, sys.stderr = out, err
    sys.stdin = io.StringIO(stdin_text)
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr, sys.stdin = old_out, old_err, old_in
    return code, out.getvalue(), err.getvalue()


def test_sniff_delimiter():
    assert sniff_delimiter("a,b,c\n1,2,3\n") == ","
    assert sniff_delimiter("a;b;c\n1;2;3\n") == ";"
    assert sniff_delimiter("a\tb\tc\n1\t2\t3\n") == "\t"
    assert sniff_delimiter("a|b|c\n1|2|3\n") == "|"


def test_parse_order_args():
    assert parse_order_args(["a,b", "c"]) == ["a", "b", "c"]
    assert parse_order_args(["a", "b"]) == ["a", "b"]


def test_swap_by_name():
    code, out, _ = run_cli(["--swap", "name", "city"], CSV)
    assert code == 0
    assert out.splitlines()[0] == "city,age,name"
    assert out.splitlines()[1] == "paris,30,alice"


def test_swap_by_index():
    code, out, _ = run_cli(["--swap", "1", "3"], CSV)
    assert code == 0
    assert out.splitlines()[0] == "city,age,name"


def test_order_partial():
    code, out, _ = run_cli(["--order", "city,name"], CSV)
    assert code == 0
    assert out.splitlines()[0] == "city,name,age"


def test_order_strict_fails():
    code, _, err = run_cli(["--order", "city", "--strict"], CSV)
    assert code == 1
    assert "missing" in err


def test_order_full_strict():
    code, out, _ = run_cli(["--order", "city,name,age", "--strict"], CSV)
    assert code == 0
    assert out.splitlines()[0] == "city,name,age"


def test_check_pass_and_fail():
    code, _, _ = run_cli(["--order", "name,age,city", "--check"], CSV)
    assert code == 0
    code, _, err = run_cli(["--order", "age,name,city", "--check"], CSV)
    assert code == 2
    assert "NOT in the requested order" in err


def test_no_header():
    code, out, _ = run_cli(["--no-header", "--swap", "1", "2"], "a,b\n1,2\n")
    assert code == 0
    assert out.splitlines()[0] == "b,a"


def test_unknown_column():
    code, _, err = run_cli(["--swap", "nope", "age"], CSV)
    assert code == 1
    assert "not found" in err


def test_index_out_of_range():
    code, _, err = run_cli(["--swap", "1", "9"], CSV)
    assert code == 1
    assert "out of range" in err


def test_json_summary():
    code, _, err = run_cli(["--swap", "name", "age", "--json"], CSV)
    assert code == 0
    data = json.loads(err)
    assert data["new_order"][0] == "age"


def test_in_place(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(CSV)
    code, out, _ = run_cli(["--swap", "name", "city", "-i", str(f)])
    assert code == 0
    assert f.read_text().splitlines()[0] == "city,age,name"


def test_empty_input():
    code, _, err = run_cli(["--swap", "a", "b"], "")
    assert code == 1
    assert "empty input" in err
