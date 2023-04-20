from os import sep, getenv
from os.path import dirname, abspath
from dotenv import load_dotenv
load_dotenv()

base_dir = dirname(abspath(__file__)) + sep
database_dir = base_dir + "databases" + sep

api_token = getenv("BOT_TOKEN")
group_id = -0
