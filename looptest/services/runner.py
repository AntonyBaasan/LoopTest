import time

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)

from looptest.services.actions import run_step
from looptest.services.formatting import BOLD, CYAN, DIM, GREEN, RED, WHITE, c


def print_suite_header(suite: dict):
    print(c("─" * 60, DIM))
    print(f"  {c('▶', CYAN, BOLD)}  {c(suite['name'], WHITE, BOLD)}")
    if suite.get("description"):
        print(f"     {c(suite['description'], DIM)}")
    print(c("─" * 60, DIM))


def run_suite(driver, suite, filepath):
    suite_name = suite["name"]
    base_url = suite["base_url"]
    timeout = suite.get("timeout", 10)
    steps = suite["steps"]
    results = []
    failed = False

    print_suite_header(suite)

    for index, step in enumerate(steps, start=1):
        step_id = step.get("id", f"step_{index}")
        t0 = time.time()
        try:
            run_step(driver, step, base_url, timeout)
            elapsed = time.time() - t0
            print(
                f"  {c('✔', GREEN, BOLD)}  "
                f"[{index}/{len(steps)}] {step_id} ({step['action']}) {elapsed:.2f}s"
            )
            results.append({"id": step_id, "status": "pass"})
        except (
            AssertionError,
            TimeoutException,
            NoSuchElementException,
            ElementNotInteractableException,
            ValueError,
        ) as e:
            print(f"  {c('✘', RED, BOLD)}  [{index}/{len(steps)}] {step_id} ({step['action']})")
            print(f"      {type(e).__name__}: {e}")
            results.append({"id": step_id, "status": "fail", "error": str(e)})
            failed = True
            break

    passed_steps = sum(1 for item in results if item["status"] == "pass")
    status = "FAIL" if failed else "PASS"
    color = RED if failed else GREEN
    print(
        f"\n  Result: {c(status, color, BOLD)}  "
        f"({passed_steps}/{len(steps)} steps passed)\n"
    )

    return {
        "file": str(filepath),
        "name": suite_name,
        "status": status,
        "steps": results,
    }
