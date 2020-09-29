from whatsapp_bot import WhatsappBot
import os
import re
import pathlib
import logging
from datetime import date
import getpass
import json
from subprocess import DEVNULL, STDOUT, check_call
import pyperclip
from urllib.parse import urlencode, quote_plus

def create_log_file(log_level):
    today = date.today().strftime("%Y-%m-%d")
    year = date.today().strftime("%Y")
    month = date.today().strftime("%m")
    log_path = application_path + '/log/{}/{}/'.format(year, month)
    os.makedirs(log_path, exist_ok=True)
    username = getpass.getuser()
    logging.basicConfig(filename=log_path + "/{}_webdocs_migration_{}.log".format(username, today), level=log_level,
                        format='%(asctime)s %(levelname)-8s {}: %(message)s'.format(username),
                        datefmt='%Y-%m-%d %H:%M:%S')
    create_terninal_log_stream(log_level)


def create_terninal_log_stream(log_level):
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(log_level)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

def kill_word_and_chrome():
    # Close all the open chrome and word applications
    try:
        check_call(['taskkill', '/im','winword.exe','/f'], stdout=DEVNULL, stderr=STDOUT)
    except:
        None
    """try:
        check_call(['taskkill', '/im','chromedriver.exe','/f'], stdout=DEVNULL, stderr=STDOUT)
        #os.system("taskkill /im winword.exe /f  > /dev/null")
        #os.system("taskkill /im chromedriver.exe /f  > /dev/null")
    except:
        None"""

def atomic_file_creation(folder, file_name):
    flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
    try:
        file = os.open(folder + file_name, flags)
        os.close(file)
        return True
    except:
        return False

def run_number_extraction(run_config_path):

    # Define try limit
    tries = 1
    limit_tries = 5

    # Create bt variable
    bot = None
    chrome_driver = None

    # Create list variable
    chat_links = None
    saved_numbers = None
    group_name = "Armário"

    with open(run_config_path,'r') as json_file:
        data = json.load(json_file)

    print("Headless:"+str(data['headless']))

    bot, numbers = run_phone_number_bot(group_name, headless=str(data['headless']))

    if not numbers is None:
        chat_links, saved_numbers = create_whatsapp_link(numbers)

    if not chat_links is None:
        for link in chat_links:
            bot.send_message(link)
            print("Message sended!")

    #if not saved_numbers is None:
    #    for name in saved_numbers:
    #        bot.send_message(None, name, group_name)
    #        print("Message sended!")
   
def run_phone_number_bot(group_name, headless=True, chrome_driver=None):
    # Initialize a WhatsappBot and run the bot to get phone number
    
    logging.info('Starting getting phone number')
    kill_word_and_chrome()

    # Implements atomic pyperclip (DONT DELETE)
    pyperclip.copy('***NULL***')
    
    bot = WhatsappBot(headless=headless, chrome_driver=chrome_driver)#XX
    try:
        numbers = bot.get_phone_number(group_name)
    finally:
        print("Retriving phone number finished!")
    
    return bot, numbers


def create_whatsapp_link(numbers):
    chat_links = []
    saved_numbers = []

    for number in numbers:
        print(number)

        if not re.search('[a-zA-Z]', number) is None:
            saved_numbers.append(number)

        else:
            number = number.replace("+", "")
            number = number.replace("(", "")
            number = number.replace(")", "")
            number = number.replace("-", "")
            number = number.replace(" ", "").strip()

            print("https://wa.me/" + number)

            message = "Olá, eu sou um robô!"
            message = quote_plus(message)

            conversation_link = "https://web.whatsapp.com/send?phone=" + number + "&text=" + message + "&source&data&app_absent"

            chat_links.append(conversation_link)

    return chat_links, saved_numbers



# Initialize global variables
application_path = str(pathlib.Path().absolute())
create_log_file(logging.INFO)
documents_source = "C:\\Whatsapp Bot"
run_config_path = application_path+"\\run_config.json"

#Run the cellphone numbers extraction
run_number_extraction(run_config_path)
