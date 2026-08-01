# csv-swap-columns

Swap two columns of a CSV file, addressed by header name or 1-based index.
Headers are swapped too; short rows are padded.

Pure Python standard library. No dependencies.

## Features

- Swap columns by name or 1-based index (`--columns a,c` or `--columns 1,3`)
- Keeps all rows aligned, pads ragged rows to the header width
- Custom delimiter (`--delimiter ';'`)
- `--check` self-verification mode (swap twice, compare to original)
- `--json` machine-readable report
- Reads stdin when the file is omitted or `-`

## Install

```bash
pip install .
# or directly from GitHub
pip install git+https://github.com/TataneSan/csv-swap-columns.git
```

## Usage

```bash
csv-swap-columns --columns first,last people.csv
csv-swap-columns --columns 1,3 --delimiter ';' data.csv
cat data.csv | csv-swap-columns --columns 2,4 -
csv-swap-columns --columns a,b --check data.csv   # CI self-check
csv-swap-columns --columns a,b --json data.csv    # report only
```

## Example

```bash
$ printf 'a,b,c\n1,2,3\n' | csv-swap-columns --columns a,c -
c,b,a
3,2,1
```

## Exit codes

| Code | Meaning                               |
| ---: | ------------------------------------- |
|    0 | Success                               |
|    1 | I/O, CLI or CSV parse error           |
|    2 | `--check` self-verification failed    |

## License

MIT
