"""Verify the immutable canary identity before replacing this process."""
from __future__ import annotations

import os
import sys

from shared.canary_identity import CanaryIdentityError, require_canary_identity


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "--" or len(args) == 1:
        raise SystemExit("usage: python -m canary.preexec -- COMMAND [ARG ...]")
    try:
        require_canary_identity()
    except CanaryIdentityError as exc:
        raise SystemExit(f"canary identity rejected: {exc}") from exc
    os.execvp(args[1], args[1:])
    return 127


if __name__ == "__main__":
    main()
