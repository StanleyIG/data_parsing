import os
import time
import random
import hashlib
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


class EmailParser:
    def __init__(self, count_mails=5):
        self.EMAIL = os.getenv('LOGIN')
        self.PASSWORD = os.getenv('PASS')
        self.count_mails = count_mails
        self.mails_list = []
        self.ids = set()
        self.driver = None

    def login(self):
        service = Service('./chromedriver.exe')
        self.driver = webdriver.Chrome(service=service)

        self.driver.implicitly_wait(5)
        self.driver.get('https://e.mail.ru/templates/')
        time.sleep(3)

        login = self.driver.find_element(By.NAME, 'username')
        login.send_keys(self.EMAIL)
        login.submit()
        time.sleep(1)

        password = self.driver.find_element(By.NAME, 'password')
        password.send_keys(self.PASSWORD)
        password.submit()
        time.sleep(1)

    # Прокрутка страницы с помощью колесика мыши
    def scroll_page_with_mouse_wheel(self, driver, mail):
        driver.execute_script("arguments[0].scrollIntoView()", mail)
        

    def parse_emails(self):
        while len(self.mails_list) != self.count_mails:
            time.sleep(0.5 + random.uniform(0.5, 2))
            mails = self.driver.find_elements(
                By.XPATH, '//a[contains(@class, "llc")]')
            mail_links = [mail.get_attribute('href') for mail in mails]

            for i, link in enumerate(mail_links):
                mail_dict = {}
                try:
                    _id = hashlib.sha256(link.encode()).hexdigest()
                    if _id in self.ids:
                        continue
                    else:
                        self.ids.add(_id)
                        mail_dict['title'] = mails[i].text
                        self.mails_list.append(mail_dict)
                        self.driver.execute_script("window.scrollBy(0, 100);")
                        # Открываю новую вкладку для письма
                        self.driver.execute_script(
                            "window.open('about:blank', '_blank');")
                        self.driver.switch_to.window(
                            self.driver.window_handles[1])
                        self.driver.get(link)
                        time.sleep(1)
                        # Обработка письма
                        self.driver.implicitly_wait(5)
                        wait = WebDriverWait(self.driver, 3)
                        _from = wait.until(EC.presence_of_element_located((By.XPATH, '//div['
                                                    '@class="letter__author"]//span[@class="letter-contact"]')))
                        mail_dict['from'] = _from.get_attribute('title')

                        mail_dict['date'] = self.driver.find_element(By.XPATH, '//div[@class="letter__author"]//div['
                                                                               '@class="letter__date"]').text

                        mail_text_elements = self.driver.find_elements(By.XPATH, '//div[@class="letter__body"]//tbody')
                        if mail_text_elements:
                            mail_text_elements = self.driver.find_elements(By.XPATH,
                                                                           '//div[@class="letter__body"]//tbody//a')
                            mail_links = [(mail.get_attribute('href'), mail.text) for mail in mail_text_elements if
                                          mail.get_attribute('href')]
                            mail_link = '\n'.join([f'ссылка на контент: {href}: текст контента: {text}' for href, text in mail_links])
                            mail_dict['link'] = mail_link if mail_link else None
                            elements = wait.until(
                                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="letter__body"]//tbody//tr')))
                            mail_tbody_content = ""
                            for element in elements:
                                for tr_element in element.find_elements(By.XPATH, './/td|th'):
                                    mail_tbody_content += tr_element.text + " "
                            mail_dict['text'] = mail_tbody_content if mail_tbody_content else None

                        else:
                            mail_text = self.driver.find_elements(By.XPATH, '//div[@class="letter__body"]//p')
                            mail_text = '\n'.join([text.text for text in mail_text])
                            mail_dict['text'] = mail_text if mail_text else None
                            link_elements = self.driver.find_elements(By.XPATH, '//div[@class="letter__body"]//a')
                            mail_links = [(mail.get_attribute('href'), mail.text) for mail in link_elements if
                                          mail.get_attribute('href')]
                            mail_link = '\n'.join([f'ссылка на контент: {href}: текст контента: {text}' for href, text in mail_links])
                            mail_dict['link'] = mail_link if mail_link else None

                        # Закрываю вкладку письма
                        self.driver.close()
                        self.driver.switch_to.window(
                            self.driver.window_handles[0])
                        self.driver.implicitly_wait(3)
                        time.sleep(1)

                        # Прокручиваю страницу вниз с помощью колесика мыши
                        self.scroll_page_with_mouse_wheel(
                            self.driver, mails[i])
                        time.sleep(1)

                        # Проверяю длину списка после добавления письма
                        if len(self.mails_list) == self.count_mails:
                            break

                except TimeoutException:
                    continue

                except StaleElementReferenceException:
                    mails = self.driver.find_elements(
                        By.XPATH, '//a[contains(@class, "llc")]')
                    continue

                except WebDriverException:
                    mails = self.driver.find_elements(
                        By.XPATH, '//a[contains(@class, "llc")]')
                    continue

    def write_to_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(self.mails_list, file,
                      ensure_ascii=False, indent=4)

    def add_to_mongodb(self):
        FILENAME = 'mails3.json'
        if os.path.exists(FILENAME):
            with open(FILENAME, 'r', encoding='utf-8')as file:
                data = json.load(file)
        client = MongoClient('mongodb://localhost:27017/')
        db = client['database']
        mails = db['email']
        for mail in data:
            if mails.find_one({"link": mail["link"]}) is None:
                mail['date_added'] = datetime.now().strftime("%d.%m.%Y")
                mails.insert_one(mail)
        return mails


# по умолчанию колличество сообщений определено в размере 10, при необходимости
# передать объекту класса парсера своё значение EmailParser(50)
parser = EmailParser(60)
parser.login()
parser.parse_emails()
parser.write_to_json('mails3.json')
# parser.add_to_mongodb()
