"""Phone stock module"""

import json
from abc import ABC, abstractmethod
import time

import requests
from onlinesimru import GetNumbers
from services.vk.exceptions import PhoneStockUnavailableException
from core.config import settings


class PhoneStockService(ABC):
    """Service for interaction with phone stock"""

    @abstractmethod
    def buy_phone(self, social_net: str):
        """Buy a phone number"""

    @abstractmethod
    def get_code(self):
        """Get the code from sms/call"""


class OnlineSimPhoneStockService(PhoneStockService):
    """Service for onlinesim.ru phone stock"""

    RESPONSE: str = "TZ_NUM_ANSWER"
    BASE_API_URL: str = "http://onlinesim.ru/api/getState.php?apikey="
    MAX_RETRY: int = 4

    def __init__(self):
        self.tzid = None

    def _get_phone_data(self) -> list:
        """Return info about the purchased phone.

        Returns:
            data(list): Info about phone.
        """
        response = requests.get(
            f"{OnlineSimPhoneStockService.BASE_API_URL}"
            f"{settings.PHONE_STOCK_API_KEY}&tzid={self.tzid}"
        )

        if response.status_code != 200:
            raise PhoneStockUnavailableException(
                f"Phone stock status code {response.status_code}"
            )

        data = json.loads(response.content)

        return data

    def buy_phone(self, social_net: str) -> str:
        """Buy phone for registration.

        Args:
            social_net(str): Social net title.

        Returns:
            phone(str): Phone number.
        """

        worker = GetNumbers(settings.PHONE_STOCK_API_KEY)

        self.tzid = worker.get(social_net)

        data = self._get_phone_data()

        phone = data[0]["number"][2:]

        return phone

    def get_code(self) -> str | None:
        """Get the code from sms/call

        Returns:
            code(int): code from sms/call or None.
        """
        try:
            data = self._get_phone_data()

        except PhoneStockUnavailableException:
            return None

        count = 0

        while data[0]["response"] != OnlineSimPhoneStockService.RESPONSE:
            count += 1

            if count - 1 == OnlineSimPhoneStockService.MAX_RETRY:
                return None

            time.sleep(30)

            data = self._get_phone_data()

        try:
            code = data[0]["msg"]

            if len(code) > 10:
                code = code[8:]

            return code

        except KeyError:
            return None
