import os
import pathlib

from dotenv import load_dotenv, find_dotenv
from selenium.webdriver.chrome.options import Options


# --- Подгружаем переменные окружения, обновляя существующие с предыдущего запуска
load_dotenv(find_dotenv(), override=True, verbose=True)

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
token = os.getenv("TOKEN")
chat_id = os.getenv("CHAT_ID")
proxy = os.getenv("PROXY")

BASE_DIR = pathlib.Path(__file__).parent.absolute()
chromedriver = str(BASE_DIR) + '/chromedriver'
cookies = str(BASE_DIR) + f'/{username}_cookies'

proxy_options = {
    "proxy": {
        "https": f"{proxy}"
    }
}

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
