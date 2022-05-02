"""Phone stock module"""

import json
from abc import ABC, abstractmethod
import time

import requests
from core.config import settings
from onlinesimru import GetNumbers


class PhoneStockService(ABC):
    """Service for interaction with phone stock"""

    @abstractmethod
    async def buy_phone(self, social_net: str):
        """Buy a phone number"""

    @abstractmethod
    async def get_code(self):
        """Get the code from sms/call"""


class OnlineSimPhoneStockService(PhoneStockService):
    """Service for onlinesim.ru phone stock"""

    RESPONSE: str = "TZ_NUM_ANSWER"
    BASE_API_URL: str = "http://onlinesim.ru/api/getState.php?apikey="
    MAX_RETRY: int = 4

    def __init__(self):
        self.tzid = None

    async def _get_phone_data(self) -> list:
        """Return info about the purchased phone.

        Returns:
            data(list): Info about phone.
        """

        data = json.loads(
            requests.get(
                f"{OnlineSimPhoneStockService.BASE_API_URL}{settings.PHONE_STOCK_API_KEY}&tzid={self.tzid}"
            ).content
        )

        return data

    async def buy_phone(self, social_net: str) -> str:
        """Buy phone for registration.

        Args:
            social_net(str): Social net title.

        Returns:
            phone(str): Phone number.
        """

        worker = GetNumbers(settings.PHONE_STOCK_API_KEY)

        self.tzid = worker.get(social_net)

        data = await self._get_phone_data()

        phone = data[0]["number"][2:]

        return phone

    async def get_code(self) -> str | None:
        """Get the code from sms/call

        Returns:
            code(int): code from sms/call or None.
        """

        data = await self._get_phone_data()
        print(data)
        count = 0

        while data[0]["response"] != OnlineSimPhoneStockService.RESPONSE:
            time.sleep(30)
            count += 1

            data = await self._get_phone_data()
            print(data)

            if count == OnlineSimPhoneStockService.MAX_RETRY:
                return None

        try:
            code = data[0]["msg"]

            if len(code) > 10:
                code = code[8:]

            return code

        except KeyError:
            return None
