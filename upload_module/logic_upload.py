from config import local_config
from crud import recursive_get_parent
from engine import local_engine
from upload_module.categories.upload_cat import upload_categories
from upload_module.products.upload_prod import upload_products
from v_2_db.model import TriyaData


async def upload():
    # await upload_categories()
    await upload_products()
