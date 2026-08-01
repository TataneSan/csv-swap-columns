# csv-swap-columns

Swap two columns of a CSV file by name or 0-based index. Reads from a file or
stdin, writes the swapped CSV to stdout. Pure Python, zero dependencies.

## Features

- Columns referenced by header name or 0-based index
- `--no-header` mode when the CSV has no header row
- Custom delimiter (`--delimiter ';'`)
- Short rows padded with empty fields so the swap always succeeds
- `--check` mode for CI: exit 0 when the columns actually differ, 2 when they
  are identical (swap would be a no-op)
- `--json` machine-readable report on stderr

## Install

```bash
pip install .
# or directly from GitHub
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

You can also run it without installing: `python3 -m csv_swap_columns`.

## Usage

```bash
csv-swap-columns data.csv --col-a name --col-b email
csv-swap-columns data.csv -a 0 -b 2 --delimiter ';'
cat data.csv | csv-swap-columns - -a first_name -b last_name
csv-swap-columns --check data.csv -a price -b discount   # CI
```

## Examples

```console
$ cat people.csv
name,city,email
Alice,Paris,alice@example.com
Bob,Lyon,bob@example.com
$ csv-swap-columns people.csv -a name -b email
email,city,name
alice@example.com,Paris,Alice
bob@example.com,Lyon,Bob

$ csv-swap-columns --no-header pipe.csv -a 0 -b 1 -d '|'
b2|a2
b1|a1
```

Check mode:

```console
$ csv-swap-columns --check people.csv -a city -b email; echo $?
columns 1 and 2 differ over 2 row(s)
0
$ csv-swap-columns --check dup.csv -a x -b y; echo $?
columns 0 and 1 identical over 3 row(s)
2
```

JSON report (stderr):

```console
$ csv-swap-columns people.csv -a 0 -b 2 --json >/dev/null
{
  "file": "people.csv",
  "col_a": {"spec": "0", "index": 0, "name": "name"},
  "col_b": {"spec": "2", "index": 2, "name": "email"},
  "rows": 2,
  "changed": true
}
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success, or `--check` passed (columns differ) |
| 1 | I/O or CLI error (missing file, unknown column, invalid CSV, same column twice) |
| 2 | `--check` failed: columns identical everywhere |

## License

MIT
