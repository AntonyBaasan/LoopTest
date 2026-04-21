from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main() -> None:
    # 1. Initialize the browser driver (e.g., Chrome)
    print("Starting Selenium")
    driver = webdriver.Chrome()

    # 2. Navigate to a website
    print("Opening www.google.com")
    driver.get("https://www.google.com")

    # 3. Find an element (e.g., search box) and interact with it
    print("Finding search box and entering text")
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("Ariuntuya Batsaikhan" + Keys.RETURN)

    results = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a:has(h3)"))
    )

    print("Search results:")
    for i, result in enumerate(results[:10], start=1):
        title = result.find_element(By.TAG_NAME, "h3").text.strip()
        link = result.get_attribute("href")
        if title and link:
            print(f"{i}. {title}")
            print(f"   {link}")

    # 4. Close the browser session
    print("Closing Selenium")
    driver.quit()


if __name__ == "__main__":
    main()
