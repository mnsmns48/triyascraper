import asyncio
import os
from operator import itemgetter

from sqlalchemy import insert, select, text, Table, Result, and_, update, func, Column
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


async def get_products_id(session: AsyncSession, table: DeclarativeAttributeIntercept, limit: int | None) -> list:
    query = select(table.id).filter(table.code != None).limit(limit)
    r = await session.execute(query)
    result = list(map(itemgetter(0), r.fetchall()))
    return result


async def update_attr_groups(session: AsyncSession,
                             attr_table_desc: DeclarativeAttributeIntercept,
                             attr_table: DeclarativeAttributeIntercept,
                             group_attr: list) -> dict:
    query = select(attr_table_desc.attribute_group_id,
                   attr_table_desc.name).filter(attr_table_desc.name.in_(group_attr))
    r = await session.execute(query)
    result = [row._mapping for row in r.fetchall()]
    result_dict = dict()
    if len(result) == len(group_attr):
        for line in result:
            result_dict.update({line.get('name'): line.get('attribute_group_id')})
        return result_dict
    else:
        for line in result:
            group_attr.remove(line.get('name'))
        to_add_desc = list()
        to_add_ = list()
        attribute_group_id = await get_max_id(session=session, column=attr_table_desc.attribute_group_id)
        for attr in group_attr:
            to_add_desc.append({'attribute_group_id': attribute_group_id + 1,
                                'language_id': 1,
                                'name': attr})
            to_add_.append({'attribute_group_id': attribute_group_id + 1,
                            'sort_order': attribute_group_id + 1})
            attribute_group_id += 1
        stmt = insert(attr_table_desc).values(to_add_desc)
        await session.execute(stmt)
        stmt2 = insert(attr_table).values(to_add_)
        await session.execute(stmt2)
        to_add_desc.extend(result)
        for line in to_add_desc:
            result_dict.update({line.get('name'): line.get('attribute_group_id')})
        return result_dict


async def update_attr(session: AsyncSession,
                      table_desc: DeclarativeAttributeIntercept,
                      table: DeclarativeAttributeIntercept,
                      props: dict) -> dict:
    to_desc = list()
    to_attr = list()
    result_dict = dict()
    attribute_id = await get_max_id(session=session, column=table_desc.attribute_id)
    for key, value in props.items():
        query = select(table_desc.attribute_id,
                       table_desc.name).filter(table_desc.name.in_(value))
        r = await session.execute(query)
        result = [row._mapping for row in r.fetchall()]
        if len(value) == len(result):
            [result_dict.update({line.get('name'): line.get('attribute_id')}) for line in result]
        else:
            for line in result:
                value.remove(line.get('name'))
            for attr in value:
                to_desc.append({'attribute_id': attribute_id + 1,
                                'language_id': 1,
                                'name': attr
                                })
                to_attr.append({'attribute_id': attribute_id + 1,
                                'sort_order': attribute_id + 1,
                                'attribute_group_id': key})
                attribute_id += 1
            await asyncio.sleep(0.5)
            stmt = insert(table_desc).values(to_desc)
            await session.execute(stmt)
            stmt2 = insert(table).values(to_attr)
            await session.execute(stmt2)
            for line in to_attr:
                result_dict.update({line.get('name'): line.get('attribute_id')})
    return result_dict


async def get_max_id(session: AsyncSession, column: Column) -> int:
    result = await session.execute(select(func.max(column)))
    r = result.one()
    if r[0] is not None:
        return int(r[0])
    else:
        return 0
