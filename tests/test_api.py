import asyncio
import datetime
import sys
import time
from pathlib import Path

from environs import Env

from vk_post.api import PostVKGroup


dotenv_path = Path(__file__).parent.parent.absolute() / '.env'

if Path.exists(dotenv_path):
    env = Env()
    env.read_env()
else:
    sys.exit(0)


async def test_posting():

    group_id = 215794226
    personal_token = env.str("PERSONAL_TOKEN")
    post = PostVKGroup(personal_token, group_id)

    await post.posting("hello")
    print("Пост 1")
    time.sleep(30)

    publish_date = datetime.datetime(2023, 8, 15, 17, 16).timestamp()
    await post.posting("hello", publish_date=publish_date)
    print("Пост 2")
    time.sleep(30)

    await post.posting("hello", path_dir_photos=Path("/home/alexander/PycharmProjects/vk_post/tests/photos"))
    print("Пост 3")
    time.sleep(30)

    publish_date = datetime.datetime(2023, 8, 15, 17, 15).timestamp()
    await post.posting("hello", path_dir_photos=Path("/home/alexander/PycharmProjects/vk_post/tests/photos"),
                       publish_date=publish_date)
    print("Пост 4")
    time.sleep(30)


asyncio.run(test_posting())
