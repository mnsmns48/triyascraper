import json

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import today
from v_1_json.logic import get_main_menu
from crud import write_data, check_links
from engine import db_start_sync, local_engine
from v_2_db.model import Base, TriyaData


async def scraper_main_db(page: async_playwright):
    await db_start_sync(engine=local_engine, base=Base)
    with open('filter.txt', 'r', encoding='utf-8') as file:
        filter_links = [line.strip() for line in file.readlines()]
    async with local_engine.scoped_session() as local_session:
        filter_links_db = await check_links(session=local_session, table=TriyaData)
    if filter_links_db:
        filter_links.extend(filter_links_db)
    MENU_URL = 'https://www.triya.ru/catalog/'
    print('start scraping www.triya.ru\n DataBase mode')
    main_menu = await get_main_menu(url=MENU_URL, page=page, transmitted_locator="xpath=//div[@class='divider-header']",
                                    filter=filter_links)
    for line in main_menu:
        line['parsing_date'] = today
        line['parent'] = 0
    async with local_engine.scoped_session() as db_session:
        if main_menu:
            await write_data(session=db_session, table=TriyaData, data=main_menu)
        main_menu_db = await get_menu(session=db_session, parent=0, not_in=False)
        for sub_menu_item in main_menu_db:
            await page.goto(url=sub_menu_item.link, wait_until='domcontentloaded')
            menu = await page.locator("xpath=//a[contains(@class, 'element')][not(contains(@href, '/?model='))]").all()
            for category in menu:
                link = f"https://www.triya.ru{await category.get_attribute('href')}"
                if link not in filter_links:
                    sub_menu_result = {'title': await category.text_content(),
                                       'link': link,
                                       'parent': sub_menu_item.id,
                                       'parsing_date': today}
                    await write_data(session=db_session, table=TriyaData, data=sub_menu_result)
        sub_menu_db = await get_menu(session=db_session, parent=0, not_in=True)
        for sub_line in sub_menu_db:
            await page.goto(url=sub_line.link, wait_until='domcontentloaded')
            child_menu = await page.locator("xpath=//a[@class='tag']").all()
            if child_menu:
                for child_menu_item in child_menu:
                    link = f"https://www.triya.ru{await child_menu_item.get_attribute('href')}"
                    if link not in filter_links:
                        sub_child_result = {'title': await child_menu_item.text_content(),
                                            'link': link,
                                            'parent': sub_line.id,
                                            'parsing_date': today}
                        await write_data(session=db_session, table=TriyaData, data=sub_child_result)
                        child_sub_db = await get_menu(session=db_session, parent=sub_line.id, not_in=False)
                        for child_sub_item in child_sub_db:
                            products = await pars_product_list_db(url=child_sub_item.link, page=page,
                                                                  parent=child_sub_item.id)
                            await write_data(session=db_session, table=TriyaData, data=products)
            else:
                products = await pars_product_list_db(url=sub_line.link, page=page, parent=sub_line.id)
                [await write_data(session=db_session,
                                  table=TriyaData,
                                  data=product_item) for product_item in products]


async def get_menu(session: AsyncSession, parent: int, not_in: bool):
    if not_in:
        query = select(TriyaData).filter(TriyaData.parent != parent)
    else:
        query = select(TriyaData).filter(TriyaData.parent == parent)
    result: Result = await session.execute(query)
    main_menu_set = result.scalars()
    return main_menu_set


async def pars_product_list_db(url: str, page: async_playwright, parent: int) -> list:
    consolidated_product_list = list()
    await page.goto(url=url, wait_until='domcontentloaded')
    pagination = await page.locator("xpath=//a[@class='pagination-link']").nth(-1).is_visible()
    if pagination:
        total_pages = await page.locator("xpath=//a[@class='pagination-link']").nth(-1).inner_text()
    else:
        total_pages = 1
    page_number = 1
    while page_number != int(total_pages) + 1:
        if page_number != 1:
            link = f"{url}?page={page_number}"
            await page.goto(link, wait_until='domcontentloaded')
        products = await page.locator("xpath=//div[@class='catalog-offers-grid']").inner_html()
        prod_list = await process_bs4_db(product_list=products, page=page, parent=parent)
        [consolidated_product_list.append(product) for product in prod_list]
        page_number += 1
    print(url, 'added')
    # print(consolidated_product_list)
    return consolidated_product_list


async def process_bs4_db(product_list: str, page: async_playwright, **kwargs) -> list:
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
                        'price': int(price.text.strip().replace(' ', '')) if price else None})
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
            product.update({'properties': json.dumps(properties, indent=2, ensure_ascii=False)})
        if description:
            descriptions = full_soup.find_all('td', {'colspan': 1})
            if len(descriptions) > 0:
                long_text = descriptions[0].text.strip()
                product.update({'description_text': long_text})
            if len(descriptions) > 1:
                description_props = list()
                for key in descriptions[1].find_all('strong'):
                    description_props.append({key.text: key.next_sibling.text if key.next_sibling else None})
                product.update({'description_props': json.dumps(description_props, indent=2, ensure_ascii=False)})
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
                        'images': json.dumps({'images': list(images)}),
                        'parsing_date': today,
                        'code': url.split('?model=')[1]})
        result.append(product)
    return result
