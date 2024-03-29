# -*- coding: UTF-8 -*-
from fame.core.module import ProcessingModule
from fame.common.exceptions import ModuleInitializationError, ModuleExecutionError
import logging
import re
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from os.path import exists
from time import perf_counter

from .__info__ import __author__, __copyright__, __email__, __license__, __source__, __version__
from .__init__ import *

class PEiDModule(ProcessingModule):
    name = 'peid_module'
    description = 'Detect packing in Windows PE files using PEiD signatures.'
    acts_on = ['executable']

    def __init__(self):
        super().__init__()

    def valid_file(self, path):
        if not exists(path):
            raise ValueError("Input file does not exist")
        return path

    def valid_percentage(self, percentage):
        p = float(percentage)
        if not 0. <= p <= 1.:
            raise ValueError("Not a percentage")
        return p

    def initialize(self):
        """ Module initialization. """
        # You can perform any necessary initialization here.
        pass

    def main(self, path, author=True, db=DB, ep_only=True, match_once=False, version=True, benchmark=False, verbose=False):
        """ Tool's main function """
        descr = "PEiD {}\n\nAuthor   : {} ({})\nCopyright: {}\nLicense  : {}\nSource   : {}\n" \
            "\nThis tool is an implementation in Python of the Packed Executable iDentifier (PEiD) in the scope of " \
            "packing detection for Windows PE files based on signatures.\n\n"
        descr = descr.format(__version__, __author__, __email__, __copyright__, __license__, __source__)
        examples = "usage examples:\n- " + "\n- ".join([
            "peid program.exe",
            "peid program.exe -b",
            "peid program.exe --db custom_sigs_db.txt",
        ])
        parser = ArgumentParser(description=descr, epilog=examples, formatter_class=RawTextHelpFormatter, add_help=False)
        parser.add_argument("path", type=self.valid_file, nargs="+", help="path to portable executable")
        opt = parser.add_argument_group("optional arguments")
        opt.add_argument("-a", "--author", action="store_true", help="include author in the result")
        opt.add_argument("-d", "--db", default=db, type=self.valid_file,
                         help="path to the custom database of signatures (default: None ; use the embedded DB)")
        opt.add_argument("-e", "--ep-only", action="store_false",
                         help="consider only entry point signatures (default: True)")
        opt.add_argument("-m", "--match-once", action="store_true",
                         help="match only one signature (relies on peutils' db.match() instead of db.match_all()")
        opt.add_argument("-v", "--version", action="store_true", help="include the version in the result")
        extra = parser.add_argument_group("extra arguments")
        extra.add_argument("-b", "--benchmark", action="store_true",
                           help="enable benchmarking, output in seconds (default: False)")
        extra.add_argument("-h", "--help", action="help", help="show this help message and exit")
        extra.add_argument("--verbose", action="store_true", help="display debug information (default: False)")
        args = parser.parse_args()
        logging.basicConfig()
        args.logger = logging.getLogger("peid")
        args.logger.setLevel([logging.INFO, logging.DEBUG][args.verbose])
        code = 0
        # execute the tool
        if benchmark:
            t1 = perf_counter()
        results = identify_packer(*args.path, db=args.db, ep_only=args.ep_only, match_all=not args.match_once,
                                  logger=args.logger)
        for pe, r in results:
            if not author:
                r = list(map(lambda x: re.sub(r"\s*\-(\-?\>|\s*by)\s*(.*)$", "", x), r))
            if not version:
                VER = r"\s*([vV](ersion)?|R)?\s?(20)?\d{1,2}(\.[xX0-9]{1,3}([a-z]?\d)?){0,3}[a-zA-Z\+]?" \
                      r"(\s*\(?(\s*([Aa]lpha|[Bb]eta|final|lite|LITE|osCE|Demo|DEMO)){1,2}(\s*[a-z]?\d)?\)?)?"
                VER = re.compile(r"^(.*?)\s+" + VER + r"(\s*[-_\/\~]" + VER + r"){0,3}(\s+\(unregistered\))?")
                r = list(map(lambda x: re.sub(r"\s+\d+(\s+SE)?$", "", VER.sub(r"\1", x)), r))
            if len(results) == 1:
                dt = str(perf_counter() - t1) if benchmark else ""
                if dt != "":
                    r.append(dt)
                if len(r) > 0:
                    print("\n".join(r))
                return 0
            else:
                print("%s %s" % (pe, ",".join(r)))
        dt = str(perf_counter() - t1) if benchmark else ""
        if dt != "":
            print(dt)
        return 0

    def each(self, target):
        """ Process each target file. """
        # Here, you can call the main function and pass the appropriate arguments.
        result = self.main(target)
        return result