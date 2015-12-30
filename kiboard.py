#!/usr/bin/env python

import sys
import argparse
import logging
import datetime
from pcbnew import *

specs = {
    'oshpark-4layers': {
        'source': "http://docs.oshpark.com/services/four-layer/",
        'trace_width': 5,
        'trace_spacing': 5, # not checked
        'drill': 10,
        'annular_ring': 5 # They say 4 in some places and 5 in others...
    },
    "AdvancedCiruits-standard": {
        'source': "http://www.4pcb.com/standard-custom-order-pcbs/",
        'trace_width': 5,
        'trace_spacing': 5, # not checked
        'drill': 10,
        'annular_ring': 5
    },
    "AdvancedCiruits-4layers66dollars": {
        'source': "http://www.4pcb.com/66-each-pcbs/",
        'trace_width': 6, # "Minimum 0.006" line/space ????
        'trace_spacing': 5, # not checked
        'drill': 15,
        'annular_ring': 5
    },
    "SeeedStudio": {
        'source': 'http://support.seeedstudio.com/knowledgebase/articles/422482-fusion-pcb-order-submission-guidelines',
        'trace_width': 6,
        'inner_trace_width': 8, # not checked yet
        'trace_spacing': 6, # not checked yet
        'innner_trace_spacing': 10, # not checked yet
        'silkscreen_width': 6,
        'drill': 11.81,
        'annular_ring': 6
    }
}


def main():
    parser = argparse.ArgumentParser(description = 'Check and fix some board design errors')
    parser.add_argument('--via-annular-ring', type=int, help='Minimum via annular ring in mils')
    parser.add_argument('--via-drill-width', type=int, help='Minimum drill width in mils')
    parser.add_argument('--trace-width', type=int, help='Minimum trace width in mils')
    parser.add_argument('--fix', action='store_true', help='Try to automatically fix errors (you WILL need to edit the board afterwards!')
    parser.add_argument('--debug', action='store_true', help='Show more debug information')
    parser.add_argument('--spec', action='append', help='Test compliance to a spec. Use --spec-list to get the list of supported specs.')
    parser.add_argument('--spec-list', action='store_true', help='Show the list of known PCB specs')
    parser.add_argument('file', type=string, nargs='?', help='the Kicad PCB file to process')

    args = parser.parse_args()


    if args.debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)

    if args.spec_list:
        show_spec_list()
        return

    if not args.file:
        print("Please provide a valid kicad_pcb file to work with.")
        return

    pcb = LoadBoard(str(args.file))

    runner = PCBRunner(pcb, args.fix)
    if args.via_drill_width:
        runner.addChecker(ViaDrillWidthChecker(args.via_drill_width))
    if args.via_annular_ring:
        runner.addChecker(AnnularRingChecker(args.via_annular_ring))
    if args.trace_width:
        runner.addChecker(TraceWidthChecker(args.trace_width))

    runner.run()

    if args.fix and runner.getTotalErrors() > 0:
        outputName = args.file + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        logging.info("Saving modified PCB to {}".format(outputName))
        pcb.Save(str(outputName))


def show_spec_list():
    for spec in specs.keys():
        print "{} ({})".format(spec, specs[spec]['source'])
        for rule in specs[spec]:
            if rule is not "source":
                print "  {}: {}".format(rule, specs[spec][rule])


class PCBRunner(object):
    def __init__(self, pcb, fix):
        self.pcb = pcb
        self.fix = fix
        self.checkers = []

    def addChecker(self, c):
        self.checkers.append(c)

    def process(self, checker, item):
        ok = checker.check(item)
        if not ok and self.fix:
            checker.fix(item)
        return ok

    def run(self):
        self.totalErrors = 0
        for checker in self.checkers:
            logging.info("Running {}".format(checker))
            errors = 0

            for item in self.pcb.GetTracks():
                if not self.process(checker, item):
                    errors = errors + 1
            logging.info("Found {} errors".format(errors))
            self.totalErrors = self.totalErrors + errors

        return self.totalErrors

    def getTotalErrors(self):
        return self.totalErrors

class AnnularRingChecker(object):
    def __init__(self, m):
        self.minimumAnnularRing = m

    def check(self, item):
        if type(item) is VIA:
            drill = ToMils(item.GetDrillValue())
            width = ToMils(item.GetWidth())
            annular = (width - drill) / 2

            if annular < self.minimumAnnularRing:
                logging.info("Fails annular ring test: Via: %f mils / %f mils - Annular ring: %f"%(drill, width, annular))
                return False
        return True

    def fix(self, item):
        # Can safely assume here is that it is a VIA
        drill = ToMils(item.GetDrillValue())
        item.SetWidth(FromMils(drill + self.minimumAnnularRing * 2))

class ViaDrillWidthChecker(object):
    def __init__(self, m):
        self.minimumDrillWidth = m

    def check(self, item):
        if type(item) is VIA:
            drill = ToMils(item.GetDrillValue())

            if drill < self.minimumDrillWidth:
                logging.debug("VIA drill is only {} mils".format(drill))
                return False

        return True

    def fix(self, item):
        if type(item) is VIA:
            item.SetDrill(FromMils(self.minimumDrillWidth))

class TraceWidthChecker(object):
    def __init__(self, m):
        self.minimumTraceWidth = m

    def check(self, item):
        if type(item) is TRACK:
            width = ToMils(item.GetWidth())
            if width < self.minimumTraceWidth:
                logging.debug("Trace width is only {} mils".format(width))
                return False
        return True

    def fix(self, item):
        if type(item) is TRACK:
            item.SetWidth(FromMils(self.minimumTraceWidth))


if __name__ == '__main__':
    main()
