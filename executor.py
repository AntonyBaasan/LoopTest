#!/usr/bin/env python3
"""
UI Test CLI Executor
Usage:
  python executor.py tests/               # run all YAML files in a folder
  python executor.py tests/01_nav.yaml    # run a single file
  python executor.py tests/ --headless    # run without opening browser window
  python executor.py tests/ --stop-on-fail
"""

import argparse
import glob
import sys
import time
from pathlib import Path

import yaml
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
WHITE = "\033[97m"


def c(text, *codes) -> str:
    """Wrap text with ANSI codes, always appending RESET at the end."""
    return "".join(codes) + str(text) + RESET


def parse_selector(raw: str) -> tuple:
    if " >> " in raw:
        return ("compound", raw)
    if raw.startswith("css:"):
        return (By.CSS_SELECTOR, raw[4:])
    if raw.startswith("xpath:"):
        return (By.XPATH, raw[6:])
    if raw.startswith("id:"):
        return (By.ID, raw[3:])
    if raw.startswith("name:"):
        return (By.NAME, raw[5:])
    if raw.startswith("text="):
        text = raw[5:]
        return (By.XPATH, f"//*[normalize-space(text())='{text}']")
    return (By.CSS_SELECTOR, raw)


def find_element(driver, raw_selector: str, timeout: int):
    by, val = parse_selector(raw_selector)

    if by == "compound":
        parent_raw, child_raw = raw_selector.split(" >> ", 1)
        parent_by, parent_val = parse_selector(parent_raw)
        parent = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((parent_by, parent_val))
        )
        child_by, child_val = parse_selector(child_raw)
        return WebDriverWait(driver, timeout).until(
            lambda d: parent.find_element(child_by, child_val)
        )

    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, val))
    )


def element_exists(driver, raw_selector: str) -> bool:
    try:
        if " >> " in raw_selector:
            parent_raw, child_raw = raw_selector.split(" >> ", 1)
            parent_by, parent_val = parse_selector(parent_raw)
            child_by, child_val = parse_selector(child_raw)
            parent = driver.find_element(parent_by, parent_val)
            parent.find_element(child_by, child_val)
            return True
        by, val = parse_selector(raw_selector)
        driver.find_element(by, val)
        return True
    except NoSuchElementException:
        return False


def action_navigate(driver, step, base_url, timeout):
    url = step["url"]
    if url.startswith("http"):
        full_url = url
    else:
        full_url = base_url.rstrip("/") + "/" + url.lstrip("/")
    driver.get(full_url)
    time.sleep(0.5)


def action_click(driver, step, timeout):
    el = find_element(driver, step["selector"], timeout)
    if step.get("expect_disabled") is True:
        assert not el.is_enabled(), f"Expected disabled element: {step['selector']}"
        return

    by, val = parse_selector(step["selector"])
    if by == "compound":
        WebDriverWait(driver, timeout).until(lambda d: el.is_displayed() and el.is_enabled())
    else:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, val)))
    el.click()


def action_hover(driver, step, timeout):
    el = find_element(driver, step["selector"], timeout)
    ActionChains(driver).move_to_element(el).perform()
    time.sleep(0.3)


def action_menu_navigate(driver, step, timeout):
    menu = find_element(driver, step["menu_selector"], timeout)
    ActionChains(driver).move_to_element(menu).perform()
    time.sleep(0.3)
    sub_key = step.get("submenu_selector") or step.get("item_selector")
    item = find_element(driver, sub_key, timeout)
    item.click()


def action_type(driver, step, timeout):
    el = find_element(driver, step["selector"], timeout)
    el.clear()
    el.send_keys(step["value"])


def action_toggle(driver, step, timeout):
    el = find_element(driver, step["selector"], timeout)
    desired = step.get("set_state")

    if el.tag_name.lower() == "input" and el.get_attribute("type") in ["checkbox", "radio"]:
        current = el.is_selected()
        if desired == "on" and not current:
            el.click()
        elif desired == "off" and current:
            el.click()
        elif desired is None:
            el.click()
        return

    aria = el.get_attribute("aria-checked") or el.get_attribute("aria-expanded")
    current_on = aria == "true"
    if desired == "on" and not current_on:
        el.click()
    elif desired == "off" and current_on:
        el.click()
    elif desired is None:
        el.click()
    elif aria is None and desired is None:
        el.click()


def action_select(driver, step, timeout):
    el = find_element(driver, step["selector"], timeout)
    sel = Select(el)
    by = step.get("by", "visible_text")
    val = step["value"]

    if by == "visible_text":
        sel.select_by_visible_text(str(val))
    elif by == "value":
        sel.select_by_value(str(val))
    elif by == "index":
        sel.select_by_index(int(val))
    else:
        raise ValueError(f"Unknown select 'by': {by}")


def action_custom_select(driver, step, timeout):
    trigger = find_element(driver, step["trigger_selector"], timeout)
    trigger.click()
    time.sleep(0.2)
    option = find_element(driver, step["option_selector"], timeout)
    option.click()


def wait_for_visible(driver, raw_selector: str, timeout: int):
    by, val = parse_selector(raw_selector)
    if by == "compound":
        return WebDriverWait(driver, timeout).until(
            lambda d: (el := find_element(driver, raw_selector, timeout)) and el.is_displayed() and el
        )
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, val)))


def wait_for_hidden(driver, raw_selector: str, timeout: int):
    by, val = parse_selector(raw_selector)
    if by == "compound":
        return WebDriverWait(driver, timeout).until(
            lambda d: not element_exists(driver, raw_selector)
            or not find_element(driver, raw_selector, 1).is_displayed()
        )
    return WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((by, val)))


def run_assert(driver, assertion, timeout):
    if "title_contains" in assertion:
        WebDriverWait(driver, timeout).until(EC.title_contains(assertion["title_contains"]))

    if "url_contains" in assertion:
        WebDriverWait(driver, timeout).until(EC.url_contains(assertion["url_contains"]))

    if "element_visible" in assertion:
        wait_for_visible(driver, assertion["element_visible"], timeout)

    if "element_hidden" in assertion:
        wait_for_hidden(driver, assertion["element_hidden"], timeout)

    if "element_missing_class" in assertion:
        spec = assertion["element_missing_class"]
        el = find_element(driver, spec["selector"], timeout)
        classes = (el.get_attribute("class") or "").split()
        assert spec["class"] not in classes, (
            f"Element {spec['selector']} unexpectedly has class '{spec['class']}'"
        )

    if "attribute" in assertion:
        spec = assertion["attribute"]
        el = find_element(driver, spec["selector"], timeout)
        actual = el.get_attribute(spec["name"])
        assert actual == spec["value"], (
            f"Attribute {spec['name']} on {spec['selector']} expected "
            f"'{spec['value']}', got '{actual}'"
        )

    if "element_text" in assertion:
        spec = assertion["element_text"]
        el = find_element(driver, spec["selector"], timeout)
        text = el.text or el.get_attribute("innerText") or ""
        assert spec["contains"] in text, (
            f"Element text for {spec['selector']} does not contain '{spec['contains']}'"
        )


def run_step(driver, step: dict, base_url: str, timeout: int):
    action = step["action"]

    dispatch = {
        "navigate": lambda: action_navigate(driver, step, base_url, timeout),
        "click": lambda: action_click(driver, step, timeout),
        "hover": lambda: action_hover(driver, step, timeout),
        "menu_navigate": lambda: action_menu_navigate(driver, step, timeout),
        "type": lambda: action_type(driver, step, timeout),
        "toggle": lambda: action_toggle(driver, step, timeout),
        "select": lambda: action_select(driver, step, timeout),
        "custom_select": lambda: action_custom_select(driver, step, timeout),
    }

    if action not in dispatch:
        raise ValueError(f"Unknown action: '{action}'")

    dispatch[action]()

    if "assert" in step:
        run_assert(driver, step["assert"], timeout)


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


def print_summary(all_results):
    total = len(all_results)
    passed = sum(1 for item in all_results if item["status"] == "PASS")
    failed = total - passed

    print(c("─" * 60, DIM))
    print(f"  {c('SUMMARY', WHITE, BOLD)}")
    print(c("─" * 60, DIM))
    for result in all_results:
        icon = "✔" if result["status"] == "PASS" else "✘"
        color = GREEN if result["status"] == "PASS" else RED
        print(f"  {c(icon, color, BOLD)}  {result['name']}")
    print()
    print(f"  Total: {total}   Passed: {passed}   Failed: {failed}")
    print(c("─" * 60, DIM))


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


if __name__ == "__main__":
    main()
