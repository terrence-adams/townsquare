#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Entry point: python -m hostreader"""
import sys

from hostreader.host_reader import main

if __name__ == "__main__":
    sys.exit(main())
