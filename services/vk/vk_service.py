"""Vk service module"""

from abc import ABC, abstractmethod
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.exceptions import StopBoostException, StopCreatingBotsException
from services.vk.stat_boost.vk_boost import VKBoostService


class SocialNetService(ABC):
    """Social net service"""

    @abstractmethod
    def create_bots(self, count: int):
        """Create bots in social net"""

    @abstractmethod
    def boost_statistics(
        self, link: str, wished_count: int, boost_type: str, data: list
    ):
        """Boost stat in social net"""


class VKService(SocialNetService):
    """Vk service"""

    BOOST_TYPE1: str = "like"
    BOOST_TYPE2: str = "sub"

    def __init__(self, bot_service: CreateVkBotsService):
        self.bot_service = bot_service

    def create_bots(self, count: int) -> list:
        """Create bots.

        Args:
            count(int): bots count.

        Returns:
            None
        """
        bots_info = []

        for _ in range(int(count)):
            data = self.bot_service.generate_data_for_bot()

            try:
                phone, password = self.bot_service.register_bot(data)
                bots_info.append((phone, password))

            except StopCreatingBotsException:
                continue

        return bots_info

    def boost_statistics(
        self, link: str, wished_count: int, boost_type: str, data: list
    ) -> None:
        """Boost stat in vk.

        Args:
            link(str): Link for profile/post.
            wished_count(int): Count of like/subs.
            boost_type(str): boost type like/sub.
            data(str): bots_data.

        Returns:
            None
        """

        count_of_bots = len(data)

        if count_of_bots < int(wished_count):
            wished_count = count_of_bots

        for bot in data:

            if wished_count != 0:

                if boost_type == VKService.BOOST_TYPE1:
                    try:
                        VKBoostService(bot["username"], bot["password"]).like_post(link)

                    except StopBoostException:
                        continue

                elif boost_type == VKService.BOOST_TYPE2:
                    try:
                        VKBoostService(bot["username"], bot["password"]).subscribe(link)

                    except StopBoostException:
                        continue

            wished_count -= 1
