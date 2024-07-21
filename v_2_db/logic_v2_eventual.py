import asyncio
from operator import itemgetter

from playwright.async_api import async_playwright
from sqlalchemy import select, and_, func, Table, Result, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from config import today
from crud import write_data
from engine import db_start_sync, local_engine
from v_2_db.model import Base, TriyaData


async def get_max_id(session: AsyncSession, table: DeclarativeAttributeIntercept) -> int:
    result = await session.execute(select(func.max(table.id)))
    r = result.one()
    return int(r[0])


async def parsing_main(browser: async_playwright):
    await db_start_sync(engine=local_engine, base=Base)
    with open('filter.txt', 'r', encoding='utf-8') as file:
        filter_links = [line.strip() for line in file.readlines()]
    print('start scraping www.triya.ru\n DataBase mode')
    context = await browser.new_context()
    page = await context.new_page()
    async with local_engine.scoped_session() as local_session:
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


async def processing_menu(db_session: AsyncSession,
                          page: async_playwright,
                          transmitted_locator: str,
                          page_filter: list,
                          sub_item: dict = None,
                          next_sub: dict = None) -> list | None:
    result = []
    if not sub_item and not next_sub:
        parent = 0
        id_ = 1
        await page.goto(url='https://www.triya.ru/catalog/', wait_until='domcontentloaded')
        menu = await page.locator(transmitted_locator).all()
    else:
        id_ = await get_max_id(session=db_session, table=TriyaData) + 1
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
    data_to_add = await check_links_in_db(session=db_session, table=TriyaData, links=result, parent=parent)
    if data_to_add:
        await write_data(session=db_session, table=TriyaData, data=data_to_add)
    return result


async def check_links_in_db(session: AsyncSession,
                            table: DeclarativeAttributeIntercept,
                            links: list[dict],
                            parent: int) -> bool | list:
    list_links = list()
    [list_links.append(d.get('link')) for d in links]
    query = await session.execute(
        select(table.link).filter(and_(table.link.in_(list_links), (table.parent == parent)))
    )
    result = query.all()
    if len(result) == len(links):
        return False
    for line in result:
        for d in links:
            if line[0] == d.get('link'):
                links.remove(d)
    return links


async def add_products_flag(session: AsyncSession, table: DeclarativeAttributeIntercept):
    subquery = select(table.parent).scalar_subquery()
    query = select(table.id).filter(table.id.notin_(subquery))
    r = await session.execute(query)
    return_result = list(map(itemgetter(0), r.all()))
    stmt = update(table).where(table.id.in_(return_result)).values({'products': True})
    await session.execute(stmt)
    await session.commit()
