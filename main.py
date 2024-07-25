import asyncio
import time
from datetime import datetime

from playwright.async_api import async_playwright

from config import run_browser
from upload_module.logic_upload import upload
from v_2_db.logic_v2_eventual import parsing_main


async def main():
    print('Начало работы')
    # async with async_playwright() as playwright:
    #     browser = await run_browser(playwright=playwright)
    #     await parsing_main(browser=browser)
    await upload()

if __name__ == "__main__":
    try:
        start = time.time()
        print('script started', datetime.now())
        asyncio.run(main())
        print(f"Скрипт завершен за {int(time.time() - start)} секунд")
    except (KeyboardInterrupt, SystemExit):
        print('script stopped')
