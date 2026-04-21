from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
