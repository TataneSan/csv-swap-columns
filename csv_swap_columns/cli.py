"""csv-swap-columns: echange deux colonnes d'un CSV par nom ou index.

Les colonnes sont designees soit par leur nom (si le CSV a un header), soit
par leur index 0-based avec ``--index``. Les lignes dont la longueur differe
du header sont traitees selon ``--strict`` (erreur) ou paddees/tronquees.

Exit codes :
  0  succes
  1  erreur I/O, argument invalide, colonne introuvable
  2  --check : les deux colonnes designees seraient effectivement permutees
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import List, Optional, Tuple

from . import __version__


def resolve_column(ref: str, header: List[str], by_index: bool) -> int:
    """Retourne l'index de colonne correspondant a ref, ou leve ValueError."""
    if by_index:
        try:
            idx = int(ref)
        except ValueError:
            raise ValueError(f"index invalide: {ref!r}")
        if idx < 0 or idx >= len(header):
            raise ValueError(
                f"index {idx} hors limites (0..{len(header) - 1})"
            )
        return idx
    if ref not in header:
        raise ValueError(
            f"colonne {ref!r} introuvable dans le header {header!r}"
        )
    return header.index(ref)


def swap_rows(
    rows: List[List[str]],
    i: int,
    j: int,
) -> List[List[str]]:
    out = []
    width = max((len(r) for r in rows), default=0)
    for row in rows:
        r = list(row) + [""] * (width - len(row))
        r[i], r[j] = r[j], r[i]
        out.append(r)
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="csv-swap-columns",
        description="Echange deux colonnes d'un CSV par nom ou index.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="fichier CSV d'entree ('-' ou omis : stdin)",
    )
    parser.add_argument(
        "--col1",
        required=True,
        help="premiere colonne (nom, ou index si --index)",
    )
    parser.add_argument(
        "--col2",
        required=True,
        help="seconde colonne (nom, ou index si --index)",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="interpreter --col1/--col2 comme des index 0-based",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="le CSV n'a pas de header (impose --index)",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="separateur CSV (defaut: ',')",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="erreur sur les lignes dont la longueur differe du header",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="mode CI : n'ecrit rien, exit 2 si un swap aurait lieu",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime un rapport JSON au lieu du CSV permute",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="en --check sans --json : silence, seul le code de sortie compte",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    if len(args.delimiter) != 1:
        print("erreur: le delimiteur doit etre un seul caractere", file=sys.stderr)
        return 1
    if args.no_header and not args.index:
        print("erreur: --no-header impose --index", file=sys.stderr)
        return 1

    try:
        if args.input == "-":
            raw = sys.stdin.read()
        else:
            with open(args.input, "r", encoding="utf-8", newline="") as fh:
                raw = fh.read()
    except OSError as exc:
        print(f"erreur: lecture impossible: {exc}", file=sys.stderr)
        return 1

    try:
        rows = list(csv.reader(io.StringIO(raw), delimiter=args.delimiter))
    except csv.Error as exc:
        print(f"erreur: CSV invalide: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("erreur: CSV vide", file=sys.stderr)
        return 1

    header = rows[0] if not args.no_header else rows[0]
    # En --no-header on resout sur la largeur observee, pas sur un header.
    width = max(len(r) for r in rows)
    pseudo_header = [str(i) for i in range(width)]
    ref_header = header if not args.no_header else pseudo_header

    try:
        i = resolve_column(args.col1, ref_header, args.index or args.no_header)
        j = resolve_column(args.col2, ref_header, args.index or args.no_header)
    except ValueError as exc:
        print(f"erreur: {exc}", file=sys.stderr)
        return 1

    if i == j:
        print("erreur: les deux colonnes designees sont identiques", file=sys.stderr)
        return 1

    if args.strict:
        expected = len(header)
        for n, row in enumerate(rows, start=1):
            if len(row) != expected:
                print(
                    f"erreur: ligne {n} a {len(row)} colonnes (attendu {expected})",
                    file=sys.stderr,
                )
                return 1

    swapped = swap_rows(rows, i, j)

    if args.json:
        payload = {
            "col1": args.col1,
            "col2": args.col2,
            "index1": i,
            "index2": j,
            "rows": len(rows),
            "swapped_header": swapped[0] if not args.no_header else None,
            "mode": "check" if args.check else "swap",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.check:
        if not args.quiet:
            print(
                f"colonnes {i} et {j} seraient permutees sur {len(rows)} ligne(s)",
                file=sys.stderr,
            )
    else:
        writer = csv.writer(sys.stdout, delimiter=args.delimiter, lineterminator="\n")
        writer.writerows(swapped)

    if args.check:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
