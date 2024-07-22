import os
from operator import itemgetter

from sqlalchemy import insert, select, text, Table, Result, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from config import images_path
from v_2_db.model import Base


async def write_data(session: AsyncSession,
                     table: DeclarativeAttributeIntercept,
                     data: list | dict) -> bool:
    await session.execute(insert(table).values(data))
    await session.commit()
    return True


async def get_data(session: AsyncSession, table: DeclarativeAttributeIntercept, **kwargs):
    if kwargs:
        query = select(table).filter(kwargs.get('criteria'))
    else:
        query = select(table)
    res = await session.execute(query)
    return res.scalars().all()


async def truncate_tables(session: AsyncSession,
                          tables: str | list):
    if isinstance(tables, str):
        query = text(f"TRUNCATE {tables}")
        await session.execute(query)
    if isinstance(tables, list):
        for table in tables:
            query = text(f"TRUNCATE {table}")
            await session.execute(query)
    await session.commit()


async def recursive_get_parent(session: AsyncSession, table: str, id_: int) -> dict:
    QUERY = text(f"WITH RECURSIVE CTE as "
                 f"(SELECT id, parent FROM `{table}` d "
                 f"WHERE d.id = {id_} "
                 f"UNION "
                 f"SELECT d2.id, d2.parent FROM `{table}` d2 "
                 f"JOIN CTE ON d2.id = CTE.parent) "
                 f"SELECT * FROM CTE WHERE id != {id_}")
    r: Result = await session.execute(QUERY)
    result = r.all()
    return_data = {'level': len(result), 'path_id': result[0][0] if result else 0}
    return return_data


async def check_links(session: AsyncSession, table: DeclarativeAttributeIntercept) -> list:
    query = select(table.link)
    r: Result = await session.execute(query)
    result = r.fetchall()
    return_result = list(map(itemgetter(0), result))
    return return_result


async def get_product(session: AsyncSession, table: DeclarativeAttributeIntercept, id_: int) -> dict:
    query = select(table.id,
                   table.parent,
                   table.title,
                   table.title_full,
                   table.code,
                   table.link,
                   table.price,
                   table.properties,
                   table.description_text,
                   table.description_props,
                   table.images).filter(table.id == id_)
    r = await session.execute(query)
    result = [row._mapping for row in r.fetchall()]
    result_dict = dict(result[0])
    return result_dict


async def get_products_id(session: AsyncSession, table: DeclarativeAttributeIntercept) -> list:
    folders = os.listdir(images_path)
    folders.remove('.DS_Store')
    folder_list = list(map(int, folders))
    query = select(table.id).filter(and_(table.code != None), (table.code.not_in(folder_list)))
    r = await session.execute(query)
    result = list(map(itemgetter(0), r.fetchall()))
    return result
