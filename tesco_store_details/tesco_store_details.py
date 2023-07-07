import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import re
import pprint
from tesco_bot import constants as const


class Tesco(webdriver.Chrome):
    def __init__(
        self, driver_path=r"C:/Users/user/Documents/chromedriver.exe", teardown=False
    ):
        self.driver_path = driver_path
        os.environ["PATH"] += self.driver_path
        self.teardown = teardown
        super(Tesco, self).__init__()
        self.implicitly_wait(15)
        self.location_elements = []
        self.concessions_elements = []
        self.store_details = []
        self.filepath = (
            r"C:/Users/keita/OneDrive/Documents/projects/data/json/tesco.json"
        )
        # self.maximize_window()

    def land_first_page(self):
        self.get(const.START_URL)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()

    def __clear_cookies__(self):
        cookie_div = self.find_element(By.CLASS_NAME, "CookieBanner-container")
        cookie_buttons = cookie_div.find_element(By.CLASS_NAME, "CookieBanner-buttons")
        if (
            cookie_buttons.find_element(By.TAG_NAME, "button").get_attribute(
                "innerText"
            )
            == "Accept all cookies"
        ):
            cookie_buttons.find_element(By.TAG_NAME, "button").click()

    def get_store_regions(self):
        if self.find_element(
            By.CSS_SELECTOR, "div.CookieBanner-container"
        ).is_displayed():
            self.__clear_cookies__()

        directory_element = self.find_element(By.CSS_SELECTOR, "a.Locator-toDirectory")
        directory_element.click()
        location_elements = self.find_elements(By.CSS_SELECTOR, "li.Directory-listItem")
        for i, location_element in enumerate(location_elements):
            self.location_elements.append(
                dict(
                    name=location_element.find_element(
                        By.TAG_NAME, "span"
                    ).get_attribute("textContent"),
                    url=location_element.find_element(
                        By.CSS_SELECTOR, "a"
                    ).get_attribute("href"),
                    count=int(
                        re.match(
                            r"\((\d+)\)",
                            location_element.find_element(
                                By.CSS_SELECTOR, "a"
                            ).get_attribute("data-count"),
                        ).group(1)
                    ),
                )
            )
            # if i == 5:
            #     break

    def __get_details_store__(self, url):
        self.get(url)
        lst = []
        store_name_element = self.find_element(By.ID, "location-name")
        address_element = self.find_element(By.ID, "address")
        store_parameters = self.find_element(
            By.CLASS_NAME, "js-datalayer-params"
        ).get_attribute("innerHTML")
        try:
            store_info = self.find_element(By.ID, "storeData").get_attribute(
                "innerHTML"
            )
        except:
            info = None
        else:
            info = self.__parse_details__(store_info)

        try:
            additional_services_element = self.find_element(
                By.CSS_SELECTOR, "div[data-ya-scope='additionalservices']"
            )
        except:
            additional_services_element = None

        else:
            for element in additional_services_element.find_elements(
                By.CSS_SELECTOR, "li.MainServices-listItem"
            ):
                lst.append(element.get_attribute("textContent"))

        self.store_details.append(
            dict(
                store_name=store_name_element.get_attribute("textContent"),
                address=self.__parse_address__(address_element),
                store_parameters=self.__parse_details__(store_parameters),
                store_info=info,
                url=url,
                facilities=lst,
            )
        )
        self.__has_concessions__(self.find_element(By.ID, "main"))

    def __parse_address__(self, address_element):
        addr = []
        address_lines = address_element.find_elements(By.CLASS_NAME, "Address-line")
        for address_line in address_lines:
            addr.append(address_line.get_attribute("textContent"))
        return ", ".join(addr)

    def __has_concessions__(self, element):
        main_services_elements = element.find_elements(
            By.CSS_SELECTOR, "div.MainServices-wrapper"
        )
        for element in main_services_elements:
            element_header = element.find_element(
                By.CSS_SELECTOR, "h2.MainServices-heading.Heading--sub"
            )
            if "What can I find at" in element_header.get_attribute("innerText"):
                element_items = element.find_elements(
                    By.CSS_SELECTOR, "div.MainServices-itemContent"
                )
                for elem in element_items:
                    try:
                        self.concessions_elements.append(
                            elem.find_element(By.CSS_SELECTOR, "a").get_attribute(
                                "href"
                            )
                        )
                    except:
                        print(f"Error: {element_header.get_attribute('innerText')}")
                    break
                break

    def get_concession_details(self):
        if self.concessions_elements:
            for url in self.concessions_elements:
                self.__get_details_store__(url)

    def __parse_details__(self, text):
        regex = r'"([^"]*)":"([^"]*)"'
        matches = re.findall(regex, text)
        return dict(matches)

    def __get_details_stores__(self, url):
        self.get(url)
        try:
            directory_content = self.find_element(
                By.CSS_SELECTOR, "div.Directory-content"
            )
        except:
            print(url)
        else:
            teaser_elements = directory_content.find_elements(
                By.CSS_SELECTOR, "li.Directory-listTeaser"
            )
            lst = []
            for teaser_element in teaser_elements:
                lst.append(
                    teaser_element.find_element(
                        By.CSS_SELECTOR, "a[data-ya-track='link#']"
                    ).get_attribute("href")
                )
            for url in lst:
                self.__get_details_store__(url)

    def write_to_file(self):
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(self.store_details, file, ensure_ascii=False, indent=4)

    def location_list(self):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.store_details)

    def get_store_details(self):
        for location_element in self.location_elements:
            if location_element["count"] > 1:
                self.__get_details_stores__(location_element["url"])
            else:
                self.__get_details_store__(location_element["url"])
