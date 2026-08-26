"""Run the taxi pipeline stages in order."""

import argparse
import logging
import sys
import time
from collections.abc import Callable, Sequence

from pipeline import ingest, transform, load_to_bq

logger = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse stage-selection flags."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-transform", action="store_true")
    parser.add_argument("--skip-load", action="store_true")
    return parser.parse_args(argv)


def run_stage(name: str, stage: Callable[[], None]) -> None:
    """Run one stage and report its elapsed time."""
    started_at = time.perf_counter()
    logger.info("Starting %s stage", name)
    try:
        stage()
    except Exception:
        logger.exception(
            "%s stage failed after %.2f seconds",
            name,
            time.perf_counter() - started_at,
        )
        raise
    logger.info(
        "%s stage completed in %.2f seconds",
        name,
        time.perf_counter() - started_at,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run enabled stages and return a process exit code."""
    args = parse_args(argv)
    stages = (
        ("ingest", ingest.run, args.skip_ingest),
        ("transform", transform.run, args.skip_transform),
        ("load", load_to_bq.run, args.skip_load),
    )

    try:
        for name, stage, skipped in stages:
            if skipped:
                logger.info("Skipping %s stage", name)
                continue
            run_stage(name, stage)
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
