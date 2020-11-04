import databases
from .settings import settings

database = databases.Database(settings.db_url)
