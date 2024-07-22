import json
import os

from playwright.async_api import async_playwright

from config import root_path


async def get_image(page: async_playwright, product: dict):
    images = json.loads(product.get('images')).get('images')
    count = 1
    path_title = str(product.get('code'))
    if not os.path.exists(f'/Volumes/Orico/images/{path_title}'):
        os.mkdir(f'/Volumes/Orico/images/{path_title}')
    for img in images:
        if img:
            await page.goto(url=img, wait_until='domcontentloaded')
            await page.locator("img").screenshot(path=f"/Volumes/Orico/images/{path_title}/{path_title}_{count}.jpg")
            # print(f"{path_title} downloaded")
            count += 1
