from crud import get_data, truncate_tables, write_data, recursive_get_parent
from engine import oc_engine, local_engine
from upload_module import categories
from upload_module.categories.model_category import OCBase, OCCategoryDescription, OCCategory, OCCategoryStore, OCCategoryPath, \
    OCCategoryLayout
from v_2_db.model import TriyaData


async def upload_categories():
    oc_category_result, oc_category_desc, oc_category_path, oc_category_store, oc_category_layout = [], [], [], [], []
    async with oc_engine.engine.begin() as async_connect:
        await async_connect.run_sync(OCBase.metadata.create_all)
    async with local_engine.scoped_session() as local_session:
        r = await get_data(session=local_session, table=TriyaData, criteria=(TriyaData.price == None))
        for line in r:
            oc_category_result.append(
                {'category_id': line.id,
                 'parent_id': line.parent,
                 'top': 0,
                 'column': 1,
                 'sort_order': line.id,
                 'status': 1}
            )
            oc_category_desc.append(
                {'category_id': line.id,
                 'language_id': 1,
                 'name': line.title,
                 'description': '',
                 'meta_title': '',
                 'meta_h1': '',
                 'meta_description': '',
                 'meta_keyword': ''}
            )
            oc_category_store.append(
                {'category_id': line.id,
                 'store_id': 0}
            )
            oc_category_layout.append(
                {'category_id': line.id,
                 'store_id': 0,
                 'layout_id': 0}
            )
            oc_category_path_data = await recursive_get_parent(session=local_session,
                                                               table=TriyaData.__tablename__,
                                                               id_=line.id)
            oc_category_path.append(
                {'category_id': line.id,
                 'path_id': oc_category_path_data.get('path_id'),
                 'level': oc_category_path_data.get('level')}
            )
    async with oc_engine.scoped_session() as oc_session:
        await truncate_tables(session=oc_session, tables=categories.__all__)
        await write_data(session=oc_session, table=OCCategoryDescription, data=oc_category_desc)
        await write_data(session=oc_session, table=OCCategory, data=oc_category_result)
        await write_data(session=oc_session, table=OCCategoryPath, data=oc_category_path)
        await write_data(session=oc_session, table=OCCategoryLayout, data=oc_category_layout)
        await write_data(session=oc_session, table=OCCategoryStore, data=oc_category_store)
