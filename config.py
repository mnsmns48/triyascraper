import os
from datetime import datetime
from pathlib import Path

from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from pydantic_settings import BaseSettings

ua = UserAgent()
today = datetime.now()
root_path = Path(os.path.abspath(__file__)).parent


async def run_browser(playwright: async_playwright) -> async_playwright:
    browser = await playwright.chromium.launch(headless=False)
    return browser


class DBConfig(BaseSettings):
    db_host: str
    db_username: str
    db_password: str
    db_local_port: int
    db_name: str


local_config = DBConfig(_env_file=f'{root_path}/settings_local.env')
oc_config = DBConfig(_env_file=f'{root_path}/settings_oc.env')
images_path = "/Volumes/Orico/images/"
