# csv-swap-columns

Swap two columns of a CSV file, including the header. Columns can be picked
by header name or 0-based index.

## Features

- Swap by header name or index (`--no-header` mode)
- Rows are padded to the widest row before swapping
- Custom `--delimiter`
- `--json` emits a small report on stderr
- Zero dependencies, Python >= 3.9

## Install

```bash
pip install .
# or
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```bash
csv-swap-columns email name users.csv
printf 'a,b,c\n1,2,3\n' | csv-swap-columns a c -
csv-swap-columns 0 2 data.csv --no-header
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | ok |
| 1 | I/O or CLI error |
| 2 | unknown column, out-of-range index, or identical columns |

## License

MIT
