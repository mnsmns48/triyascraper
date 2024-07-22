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



