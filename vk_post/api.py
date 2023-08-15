import datetime
from pathlib import Path
from typing import Optional
from abc import abstractmethod, ABC

from vkbottle import API
import requests


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

    def __init__(self, personal_token: str, group_id: int):
        self._personal_token = personal_token
        self._group_id = group_id
        self._api = API(token=self._personal_token)

    async def posting(self, post_message: str, path_dir_photos: Optional[Path]=None,
                      publish_date: datetime.datetime=None) -> None:
        """
        Основной метод для постинга в группы вконтакте

        :param post_message: сообщение в посте
        :param path_dir_photos: путь до директрии, где фотографии для этого поста
        :param publish_date: дата публикации, если нужно сделать отложенный пост

        :return: None
        """

        if path_dir_photos is None:
            await self._wall_post(post_message, publish_date=publish_date)
        else:
            attachments = []
            files = path_dir_photos.glob('*')

            for file in files:
                if self._is_video_file(file):
                    upload_url = await self._url_upload_video(file.name)
                    attachments.append(await self._save_upload_video(upload_url, file))
                else:
                    upload_url = await self._get_wall_upload_server()
                    attachments.append(await self._save_wall_photo(upload_url, file))

            await self._wall_post(post_message, ",".join(attachments), publish_date)

    async def _get_wall_upload_server(self) -> str:
        upload_url = await self._api.photos.get_wall_upload_server()
        upload_url = upload_url.dict()
        return upload_url['upload_url']

    async def _save_wall_photo(self, upload_url: str, path_photo: Path)-> str:
        response = requests.post(upload_url, files={'photo': open(path_photo, "rb")}).json()

        # Получаем идентификатор сохраненной фотографии
        photo_info = await self._api.photos.save_wall_photo(
            photo=response["photo"],
            server=response['server'],
            hash=response['hash']
        )

        photo_info = photo_info[0].dict()
        return 'photo' + str(photo_info['owner_id']) + '_' + str(photo_info['id'])

    async def _save_upload_video(self, upload_url: str, path_video: Path):
        video_info = requests.post(upload_url, files={'video_file': open(path_video, "rb")}).json()
        return 'video' + str(video_info['owner_id']) + '_' + str(video_info['video_id'])

    async def _url_upload_video(self, video_name: str) -> str:
        response = await self._api.video.save(name=video_name, group_id=self._group_id)
        return response.dict()['upload_url']

    async def _wall_post(self, message: str, attachments: Optional[str]=None,
                         publish_date: Optional[datetime.datetime]=None) -> None:

        await self._api.wall.post(
            owner_id=-self._group_id,
            message=message,
            attachments=attachments,
            publish_date=publish_date
        )

    def _is_video_file(self, filename: Path):
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        ext = filename.suffix.lower()
        return ext in video_extensions
