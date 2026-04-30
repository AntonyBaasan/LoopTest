import argparse
import sys

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from looptest.services.file_reader import collect_files, run_file
from looptest.services.formatting import BOLD, DIM, WHITE, YELLOW, c
from looptest.services.reporter import print_summary
from looptest.services.runner import run_suite


def main():
    parser = argparse.ArgumentParser(
        prog="ui-test",
        description="Run UI test YAML files with Selenium Chrome",
    )
    parser.add_argument("path", help="Path to a YAML file or directory of YAML files")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headlessly")
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop the entire run on the first failed file",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Override per-step timeout (seconds) for all files",
    )
    args = parser.parse_args()

    files = collect_files(args.path)
    print(f"{c('UI Test CLI', WHITE, BOLD)}  {c('—', DIM)}  {len(files)} file(s) found\n")

    options = Options()
    if args.headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1440, 900)

    all_results = []
    try:
        for filepath in files:
            if args.timeout:
                with open(filepath, "r", encoding="utf-8") as handle:
                    suite = yaml.safe_load(handle)
                suite["timeout"] = args.timeout
                result = run_suite(driver, suite, filepath)
            else:
                result = run_file(driver, filepath)

            all_results.append(result)

            if args.stop_on_fail and result["status"] == "FAIL":
                print(c("⚠ Stopping after first failed suite", YELLOW, BOLD))
                break
    finally:
        driver.quit()

    print_summary(all_results)
    sys.exit(1 if any(result["status"] == "FAIL" for result in all_results) or not files else 0)
