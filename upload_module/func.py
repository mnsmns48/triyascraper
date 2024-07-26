import json
import os

from playwright.async_api import async_playwright

from config import images_path


async def get_image(page: async_playwright, product: dict):
    images = json.loads(product.get('images')).get('images')
    count = 1
    path_title = str(product.get('code'))
    if not os.path.exists(f'/Volumes/Orico/images/{path_title}'):
        os.mkdir(f'{images_path}{path_title}')
    for img in images:
        if img:
            await page.goto(url=img, wait_until='domcontentloaded')
            await page.locator("img").screenshot(path=f"{images_path}{path_title}/{path_title}_{count}.jpg")
            count += 1


async def json_to_text(json_data: json) -> str:
    result = '&lt;/p&gt;&lt;p&gt;'
    dict_list = json.loads(json_data)
    for line in dict_list:
        result += ' '.join(f'{k} {v}' for k, v in line.items()) + '&lt;/p&gt;&lt;p&gt;'
    return result
