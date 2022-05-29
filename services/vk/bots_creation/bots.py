"""Bots creation module"""
import random
from abc import ABC
from abc import abstractmethod
from typing import NamedTuple

from mimesis import Person
from mimesis.enums import Gender
from mimesis.enums import Locale
from passwordgenerator import pwgenerator
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from core.config import logger
from services.vk.bots_creation.phone_stock import PhoneStockService
from services.vk.exceptions import PhoneStockUnavailableException
from services.vk.exceptions import StopCreatingBotsException

SEX: tuple = (0, 1)


class PersonData(NamedTuple):
    name: str
    surname: str
    sex: int


class BotData(NamedTuple):
    phone: str
    password: str


class CreateBotsService(ABC):
    """Create bots service"""

    @abstractmethod
    def register_bot(self, data):
        """Register bot in social net"""

    @staticmethod
    @abstractmethod
    def generate_data_for_bot():
        """Generate data for registration"""


class CreateVkBotsService(CreateBotsService):
    """Create bots in VK social net"""

    MAIN_PAGE: str = "https://vk.com/"

    TIME_OUT: int = 10
    SMS_MAX_RESEND_TIME: int = 2

    NAME_INPUT: str = "vkc__TextField__input"
    SURNAME_INPUT: str = "vkc__TextField__input"
    SEX_BTN: str = "vkc__Switcher__button"
    BIRTHDAY_SELECTOR: str = "vkc__Select__customContainer"
    PASSWRD_INPUT: str = "Input__el"
    CODE_INPUT: str = "vkc__TextField__input"
    PHONE_INPUT: str = "vkc__TextField__input"
    CONTINUE_BTN: str = "vkc__Button__title"
    REGISTRATE_BTN: str = "VkIdForm__button"
    NOT_VALID_ACCOUNT: str = "vkc__EnterPasswordHasUserInfo__link"
    BTN: str = "vkuiButton__content"
    PAGE: str = "page_name"
    SOCIAL_NET: str = "vk"
    SMS_BTN: str = "vkc__Link__primary"
    CHANGE_PASSWORD_URL: str = "https://id.vk.com/account/#/password-change"

    PAGE_LOAD_STRATEGY: str = "eager"

    def __init__(self, phone_stock: PhoneStockService) -> None:
        """Init phone stock and set up driver.

        Args:
            phone_stock(PhoneStock): phone stock.
        """

        self.phone_stock = phone_stock
        self._setup_driver()

    def register_bot(self, data: tuple) -> BotData:
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
            name, surname, sex = data

            try:
                phone = self.phone_stock.buy_phone(
                    CreateVkBotsService.SOCIAL_NET
                )

            except PhoneStockUnavailableException:
                logger.error("Phone stock is unavailable now.")
                raise StopCreatingBotsException

            self._phone_input(phone)

            code = self._get_sms_or_call()
            self._input_code(code, phone)

            self._input_generated_data(name, surname, sex)

            password = self._set_password()

            return BotData(phone=phone, password=password)

        except (NoSuchElementException, TimeoutException, IndexError) as e:
            logger.error(f"Error occurred while creating a bot:{str(e)}")
            driver.quit()
            raise StopCreatingBotsException

    def _setup_driver(self) -> None:
        """Set up driver.

        Args:
        Returns:
            None
        """

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Remote(
            "http://selenium_bots_creation:4444/wd/hub", options=options
        )
        self.driver.implicitly_wait(5)

    def _input_generated_data(self, name: str, surname: str, sex: int) -> None:
        """Input generated data in a form.

        Args:
            name(str): name.
            surname(str): surname.
            sex(int): sex.

        Returns:
            None
        """

        driver = self.driver

        name_input = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.NAME_INPUT
        )[0]
        name_input.send_keys(name)

        surname_input = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.SURNAME_INPUT
        )[1]
        surname_input.send_keys(surname)

        sex_buttons = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.SEX_BTN
        )

        if sex == 0:
            sex_buttons[0].click()

        else:
            sex_buttons[1].click()

        driver.find_element(
            By.CLASS_NAME, CreateVkBotsService.CONTINUE_BTN
        ).click()

        birthday_selectors = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.BIRTHDAY_SELECTOR
        )

        day = birthday_selectors[0]
        month = birthday_selectors[1]
        year = birthday_selectors[2]

        webdriver.ActionChains(driver).move_to_element(
            day
        ).click().move_by_offset(0, 100).click().perform()
        webdriver.ActionChains(driver).move_to_element(
            month
        ).click().move_by_offset(0, 100).click().perform()
        webdriver.ActionChains(driver).move_to_element(
            year
        ).click().move_by_offset(0, 100).click().perform()

        driver.find_element(
            By.CLASS_NAME, CreateVkBotsService.CONTINUE_BTN
        ).click()

        try:
            WebDriverWait(driver, CreateVkBotsService.TIME_OUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, CreateVkBotsService.PAGE)
                )
            )
        except TimeoutException:
            logger.info("Bot is created.")

    def _phone_input(self, phone: str) -> None:
        """Phone input in a form.

        Args:
            phone(str): Phone number.

        Returns:
            None
        """

        driver = self.driver

        registrate_button = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.REGISTRATE_BTN
        )[1]
        registrate_button.click()

        phone_input = WebDriverWait(
            driver, CreateVkBotsService.TIME_OUT
        ).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, CreateVkBotsService.PHONE_INPUT)
            )
        )

        phone_input.send_keys(phone + Keys.ENTER)

    def _get_sms_or_call(self) -> str | None:
        """Get code from sms or call.

        Returns:
            code(str): Код.
        """

        driver = self.driver
        code = self.phone_stock.get_code()

        count = 0

        while not code:
            count += 1

            if count - 1 == CreateVkBotsService.SMS_MAX_RESEND_TIME:
                return None

            sms_btn = WebDriverWait(
                driver, CreateVkBotsService.TIME_OUT
            ).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, CreateVkBotsService.SMS_BTN)
                )
            )
            sms_btn[2].click()

            code = self.phone_stock.get_code()

        return code

    def _input_code(self, code: str | None, phone: str) -> None:
        """Input code in a form.

        Args:
            code(str): code for registration.
            phone(str): phone number.

        Returns:
            None
        """

        driver = self.driver

        if code:
            code_input = WebDriverWait(
                driver, CreateVkBotsService.TIME_OUT
            ).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, CreateVkBotsService.CODE_INPUT)
                )
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
                raise StopCreatingBotsException

            except TimeoutException:
                logger.info(f"{phone} is valid")

        else:
            logger.error(f"{phone} doesnt receive a code")
            driver.close()
            raise StopCreatingBotsException

    def _set_password(self) -> str:
        """Set password for new account."""
        driver = self.driver
        driver.get(CreateVkBotsService.CHANGE_PASSWORD_URL)

        call_me = driver.find_element(By.CLASS_NAME, CreateVkBotsService.BTN)
        webdriver.ActionChains(driver).move_to_element(
            call_me
        ).click().move_by_offset(0, 25).click().perform()

        WebDriverWait(
            driver,
            CreateVkBotsService.TIME_OUT,
            ignored_exceptions=(
                StaleElementReferenceException,
                NoSuchElementException,
            ),
        ).until(EC.presence_of_element_located((By.TAG_NAME, "button")))
        btn = driver.find_elements(By.TAG_NAME, "button")[1]
        btn.click()

        code = self._get_sms_or_call()

        code_input = driver.find_element(
            By.CLASS_NAME, CreateVkBotsService.PASSWRD_INPUT
        )
        code_input.send_keys(code + Keys.ENTER)

        passwrd = pwgenerator.generate()
        password_inputs = driver.find_elements(
            By.CLASS_NAME, CreateVkBotsService.PASSWRD_INPUT
        )
        password_inputs[0].send_keys(passwrd)
        password_inputs[1].send_keys(passwrd + Keys.TAB + Keys.ENTER)

        save_btn = driver.find_element(By.CLASS_NAME, CreateVkBotsService.BTN)
        save_btn.click()

        return passwrd

    @staticmethod
    def generate_data_for_bot() -> PersonData:
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

        return PersonData(name=name, surname=surname, sex=sex)
