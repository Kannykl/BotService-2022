"""Bots creation module"""

from abc import ABC, abstractmethod

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from services.vk.bots_creation.phone_stock import PhoneStockService
from selenium import webdriver
from passwordgenerator import pwgenerator
import random
from mimesis import Person
from mimesis.enums import Gender, Locale
from core.config import logger
import undetected_chromedriver as uc


MONTHS: tuple = (
    "Января",
    "Февраля",
    "Марта",
    "Апреля",
    "Мая",
    "Июня",
)

SEX: tuple = (0, 1)


class CreateBotsService(ABC):
    """Create bots service"""

    @abstractmethod
    async def register_bot(self, data):
        """Register bot in social net"""

    @staticmethod
    @abstractmethod
    async def generate_data_for_bot():
        """Generate data for registration"""


class CreateVkBotsService(CreateBotsService):
    """Create bots in VK social net"""

    MAIN_PAGE: str = "https://vk.com/"

    TIME_OUT: int = 10
    NAME_INPUT: str = "vkc__TextField__input"
    SURNAME_INPUT: str = "vkc__TextField__input"
    SEX_BTN: str = "vkc__Switcher__button"
    BIRTHDAY_SELECTOR: str = "vkc__Select__customContainer"
    PASSWRD_INPUT: str = "Input__el"
    CODE_INPUT: str = "vkc__TextField__input"
    PHONE_INPUT: str = "vkc__TextField__input"
    ERROR_WINDOW: str = "error"
    CALL_MSG: str = "join_called_phone_wrap"
    RESEND_LINK: str = "join_resend_lnk"
    SKIP_LINK: str = "join_skip_link"
    CONTINUE_BTN: str = "vkc__Button__title"
    REGISTRATE_BTN: str = "VkIdForm__button"
    NOT_VALID_ACCOUNT: str = "vkc__EnterPasswordHasUserInfo__link"
    BTN: str = "vkuiButton__content"
    PAGE: str = "page_name"
    SOCIAL_NET: str = "vk"

    PAGE_LOAD_STRATEGY: str = "eager"

    def __init__(self, phone_stock: PhoneStockService) -> None:
        """Init phone stock and set up driver.

        Args:
            phone_stock(PhoneStock): phone stock.
        """

        self.phone_stock = phone_stock
        self._setup_driver()

    async def register_bot(self, data: tuple) -> tuple[str, str] | int:
        """Register bot in a social net.

        Args:
            data(list): generated data.

        Returns:
            phone(str): phone for login.
            password(str): account password.
        """

        driver = self.driver
        driver.get(CreateVkBotsService.MAIN_PAGE)

        try:
            name, surname, sex = data[0], data[1], data[2]

            phone = await self.phone_stock.buy_phone(CreateVkBotsService.SOCIAL_NET)
            return_code = await self._phone_input(phone)

            if return_code:
                return -1

            code = await self._get_sms_or_call()
            await self._input_code(code, phone)

            await self._input_generated_data(name, surname, sex)

            password = await self._set_password()

            return phone, password

        except NoSuchElementException as e:
            logger.error(str(e))

    def _setup_driver(self) -> None:
        """Set up driver.

        Args:
        Returns:
            None
        """

        options = uc.ChromeOptions()
        options.add_argument("--headless")

        self.driver = uc.Chrome(version_main=100, options=options)
        self.driver.implicitly_wait(5)

    async def _input_generated_data(self, name: str, surname: str, sex: int) -> None:
        """Input generated data in a form.

        Args:
            name(str): name.
            surname(str): surname.
            sex(int): sex.

        Returns:
            None
        """

        driver = self.driver

        name_input = driver.find_elements(By.CLASS_NAME, CreateVkBotsService.NAME_INPUT)[0]
        name_input.send_keys(name)

        surname_input = driver.find_elements(By.CLASS_NAME, CreateVkBotsService.SURNAME_INPUT)[1]
        surname_input.send_keys(surname)

        sex_buttons = driver.find_elements(By.CLASS_NAME, CreateVkBotsService.SEX_BTN)

        if sex == 0:
            sex_buttons[0].click()

        else:
            sex_buttons[1].click()

        driver.find_element(By.CLASS_NAME, CreateVkBotsService.CONTINUE_BTN).click()

        birthday_selectors = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.BIRTHDAY_SELECTOR
        )

        day = birthday_selectors[0]
        month = birthday_selectors[1]
        year = birthday_selectors[2]

        webdriver.ActionChains(driver).move_to_element(day).click().move_by_offset(
            0, 100
        ).click().perform()
        webdriver.ActionChains(driver).move_to_element(month).click().move_by_offset(
            0, 100
        ).click().perform()
        webdriver.ActionChains(driver).move_to_element(year).click().move_by_offset(
            0, 100
        ).click().perform()

        driver.find_element_by_class_name(CreateVkBotsService.CONTINUE_BTN).click()

        try:
            WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, CreateVkBotsService.PAGE)
                )
            )
        except TimeoutException:
            logger.info("Bot is created.")

    async def _phone_input(self, phone: str) -> int | None:
        """Phone input in a form.

        Args:
            phone(str): Phone number.

        Returns:
            -1 or None: -1 if phone number is not valid.
        """

        driver = self.driver

        registrate_button = driver.find_elements_by_class_name(CreateVkBotsService.REGISTRATE_BTN)[1]
        registrate_button.click()

        phone_input = WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, CreateVkBotsService.PHONE_INPUT))
        )

        phone_input.send_keys(phone + Keys.ENTER)

        try:
            WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, CreateVkBotsService.ERROR_WINDOW)
                )
            )

            logger.error(f"{phone} is not valid")
            driver.quit()

            return -1

        except TimeoutException:
            logger.info(f"{phone} is valid")

    async def _get_sms_or_call(self) -> str:
        """Get code from sms or call.

        Returns:
            code(str): Код.
        """

        driver = self.driver

        try:
            WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, CreateVkBotsService.CALL_MSG)
                )
            )

            code = self.phone_stock.get_code()

            if not code:
                sms_btn = WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                    EC.presence_of_element_located(
                        (By.ID, CreateVkBotsService.RESEND_LINK)
                    )
                )
                sms_btn.click()

        except TimeoutException:
            code = self.phone_stock.get_code()

            if not code:
                sms_btn = WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                    EC.presence_of_element_located(
                        (By.ID, CreateVkBotsService.RESEND_LINK)
                    )
                )

                sms_btn.click()

        code = await self.phone_stock.get_code()

        return code

    async def _input_code(self, code: str, phone: str) -> None:
        """Input code in a form.

        Args:
            code(str): code for registration.
            phone(str): phone number.

        Returns:
            None
        """

        driver = self.driver

        if code:
            code_input = WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, CreateVkBotsService.CODE_INPUT))
            )

            code_input.send_keys(code + Keys.ENTER)

            try:
                WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, CreateVkBotsService.NOT_VALID_ACCOUNT)
                    )
                )

                logger.error(f"{phone} is not valid")
                driver.close()

            except TimeoutException:
                logger.info(f"{phone} is valid")

        else:
            logger.error(f"{phone} doesnt receive a code")
            driver.close()

    async def _set_password(self):
        """Set password for new account."""
        driver = self.driver
        driver.get("https://id.vk.com/account/#/password-change")

        call_me = driver.find_element(By.CLASS_NAME, CreateVkBotsService.BTN)
        call_me.click()

        continue_btn = driver.find_elements(By.TAG_NAME, "button")[1]
        continue_btn.click()

        code = await self.phone_stock.get_code()

        code_input = driver.find_element(By.CLASS_NAME, CreateVkBotsService.PASSWRD_INPUT)
        code_input.send_keys(code)

        passwrd = pwgenerator.generate()
        password_inputs = driver.find_elements(By.CLASS_NAME, CreateVkBotsService.PASSWRD_INPUT)
        password_inputs[0].send_keys(passwrd)
        password_inputs[1].send_keys(passwrd)

        save_btn = driver.find_element(By.CLASS_NAME, CreateVkBotsService.BTN)
        save_btn.click()

        return passwrd

    @staticmethod
    async def generate_data_for_bot() -> tuple[str, str, int]:
        """Generate data.

        Returns:
            name(str): name.
            surname(str): surname.
            birthdate(str): birth date.
            sex(int): sex.
        """

        man = Person(locale=Locale.RU)
        sex = random.choice(SEX)

        if sex == 0:
            name = man.first_name(gender=Gender.MALE)
            surname = man.last_name(gender=Gender.MALE)

        else:
            name = man.first_name(gender=Gender.FEMALE)
            surname = man.last_name(gender=Gender.FEMALE)

        return name, surname, sex
