
import time
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import logging
import re
import pyperclip
import os, sys
from PIL import Image as Image_Aux
from PIL import BmpImagePlugin, GifImagePlugin, Jpeg2KImagePlugin, JpegImagePlugin, PngImagePlugin, TiffImagePlugin, WmfImagePlugin  # added this line
import csv
import pymsgbox


def atomic_pyperclip(self, element, copy_element):
    ''' Function to use pyperclip atomic, to implement parallelism'''

    #while pyperclip.paste() != "***NULL***":
    #    pass
    pyperclip.copy(copy_element)
    element.send_keys(Keys.CONTROL, 'v')
    pyperclip.copy('***NULL***')
    return True

class WhatsappBot():
    """ Whatsapp Bot Input Class"""

    def __init__(self, timeout=15,headless = False,chrome_driver=None):
        
        self.driver = self.get_driver(headless, chrome_driver)
        
        self.timeout = timeout
        self.headless = headless

        self.url = "https://web.whatsapp.com/"


    def get_driver(self, headless, chrome_driver=None):
        driver_options = Options()
        if headless:
            #driver_options.add_argument("--headless")# headless function
            driver_options.add_argument("window-size=1980,1080")# To render the headless chrome right
            #driver_options.add_argument("--disable-gpu")# Temporary necessary on windows machine
            #driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("--log-level=3")# Allow only js warings and erros in the console
            #driver_options.add_argument("--start-maximized")
            
        else:
            driver_options.add_argument("--start-maximized")
        
        driver_options.add_experimental_option("detach", True)
        
        if chrome_driver is not None:
            SELENIUM_PORT=9515

            executor_url = chrome_driver.command_executor._url
            session_id = chrome_driver.session_id

            capabilities = driver_options.to_capabilities()
            driver = webdriver.Remote(command_executor=executor_url, desired_capabilities=capabilities)
            # prevent annoying empty chrome windows
            driver.close()
            driver.quit() 

            # attach to existing session
            driver.session_id = session_id
        else:
            driver = Chrome(chrome_options=driver_options)

        return driver

    def get_credentials(self):
        return [line.rstrip() for line in open("../Config/credentials.txt", "r")]

    def get_doc_special_id(self, doc_code):
        with open("Consolidated_Bases\\ims_portal_docs_ids.csv",'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')

            #Creates a dictionary of: column_names -> column_index
            header = next(csv_reader)
            columns = {}
            for i in range(0, len(header)):
                columns[header[i]] = i

            for row in csv_reader:
                if row[columns["Document Code"]] == doc_code:
                    return row[columns["Document Id"]]
        
        return ""

    def get_doc_active_revision(self, doc_code):
        with open("Consolidated_Bases\\ims_portal_docs_ids.csv",'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')

            #Creates a dictionary of: column_names -> column_index
            header = next(csv_reader)
            columns = {}
            for i in range(0, len(header)):
                columns[header[i]] = i

            for row in csv_reader:
                if row[columns["Document Code"]] == doc_code:
                    return row[columns["Active Revision"]]
        
        return ""

    def get_document_url(self):
        """ Gets specific IMS Portal URL for Document Editting"""
        
        prefix = "http://10.12.8.14/Workflow/OnlineDocuments?"
        document_pattern = re.compile("([0-9]){4}-([A-Z]){3}([0-9]){2}-([A-Z]|[0-9]){4}-([0-9]){4}(\s|\.|,|;|$)+")
        doc_code = document_pattern.search(self.web_document.document_path).group(0).strip()
        doc_id = f"documentId={self.get_doc_special_id(doc_code)}"
        language = f"TypeLanguage={self.language}"
        revision = f"revision={self.get_doc_active_revision(doc_code)}"
        req = "UrlToReturn=EditDocument"

        return prefix + "&".join([doc_id, language, revision, req])

    def get_last_attach_seq(self,doc_path):
        with open("Consolidated_Bases\\ims_portal_docs_ids.csv",'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            document_pattern = re.compile("([0-9]){4}-([A-Z]){3}([0-9]){2}-([A-Z]|[0-9]){4}-([0-9]){4}(\s|\.|,|;|$)+")
            doc_code = document_pattern.search(doc_path).group(0).strip()
            #Creates a dictionary of: column_names -> column_index
            header = next(csv_reader)
            columns = {}
            for i in range(0, len(header)):
                columns[header[i]] = i

            for row in csv_reader:
                if row[columns["Document Code"]] == doc_code:
                    return int(row[columns["LastAttachSeq"]])
            
        return int(0)

    def wait_then_click_xpath(self, html, path):
        try:
            element = html.find_element_by_xpath(path)
            WebDriverWait(html, self.timeout).until(EC.element_to_be_clickable((By.XPATH, path)))
            try: # try by using the library Actions
                ActionChains(self.driver).move_to_element(element).perform()
                element.click()
            except: #Try by using javascript code
                element = html.find_element_by_xpath(path)
                WebDriverWait(html, self.timeout).until(EC.element_to_be_clickable((By.XPATH, path)))
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", element)# move to the correct position
                    time.sleep(2)
                    element.click()
                except: # Try to move the cursor up and click it 
                    element = html.find_element_by_xpath(path)
                    WebDriverWait(html, self.timeout).until(EC.element_to_be_clickable((By.XPATH, path)))
                    self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
                    time.sleep(0.5)
                    ActionChains(self.driver).move_to_element(element).perform()
                    element.click()
            return element
        except:
            logging.info('Failed to click.')

    def search_group(self, group_name):

        try:
            # Search chat
            #self.driver.find_element_by_css_selector('span[title="' + group_name + '"]').click()
            self.driver.find_elements_by_xpath('//*[contains(@title, "' + group_name + '")]')[0].click()
            time.sleep(2)

            # Get phone numbers
            numbers = self.driver.find_element_by_css_selector('#main > header > div._33QME > div._2ruUq._3xjAz > span').text.split(", ")
        except:    
            logging.error("Failed to get phone numbers. Trying again!")

            search = self.driver.find_element_by_xpath("//*[@id='side']/div[1]/div/label/div/div[2]")
            search.clear()
            atomic_pyperclip(self, search, group_name)
            #self.driver.find_element_by_css_selector('span[title="' + group_name + '"]').click()
            self.driver.find_elements_by_xpath('//*[contains(@title, "' + group_name + '")]')[0].click()
            time.sleep(2)

            numbers = self.driver.find_element_by_css_selector('#main > header > div._33QME > div._2ruUq._3xjAz > span').text.split(", ")

        return numbers


    def get_phone_number(self, group_name):
        # Navigate to whatsapp webpage
        self.driver.get(self.url)

        try:
            element_present = EC.presence_of_element_located((By.ID, 'app'))
            WebDriverWait(self.driver, self.timeout).until(element_present)
            time.sleep(2)
        except:
            print("Timed out waiting for page to load")

        try:
            if not self.driver.find_element_by_xpath("//*[@id='app']/div/div/div[2]/div[1]/div/div[2]/div/canvas") is None:
                pymsgbox.alert('Por favor active su whatsapp en la computadora y después haz clic Ok!', 'Atención!')
        except:
            logging.info("Whastapp was already logged!")

        try:
            numbers = self.search_group(group_name)
            time.sleep(3)
        except:
            numbers = None
            logging.info("Problem accessing whatsapp group.")
        
        return numbers

    def send_message(self, link, saved_contact=None):
        
        if not saved_contact is None:
            try:
                # Search chat
                #self.driver.find_element_by_css_selector('span[title="' + group_name + '"]').click()
                self.driver.find_elements_by_xpath('//*[contains(@title, "' + saved_contact + '")]')[1].click()
                time.sleep(2)

            except:    
                logging.error("Does not have contact chat.")

                search = self.driver.find_element_by_xpath("//*[@id='side']/div[1]/div/label/div/div[2]")
                search.clear()
                atomic_pyperclip(self, search, saved_contact)
                #self.driver.find_element_by_css_selector('span[title="' + group_name + '"]').click()
                self.driver.find_elements_by_xpath('//*[contains(@title, "' + saved_contact + '")]')[1].click()
                time.sleep(2)

        else:
            # Navigate to whatsapp webpage
            print(link)
            self.driver.get(link)

        # Click send
        if self.wait_element_until_appear("//*[@id='main']/footer/div[1]/div[3]/button"):
            time.sleep(1)
            self.wait_then_click_xpath(self.driver, "//*[@id='main']/footer/div[1]/div[3]/button")

    def wait_element_until_appear(self, element_xpath):
        loop = 0
        while loop < self.timeout:   
            try:
                time.sleep(1)
                self.wait_then_click_xpath(self.driver, element_xpath)
                loop = self.timeout
            except:
                loop += 1
                return False
        return True