"""
Convert word table to various other formats.

Needs tabulate (https://pypi.python.org/pypi/tabulate).

Usage: python wordtable.py actions.txt > actions.rst
"""

import sys
from tabulate import tabulate


def tabledata(data, rows=10):
    padding = rows - (len(data) % rows)
    values = list(data) + [None] * padding
    for row in range(rows):
        yield [values[idx] for idx in range(row, len(values), rows)]


def writetable(words, formats):
    table = list(tabledata(words))
    print ".. Autogenerated by wordtable.py -- do not edit!"

    for fmt in formats:
        output = tabulate(table, tablefmt=fmt)

        print
        print ".. raw::", fmt
        print
        for line in output.split("\n"):
            print "  ", line


if __name__ == "__main__":
    import fileinput

    words = []
    for word in fileinput.input():
        words.append(word.strip())

    writetable(words, formats=['html', 'latex'])