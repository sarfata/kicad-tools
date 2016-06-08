#!/usr/bin/env python

import csv
import argparse

def read_csv_indexed_by_column(csvfile, index):
    dataset = {}
    reader = csv.DictReader(csvfile)
    for row in reader:
        print "Storing {} => {}".format(repr(row[index]), repr(row))
        dataset[row[index]] = row

    return dataset

def join_csv(csvleft, csvright, leftcol, rightcol, csvoutput, fields = None):
    dataset = read_csv_indexed_by_column(csvright, rightcol)

    reader = csv.DictReader(csvleft)

    # out_columns = reader.next().keys()
    out_columns = reader.fieldnames

    if fields is not None:
        out_columns.extend(fields)
    else:
        right_cols = dataset[dataset.keys()[0]].keys()
        for c in right_cols:
            if c not in out_columns:
                out_columns.append(c)

    print "extended dataset is: {}".format(out_columns)

    writer = csv.DictWriter(csvoutput, out_columns, )
    writer.writeheader()

    for row in reader:
        bom_line = dataset[row[leftcol]]
        extra_fields = { (k, bom_line[k]) for k in out_columns if k in bom_line.keys()}
        row.update(extra_fields)
        print "Writing row: {}".format(repr(row))
        writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description = "Merge a XYRS file with a BOM file.")

    parser.add_argument("xyrs", type = argparse.FileType('rb'), help = "XYRS file (Must be in CSV format)")
    parser.add_argument("bom", type = argparse.FileType('rb'), help = "BOM file to pull extra data from")
    parser.add_argument("--xyrs-identifier", default = "Ref", help = "Name (in XYRS file) of the column with component identifier (R11, C1, U42, etc)")
    parser.add_argument("--bom-identifier", default = "Schematic Reference", help = "Name (in BOM) of the column with component identifier")
    parser.add_argument("output", type = argparse.FileType('wb'), default = "Output CSV file")
    parser.add_argument("fields", nargs = '*', default = [ "MPN", "Digi-Key", "Mouser" ], help = "List of columns to pull from BOM file and add to XYRS file");
    args = parser.parse_args()

    join_csv(args.xyrs, args.bom, args.xyrs_identifier, args.bom_identifier, args.output, args.fields)


if __name__ == '__main__':
    main()
