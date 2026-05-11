"""Run a command."""
import subprocess as sp

import rich
from loguru import logger


def run_cmd(cmd):
    """Execute cmd."""
    logger.info(f"{cmd=}")
    ret = sp.run(cmd, capture_output=1, check=0, shell=1, encoding="utf8")
    if ret.stdout:
        rich.print(ret.stdout)
    if ret.stderr:
        rich.print("[red bold]" + ret.stdout)
