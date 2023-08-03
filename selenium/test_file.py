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
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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

    def parse_emails(self):
        mails = self.driver.find_elements(By.XPATH, '//a[contains(@class, "llc")]')
        while len(self.mails_list) != self.count_mails:
            time.sleep(0.5 + random.uniform(0.5, 2))
            i = 0
            while i < len(mails):
                mail_dict = {}
                try:
                    link = mails[i].get_attribute('href')
                    _id = hashlib.sha256(link.encode()).hexdigest()
                    if _id in self.ids:
                        i += 1
                        continue
                    else:
                        self.ids.add(_id)
                        mail_dict['title'] = mails[i].text
                        self.mails_list.append(mail_dict)

                        mails[i].click()
                        self.driver.implicitly_wait(5)
                        time.sleep(3)
                    
                except StaleElementReferenceException:
                    mails = self.driver.find_elements(By.XPATH, '//a[contains(@class, "llc")]')
                    continue

                except TimeoutException:
                    continue

                self.driver.back()
                time.sleep(1)
                i += 1
                if len(self.mails_list) == self.count_mails:
                            break


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
parser = EmailParser(5)
parser.login()
parser.parse_emails()
parser.write_to_json('mails3.json')
#parser.add_to_mongodb()