import os

import xlsxwriter
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from config import today
from v_1_json.func_excel import create_json, read_json, json_collector, excel_writer


async def scraper_main(page: async_playwright):
    if not os.path.exists('../images'):
        os.mkdir('../images')
    os.rmdir('../images')
    os.mkdir('../images')
    with open('../filter.txt', 'r', encoding='utf-8') as file:
        filter_links = [line.strip() for line in file.readlines()]
    print('start scraping www.triya.ru\nCreating a menu structure')
    MENU_URL = 'https://www.triya.ru/catalog/'
    main_menu = await get_main_menu(url=MENU_URL, page=page, transmitted_locator="xpath=//div[@class='divider-header']",
                                    filter=filter_links)
    sub_menu_locator = "xpath=//a[contains(@class, 'element')][not(contains(@href, '/?model='))]"
    for sub in main_menu:
        sub_1 = await get_sub1(url=sub['link'], page=page, transmitted_locator=sub_menu_locator, filter=filter_links)
        sub.update({'sub_menu': sub_1})
    for sub in main_menu:
        for sub_1 in sub['sub_menu']:
            if sub_1['link']:
                sub_1_child = await get_sub1_child(url=sub_1['link'],
                                                   page=page,
                                                   transmitted_locator="xpath=//a[@class='tag']",
                                                   filter=filter_links)
                if sub_1_child:
                    sub_1.update({'sub_menu': sub_1_child})
    print('Menu OK')
    await create_json(file='menu', data=main_menu)
    main_menu.clear()
    main_menu = await read_json(file='menu')
    counter = 0
    for product_group in main_menu:
        result = await add_products_in_menu(menu=[product_group], result=[], page=page)
        await create_json(file=f"00{counter}_{result[0]['title']}", data=result)
        counter += 1
        print('------------')
    json_files = await json_collector()
    workbook = xlsxwriter.Workbook(f"{today}.xlsx")
    await excel_writer(files=json_files, workbook=workbook)
    print('Done')


async def get_main_menu(url: str, page: async_playwright, transmitted_locator: str, **kwargs) -> list:
    menu_result = list()
    await page.goto(url=url, wait_until='domcontentloaded')
    menu = await page.locator(transmitted_locator).all()
    for category in menu:
        link = f"https://www.triya.ru{await category.get_by_role('link').get_attribute('href')}"
        if link not in kwargs.get('filter'):
            menu_result.append({'title': await category.text_content(),
                                'link': link})
    return menu_result


async def get_sub1(url: str, page: async_playwright, transmitted_locator: str, **kwargs) -> list:
    menu_result = list()
    if url not in kwargs.get('filter'):
        await page.goto(url=url, wait_until='domcontentloaded')
        menu = await page.locator(transmitted_locator).all()
        for category in menu:
            link = f"https://www.triya.ru{await category.get_attribute('href')}"
            if link not in kwargs.get('filter'):
                menu_result.append({'title': await category.text_content(),
                                    'link': link})
    return menu_result


async def get_sub1_child(url: str, page: async_playwright, transmitted_locator: str, **kwargs) -> list | None:
    sub_1_child_result = list()
    if url not in kwargs.get('filter'):
        await page.goto(url=url, wait_until='domcontentloaded')
        menu = await page.locator(transmitted_locator).all()

        if menu:
            for category in menu:
                link = f"https://www.triya.ru{await category.get_attribute('href')}"
                if link not in kwargs.get('filter'):
                    sub_1_child_result.append({'title': await category.text_content(),
                                               'link': link})
        return sub_1_child_result


async def add_products_in_menu(menu: list, result: list, page: async_playwright) -> list:
    for item in menu:
        result.append(item)
        sub_menu = item.get('sub_menu')
        if sub_menu:
            await add_products_in_menu(menu=sub_menu, result=[], page=page)
        else:
            products = await pars_products(item=item, page=page)
            item.update({'products': products})
    return result


async def pars_products(item: dict, page: async_playwright) -> list:
    consolidated_product_list = list()
    await page.goto(url=item.get('link'), wait_until='domcontentloaded')
    pagination = await page.locator("xpath=//a[@class='pagination-link']").nth(-1).is_visible()
    if pagination:
        total_pages = await page.locator("xpath=//a[@class='pagination-link']").nth(-1).inner_text()
    else:
        total_pages = 1
    page_number = 1
    while page_number != int(total_pages) + 1:
        link = item['link']
        if page_number != 1:
            link = f"{item.get('link')}?page={page_number}"
            await page.goto(link, wait_until='domcontentloaded')
        products = await page.locator("xpath=//div[@class='catalog-offers-grid']").inner_html()
        prod_list = await process_bs4(product_list=products, page=page)
        [consolidated_product_list.append(product) for product in prod_list]
        page_number += 1
    print(item['title'], 'added')
    return consolidated_product_list


async def process_bs4(product_list: str, page: async_playwright, **kwargs) -> list:
    soup = BeautifulSoup(markup=product_list, features='lxml')
    products = soup.findAll('div', {'itemtype': 'http://schema.org/Product'})
    result = list()
    for prod in products:
        product = dict()
        title = prod.find('span', {'itemprop': 'name'})
        url = f"https://www.triya.ru{prod.find('a').get('href')}"
        price = prod.find('span', {'class': 'price currency'})
        product.update({'link': url,
                        'title': title.text.strip() if title else None,
                        'price': price.text.strip() if price else None})
        if kwargs.get('parent'):
            product.update({'parent': kwargs.get('parent')})
        await page.goto(url, wait_until='domcontentloaded')
        show_more = await page.locator("xpath=//span[@class='show-more-button']").is_visible()
        if show_more:
            await page.locator("xpath=//span[@class='show-more-button']").click()
        description = await page.locator("xpath=//div[@class='link'][contains(text(), 'Описание')]").is_visible()
        if description:
            await page.locator("xpath=//div[@class='link'][contains(text(), 'Описание')]").click()
        full_page = await page.locator("xpath=//div[@class='offer-page body']").inner_html()
        full_soup = BeautifulSoup(markup=full_page, features='lxml')
        title_full = full_soup.find('h1')
        if show_more:
            props = full_soup.find_all('section', {'class': 'prop-group'})
            properties = dict()
            for prop_group in props:
                prop_bold = prop_group.header.text.strip()
                props = prop_group.find_all('div', {'class': 'prop'})
                props_list = list()
                for prop in props:
                    prop_name = prop.find('span', {'class': 'name'}).text
                    prop_value = prop.contents[-1].text.strip().replace(' ', '')
                    props_list.append({prop_name: prop_value})
                properties.update({prop_bold: props_list})
            product.update({'properties': properties})
        if description:
            descriptions = full_soup.find_all('td', {'colspan': 1})
            if len(descriptions) > 0:
                long_text = descriptions[0].text.strip()
                product.update({'description_text': long_text})
            if len(descriptions) > 1:
                description_list = list()
                for key in descriptions[1].find_all('strong'):
                    description_list.append({key.text: key.next_sibling.text if key.next_sibling else None})
                product.update({'description_list': description_list})
        images = set()
        image_html = full_soup.find('div', {'class': ['swiper-container',
                                                      'thumbs-slider',
                                                      'swiper-container-initialized',
                                                      'swiper-container-horizontal',
                                                      'swiper-container-pointer-events',
                                                      'swiper-container-thumbs']})
        for image in image_html.find_all('div', {'class': 'swiper-slide'}):
            images.add('https:' + image.find('img').get('src') if image.find('img') else None)
        product.update({'title_full': title_full.text.strip(),
                        'images': list(images)})
        result.append(product)
    return result
