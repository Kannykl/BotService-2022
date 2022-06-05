"""Vk service module"""
from abc import ABC
from abc import abstractmethod

from services.vk.bots_creation.bots import BotData
from services.vk.bots_creation.bots import CreateVkBotsService
from services.vk.stat_boost.vk_boost import VKBoostService


class SocialNetService(ABC):
    """Social net service"""

    @abstractmethod
    def create_bot(self):
        """Create bots in social net"""

    @abstractmethod
    def boost_statistics(self, link: str, boost_type: str, bot: dict):
        """Boost stat in social net"""


class VKService(SocialNetService):
    """Vk service"""

    BOOST_TYPE1: str = "like"
    BOOST_TYPE2: str = "sub"

    def __init__(self, bot_service: CreateVkBotsService):
        self.bot_service = bot_service

    def create_bot(self) -> BotData:
        """Create bots.

        Args:
        Returns:
            BotData
        """

        data = self.bot_service.generate_data_for_bot()

        bot_data = self.bot_service.register_bot(data)

        return bot_data

    def boost_statistics(self, link: str, boost_type: str, bot: dict) -> None:
        """Boost stat in vk.

        Args:
            link(str): Link for profile/post.
            boost_type(str): boost type like/sub.
            bot(dict): bots_data.

        Returns:
            None
        """

        if boost_type == VKService.BOOST_TYPE1:
            VKBoostService(bot["username"], bot["password"]).like_post(link)

        else:
            VKBoostService(bot["username"], bot["password"]).subscribe(link)
