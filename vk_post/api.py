import datetime
from pathlib import Path
from typing import Optional
from abc import abstractmethod, ABC

import aiohttp
import requests

from constants import *


class Post(ABC):
    @abstractmethod
    def posting(cls):
        ...


class PostVKGroup(Post):
    """
    Класс для постинга в группы в социальной сети вконтакте

    Если нужно изменить метод posting так, чтобы, например, удалялись
    все картинки из папки после постинга, то лучше это сделать так:

    class MyPostVKGroup(PostVKGroup):
        def posting(self, path_dir_photos: Path, publish_date=None):
            ...

    Атрибуты:
    ____________________________________________________________________________
        :param personal_token: токен от приложения вконтакте. Создаеть его можно
        тут https://dev.vk.com/ru

        :param group_id: id группы вконтакте без знака минус

        :param version: версия api вконтакте по умолчанию стоит 5.131


    Методы PostVKGroup:
    ____________________________________________________________________________
        :param:  posting


    Вспомогательные методы:
    ____________________________________________________________________________
        :param: _get_wall_upload_server
        :param: _save_wall_photo
        :param: _wall_post
    """

    def __init__(self, personal_token: str, group_id: int, version: str="5.131"):
        self._personal_token = personal_token
        self._group_id = group_id
        self._version = version
        self._params = {
            'access_token': self._personal_token,
            'group_id': self._group_id,
            'v': self._version
        }

    async def posting(self, post_message: str, path_dir_photos: Optional[Path]=None,
                      publish_date: datetime.datetime=None) -> None:
        """
        Основной метод для постинга в группы вконтакте

        :param post_message: сообщение в посте
        :param path_dir_photos: путь до директрии, где фотографии для этого поста
        :param publish_date: дата публикации, если нужно сделать отложенный пост

        :return: None
        """

        async with aiohttp.ClientSession() as session:
            if path_dir_photos is None:
                await self._wall_post(session, post_message, publish_date=publish_date)
            else:
                upload_url = await self._get_wall_upload_server(session)

                attachments = []
                files = path_dir_photos.glob('*')

                for file in files:
                    attachments.append(await self._save_wall_photo(upload_url, file))

                await self._wall_post(session, post_message, ",".join(attachments), publish_date)


    async def _get_wall_upload_server(self, session: aiohttp.ClientSession) -> str:
        async with session.get(URL_WALL_UPLOAD_SERVER, params=self._params) as response:
            upload_url = await response.json()

        return upload_url['response']['upload_url']


    async def _save_wall_photo(self, upload_url: str, path_photo: Path)-> str:
        response = requests.post(upload_url, files={'photo': open(path_photo, "rb")}).json()

        add_params = {
            'photo': response["photo"],
            'server': response['server'],
            'hash': response['hash']
        }

        params = {**self._params, **add_params}

        # Сохраняем картинку на сервере и получаем её идентификатор
        photo_id = requests.get(SAVE_WALL_PHOTO, params=params).json()

        return 'photo' + str(photo_id['response'][0]['owner_id']) + '_' + str(photo_id['response'][0]['id'])


    async def _wall_post(self, session: aiohttp.ClientSession, message: str, attachments: Optional[str]=None,
                         publish_date: Optional[datetime.datetime]=None) -> None:

        add_params = {
            'from_group': 1,
            'message': message
        }

        if attachments is not None:
            add_params['attachments'] = attachments

        if publish_date is not None:
            add_params['publish_date'] = publish_date

        params = {**self._params, **add_params}
        del params['group_id']
        params['owner_id'] = -self._group_id

        await session.get(WALL_POST, params=params)
