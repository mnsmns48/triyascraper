import json
import os
from operator import itemgetter
from typing import Sequence

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from sqlalchemy import select, and_, Result, update, Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from config import today, images_path
from crud import write_data, get_product, get_max_id
from engine import db_start_sync, local_engine
from upload_module.image_download import get_image
from v_2_db.model import Base, TriyaData


async def parsing_main(browser: async_playwright):
    await db_start_sync(engine=local_engine, base=Base)
    with open('filter.txt', 'r', encoding='utf-8') as file:
        filter_links = [line.strip() for line in file.readlines()]
    print('start scraping www.triya.ru\n DataBase mode')
    context = await browser.new_context()
    page = await context.new_page()
    async with local_engine.scoped_session() as local_session:
        query = select(TriyaData.id).filter(TriyaData.id == 1)
        r = await local_session.execute(query)
        result: Result = r.fetchall()
        if not result:
            await write_data(session=local_session, table=TriyaData,
                             data={'parsing_date': today, 'id': 1, 'title': 'Главное меню', 'parent': 0})
        main_menu = await processing_menu(db_session=local_session,
                                          page=page,
                                          transmitted_locator="xpath=//div[@class='divider-header']",
                                          page_filter=filter_links)

        for sub_menu in main_menu:
            sub_result = await processing_menu(db_session=local_session, page=page, sub_item=sub_menu,
                                               transmitted_locator="xpath=//a[contains(@class, 'element')]"
                                                                   "[not(contains(@href, '/?model='))]",
                                               page_filter=filter_links)
            for sub_next_menu in sub_result:
                _sub = await processing_menu(db_session=local_session, page=page,
                                             sub_item=sub_menu,
                                             next_sub=sub_next_menu,
                                             transmitted_locator="xpath=//a[@class='tag']",
                                             page_filter=filter_links)
        await add_products_flag(session=local_session, table=TriyaData)
        print('Menu structure is ready')
        links_with_products = await get_product_list(session=local_session, table=TriyaData)
        for link in links_with_products:
            products = await pars_product_list_db(url=link.link, page=page, parent=link.id)
            [await write_data(session=local_session,
                              table=TriyaData,
                              data=product_item) for product_item in products]
        #  D O W N L O A D   I M A G E S #
        folders = os.listdir(images_path)
        folders.remove('.DS_Store')
        folder_list = list(map(int, folders))
        query = select(TriyaData.id).filter(and_(TriyaData.code != None), (TriyaData.code.not_in(folder_list)))
        r = await local_session.execute(query)
        product_list_id = list(map(itemgetter(0), r.fetchall()))
        c = len(product_list_id)
        for id_ in product_list_id:
            product = await get_product(session=local_session, table=TriyaData, id_=id_)
            await get_image(product=product, page=page)
            c -= 1
            print(id_, c)


async def processing_menu(db_session: AsyncSession,
                          page: async_playwright,
                          transmitted_locator: str,
                          page_filter: list,
                          sub_item: dict = None,
                          next_sub: dict = None) -> list | None:
    result = []
    if not sub_item and not next_sub:
        parent = 0
        id_ = 2
        await page.goto(url='https://www.triya.ru/catalog/', wait_until='domcontentloaded')
        menu = await page.locator(transmitted_locator).all()
    else:
        id_ = await get_max_id(session=db_session, column=TriyaData.id) + 1
        if sub_item and not next_sub:
            parent = sub_item.get('id')
            await page.goto(url=sub_item.get('link'), wait_until='domcontentloaded')
            menu = await page.locator(transmitted_locator).all()
        else:
            parent = next_sub.get('id')
            await page.goto(url=next_sub.get('link'), wait_until='domcontentloaded')
            menu = await page.locator(transmitted_locator).all()
            if not menu:
                return None
    for category in menu:
        if sub_item or next_sub:
            link = f"https://www.triya.ru{await category.get_attribute('href')}"
        else:
            link = f"https://www.triya.ru{await category.get_by_role('link').get_attribute('href')}"
        if link not in page_filter:
            result.append({'id': id_,
                           'title': await category.text_content(),
                           'link': link,
                           'parsing_date': today,
                           'parent': parent})

            id_ += 1
    data_to_add = await check_links_in_db(session=db_session, table=TriyaData, links=result)
    if data_to_add:
        await write_data(session=db_session, table=TriyaData, data=data_to_add)
    return result


async def check_links_in_db(session: AsyncSession,
                            table: DeclarativeAttributeIntercept,
                            links: list[dict]) -> bool | list:
    list_links = list()
    [list_links.append(d.get('link')) for d in links]
    query = await session.execute(
        select(table.link).filter(table.link.in_(list_links))
    )
    result = query.all()
    if len(result) == len(links):
        return False
    for line in result:
        for d in links:
            if line[0] == d.get('link'):
                links.remove(d)
    return links


async def add_products_flag(session: AsyncSession, table: DeclarativeAttributeIntercept) -> None:
    subquery = select(table.parent).scalar_subquery()
    query = select(table.id).filter(table.id.notin_(subquery))
    r = await session.execute(query)
    return_result = list(map(itemgetter(0), r.all()))
    stmt = update(table).where(and_(table.id.in_(return_result), (table.id != 1))).values({'products': True})
    await session.execute(stmt)
    await session.commit()


async def get_product_list(session: AsyncSession, table: DeclarativeAttributeIntercept) -> Sequence[Row[tuple]]:
    query = select(table.id, table.link).filter(table.products == 1)
    r = await session.execute(query)
    result = r.all()
    return result


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
