from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from looptest.services.selector import element_exists, find_element, parse_selector


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
