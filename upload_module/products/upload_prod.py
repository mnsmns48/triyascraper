import asyncio
import json
import random

from config import today
from crud import check_links, get_products_id, get_product, update_attr_groups, update_attr, truncate_tables, write_data
from engine import local_engine, oc_engine
from upload_module import products, OCProduct, OCProductDesc, OCProductCategory, OCProductStore, OCProductLayout, \
    OCProductAttr
from upload_module.attributes import OCAttrGroupDesc, OCAttrGroup, OCAttr, OCAttrDesc
from v_2_db.model import TriyaData


async def upload_products():
    async with oc_engine.scoped_session() as oc_session:
        # await truncate_tables(session=oc_session, tables=products.__all__)
        async with local_engine.scoped_session() as local_session:
            products_id = await get_products_id(session=local_session, table=TriyaData, limit=1)
            for id_ in products_id:
                product_dict = await get_product(session=local_session, table=TriyaData, id_=id_)
                if product_dict.get('properties'):
                    props = json.loads(product_dict.get('properties'))
                    groups = await update_attr_groups(session=oc_session,
                                                      attr_table_desc=OCAttrGroupDesc,
                                                      attr_table=OCAttrGroup,
                                                      group_attr=list(props.keys()))
                    props_dict = dict()
                    for group in list(groups.keys()):
                        props_list = list()
                        for attr in props.get(group):
                            props_list.append(list(attr.keys())[0])
                        props_dict.update({groups.get(group): props_list})
                    attributes = await update_attr(session=oc_session,
                                                   table_desc=OCAttrDesc,
                                                   table=OCAttr,
                                                   props=props_dict)
                sort = 1
                oc_product = {
                    'product_id': product_dict.get('code'),
                    'model': product_dict.get('code'),
                    'sku': f"17216{str(random.randint(10000, 99999))}",
                    'upc': '',
                    'ean': '',
                    'jan': '',
                    'isbn': '',
                    'mpn': '',
                    'location': '',
                    'quantity': 1,
                    'stock_status_id': 7,
                    'image': '',
                    'manufacturer_id': 127,
                    'shipping': 1,
                    'price': product_dict.get('price'),
                    'points': 0,
                    'tax_class_id': 0,
                    'date_available': today,
                    'weight': 0,
                    'weight_class_id': 1,
                    'length': 0,
                    'width': 0,
                    'height': 0,
                    'length_class_id': 1,
                    'subtract': 1,
                    'minimum': 1,
                    'sort_order': sort,
                    'status': 1,
                    'date_added': today,
                    'date_modified': today
                }
                oc_product_description = {
                    'product_id': product_dict.get('code'),
                    'language_id': 1,
                    'name': product_dict.get('title_full'),
                    'description': product_dict.get('description_text'),
                    'tag': '',
                    'meta_title': '',
                    'meta_h1': '',
                    'meta_description': '',
                    'meta_keyword': ''
                }
                oc_product_category = {
                    'product_id': product_dict.get('code'),
                    'category_id': product_dict.get('parent'),
                    'main_category': 2
                }
                oc_product_store = {
                    'product_id': product_dict.get('code'),
                    'store_id': 0
                }
                oc_product_layout = {
                    'product_id': product_dict.get('code'),
                    'store_id': 0,
                    'layout_id': 0
                }
                oc_product_attribute = list()
                for key, value in props.items():
                    for p in value:
                        k = list(p.keys())[0]
                        oc_product_attribute.append({
                            'product_id': product_dict.get('code'),
                            'attribute_id': attributes.get(k),
                            'language_id': 1,
                            'text': p.get(k)})
                sort += 1
                await write_data(session=oc_session, table=OCProduct, data=oc_product)
                await write_data(session=oc_session, table=OCProductDesc, data=oc_product_description)
                await write_data(session=oc_session, table=OCProductCategory, data=oc_product_category)
                await write_data(session=oc_session, table=OCProductStore, data=oc_product_store)
                await write_data(session=oc_session, table=OCProductLayout, data=oc_product_layout)
                await write_data(session=oc_session, table=OCProductAttr, data=oc_product_attribute)
