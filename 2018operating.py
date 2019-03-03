#!/usr/bin/env python3
"""
Ingest the 2018 City of Winnipeg operating budget PDF as HTML from pdftohtml, and dump out JSON
that describes the service-based salaries, as well as by department.

Example usage:

wget https://winnipeg.ca/finance/files/2018AdoptedOperatingBudgetVolume2.pdf
pdftohtml -hidden -noframes -c -s -i 2018AdoptedOperatingBudgetVolume2.pdf
cat 2018AdoptedOperatingBudgetVolume2.html | python3 do.py > salaries.json
"""

import sys
import re
import json

SALARY_COLUMNS = [
    "2016 Actual", "2017 Actual", "2018 Adopted", "2019 Projection",
    "2020 Projection"
]


def test(l):
    return "Contributing Department" in l


def clean_line_depts(l):
    m = re.findall(">[^<]+<", l)
    return [
        re.sub("[<>]", "", d).replace("&amp;", "&").split("&#160;") for d in m
        if "Contributing" not in d
    ]


def clean_line_salaries(l):
    m = re.findall(">[^<]+<", l)
    return [re.sub("[<>]", "", s) for s in m]


def parse(lines):
    depts = list()
    salaries = list()
    i = 0
    while "Operating Budget" not in lines[i]:
        depts.append(clean_line_depts(lines[i]))
        i += 1

    depts = [
        d.strip() for d in json.loads("[" + re.sub(
            "[\[\]%]", "", json.dumps(
                [d for d in depts if d != [] and d != ""])) + "]")
        if d.strip() != ""
    ]
    depts = dict([(depts[i].strip(), depts[i + 1].strip())
                  for i in range(0,
                                 len(depts) - 1, 2)])
    assert 100.0 == sum([float(v) for v in depts.values()])
    for k, v in depts.items():
        depts[k] = float(v) / 100.0

    while "Salaries" not in lines[i]:
        i += 1

    i += 1
    while re.search(">[0-9.,]+<", lines[i]) is not None:
        salaries.append(clean_line_salaries(lines[i]))
        i += 1

    return dict(depts=depts, salaries=dict(zip(SALARY_COLUMNS, salaries)))


html_lines = [l.strip() for l in sys.stdin.read().split("\n")]

salaries = list()

for i in range(len(html_lines)):
    l = html_lines[i]
    if test(l):
        data = parse(html_lines[i:])
        salaries.append(data)

print(json.dumps(salaries))
