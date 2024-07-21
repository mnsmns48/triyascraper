import json
import os
import excel_format

from xlsxwriter import Workbook
from xlsxwriter.worksheet import Worksheet


async def create_json(file: str, data: list):
    with open(f'{file}.json', 'w') as file:
        file.write(json.dumps(data, indent=2, ensure_ascii=False))


async def update_json(file: str, data: list):
    json_data = json.load(open(f"{file}.json"))
    json_data.append(data)
    with open(f"{file}.json", "w") as file:
        json.dump(json_data, file, indent=2, ensure_ascii=False)


async def read_json(file: str) -> list | None:
    try:
        with open(f'{file}.json', 'r') as file:
            json_data = json.load(file)
        return json_data
    except FileNotFoundError:
        with open(f'{file}.json', 'w') as file:
            file.close()
        return None


async def json_collector() -> list:
    files = list()
    for file in os.listdir():
        if 'json' in file and 'menu' not in file:
            files.append(file)
    files.sort()
    return files


async def excel_writer(files: list, workbook: Workbook):
    worksheet = workbook.add_worksheet()
    worksheet.outline_settings(symbols_below=False, auto_style=False)
    menu_cells = workbook.add_format(excel_format.main_format)
    link_cells = workbook.add_format(excel_format.link_format)
    sub_menu_1_cells = workbook.add_format(excel_format.sub_menu_1_format)
    sub_menu_2_cells = workbook.add_format(excel_format.sub_menu_2_format)
    product_cells = workbook.add_format(excel_format.product_format)
    price_cells = workbook.add_format(excel_format.price_format)
    row = 0
    for file in files:
        data: list = await read_json(file=file.split('.json')[0])
        await write_menu(menu=data[0], worksheet=worksheet, row=row, sub_menu_cells=menu_cells, link_cells=link_cells)
        row += 1
        if data[0].get('sub_menu'):
            for sub_menu in data[0].get('sub_menu'):
                await write_menu(menu=sub_menu, worksheet=worksheet, row=row,
                                 sub_menu_cells=sub_menu_1_cells,
                                 link_cells=link_cells)
                row += 1
                if sub_menu.get('sub_menu'):
                    for sub_menu2 in sub_menu.get('sub_menu'):
                        await write_menu(menu=sub_menu2, worksheet=worksheet, row=row,
                                         sub_menu_cells=sub_menu_2_cells,
                                         link_cells=link_cells)
                        row += 1
                        start_row = row
                        for product in sub_menu2.get('products'):
                            await write_product(product=product, worksheet=worksheet, row=row,
                                                product_cells=product_cells,
                                                price_cells=price_cells,
                                                link_cells=link_cells)
                            row += 1
                        end_row = row
                        for row_ in range(start_row, end_row):
                            worksheet.set_row(row_, None, None, {'level': 1, 'hidden': True})
                if sub_menu.get('products'):
                    start_row = row
                    for product in sub_menu.get('products'):
                        await write_product(product=product, worksheet=worksheet, row=row,
                                            product_cells=product_cells,
                                            price_cells=price_cells,
                                            link_cells=link_cells)
                        row += 1
                    end_row = row
                    for row_ in range(start_row, end_row):
                        worksheet.set_row(row_, None, None, {'level': 1, 'hidden': True})
    worksheet.set_column(2, 3, 20)
    worksheet.autofit()
    workbook.close()


async def write_menu(menu: dict, worksheet: Worksheet, row: int, **kwargs):
    worksheet.write(row, 0, menu['title'], kwargs.get('sub_menu_cells'))
    worksheet.write(row, 1, None, kwargs.get('sub_menu_cells'))
    worksheet.write(row, 2, None, kwargs.get('sub_menu_cells'))
    worksheet.write(row, 3, None, kwargs.get('sub_menu_cells'))
    worksheet.write(row, 4, menu['link'], kwargs.get('link_cells'))


async def write_product(product: dict, worksheet: Worksheet, row: int, **kwargs):
    column = 0
    id_ = product['link'].split('?model=')[1]
    worksheet.write(row, column, product['title'], kwargs.get('product_cells'))
    worksheet.write(row, column + 1, product['title_full'], kwargs.get('product_cells'))
    worksheet.write(row, column + 2, int(id_), kwargs.get('product_cells'))
    worksheet.write(row, column + 3, int(product['price'].replace(' ', '')), kwargs.get('price_cells'))
    worksheet.write(row, column + 4, product['link'], kwargs.get('link_cells'))
    column = 5
    if product.get('../images'):
        images = list()
        for line in product.get('../images'):
            if line:
                images.append(line)
        worksheet.write(row, column, f"{id_}:[{','.join(images)}]", kwargs.get('link_cells'))
        column += 1
    if product.get('description_text'):
        worksheet.write(row, column, str(product['description_text']), kwargs.get('product_cells'))
        column += 1
    if product.get('properties'):
        worksheet.write(row, column, str(product['properties']), kwargs.get('product_cells'))
        column += 1
    if product.get('description_list'):
        worksheet.write(row, column, str(product['description_list']), kwargs.get('product_cells'))
