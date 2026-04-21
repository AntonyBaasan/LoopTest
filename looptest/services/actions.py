import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from looptest.services.assertions import run_assert
from looptest.services.selector import find_element, parse_selector


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
