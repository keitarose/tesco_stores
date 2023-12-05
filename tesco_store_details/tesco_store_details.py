import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import os
import re
import pprint
import pandas as pd
import random
import time
from tesco_store_details import constants as const


class Tesco(uc.Chrome):
    def __init__(
        self,
        driver_path=r"C:/Users/keita/OneDrive/Documents/projects/selenium/chrome_driver",
        teardown=False,
    ):
        self.driver_path = driver_path
        os.environ["PATH"] += self.driver_path
        self.teardown = teardown
        super(Tesco, self).__init__()
        self.implicitly_wait(15)
        self.location_elements = []
        self.concessions_elements = []
        self.store_details = []
        self.request_count = 0
        self.consession_count = 0
        self.store_filepath = const.STORE_DATA_FILEPATH
        self.location_filepath = const.LOCATION_DATA_FILEPATH

        # self.maximize_window()

    def land_first_page(self):
        self.get(const.START_URL)
        self.__clear_cookies__()

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
            cookie_buttons.find_element(By.TAG_NAME, "button").submit()

    def get_store_regions(self):
        pattern = re.compile("\d+")
        # if self.find_element(
        #     By.CSS_SELECTOR, "div.CookieBanner-container"
        # ).is_displayed():
        #     self.__clear_cookies__()

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
                        pattern.search(
                            location_element.find_element(
                                By.CSS_SELECTOR, "a"
                            ).get_attribute("data-count")
                        ).group(0)
                    ),
                )
            )
            # if i == 20:
            #     break
        with open(self.location_filepath, "w", encoding="utf-8") as file:
            json.dump(self.location_elements, file, ensure_ascii=False, indent=4)

    def __get_details_store__(self, url, restart=False):
        self.get(url)
        lst = []
        mode = "w"
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
        self.request_count += 1
        if self.request_count % 100 == 0:
            print(f"Request count: {self.request_count}")
            if restart:
                mode = "a"
            with open(self.store_filepath, mode, encoding="utf-8") as file:
                json.dump(self.store_details, file, ensure_ascii=False, indent=4)

            time.sleep(random.randint(5, 15))
        return 1

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
        if len(main_services_elements)==0:
            return
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
                        if elem.find_element(By.TAG_NAME, "a").get_attribute(
                            "innerText"
                        ) == "Learn more":
                            self.concessions_elements.append(
                                elem.find_element(By.TAG, "a").get_attribute(
                                    "href"
                                )
                            )
                    except:
                        print(element_header.get_attribute("innerText"))
                        print(
                            f"Concession: {elem.find_element(By.TAG_NAME, 'h3').get_attribute('innerText')}"
                        )

    def get_concession_details(self, from_file=False, start_at=0, restart=False):
        if from_file:
            with open(const.CONCESSION_DATA_FILEPATH, "r") as fp:
                self.concessions_elements = fp.read().splitlines()[start_at:]

        if self.concessions_elements:
            for url in self.concessions_elements:
                self.__get_details_store__(url)

    def __parse_details__(self, text):
        regex = r'"([^"]*)":"([^"]*)"'
        matches = re.findall(regex, text)
        return dict(matches)

    def __get_details_stores__(self, url):
        self.get(url)
        count = 0
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
                count += self.__get_details_store__(url)
        return count

    def write_to_file(self, ):
        with open(self.store_filepath, "w", encoding="utf-8") as file:
            json.dump(self.store_details, file, ensure_ascii=False, indent=4)

    def location_list(self):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.store_details)

    def get_store_details(self):
        location_df = pd.read_json(self.location_filepath, orient="records")
        # location_elements = location_df["url"]
        for _, location_element in location_df.copy().iterrows():
            if location_element["count"] > 1:
                location_df.loc[i, "return_count"] = self.__get_details_stores__(location_element["url"])
            else:
                location_df.loc[i, "return_count"] = self.__get_details_store__(location_element["url"])
            location_df.to_json(self.location_filepath, orient="records", indent=4)
        self.concession_count = len(self.concessions_elements)
        with open(const.CONCESSION_DATA_FILEPATH, "w") as fp:
            fp.write("\n".join(self.concessions_elements))

