import glob
from pathlib import Path

import yaml

from looptest.services.formatting import BOLD, YELLOW, c
from looptest.services.runner import run_suite


def run_file(driver, filepath):
    with open(filepath, "r", encoding="utf-8") as handle:
        suite = yaml.safe_load(handle)
    return run_suite(driver, suite, filepath)


def collect_files(path):
    path_obj = Path(path)
    if path_obj.is_file() and path_obj.suffix.lower() in {".yaml", ".yml"}:
        return [str(path_obj)]
    if path_obj.is_dir():
        files = sorted(
            glob.glob(str(path_obj / "*.yaml")) + glob.glob(str(path_obj / "*.yml"))
        )
        if not files:
            print(c(f"No YAML files found in {path}", YELLOW, BOLD))
        return files
    raise FileNotFoundError(path)
