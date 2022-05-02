"""VK boost service module"""

from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from core.config import logger


class VKBoostService:
    """Statistic boost service"""

    LOGIN_BTN: str = "VkIdForm__button"
    LOGIN_INPUT: str = "vkc__TextField__input"
    SWITCH_TO_PASSWORD: str = "vkc__Bottom__switchToPassword"
    PASSWORD_INPUT: str = "vkc__TextField__input"

    LIKE_BTN: str = '//div[text()="Нравится"]'
    SUBSCRIBE_BTN: str = "profile_action_btn"
    LIKED_POST: str = '//div[@data-reaction-user-reaction-id="0"]'
    PAGE_ACTIONS: str = "//span[@class='page_actions_dd_label']"
    EMAIL_BOX: str = "box_layout"
    EMAIL_INPUT: str = "bind_email"

    MAIN_PAGE: str = "https://vk.com/"

    PAGE_LOAD_STRATEGY: str = "eager"
    TIME_OUT: int = 5

    def __init__(self, username: str, password: str) -> None:
        """Login to bot account.

        Args:
            username(str): login.
            password(str): password.
        """

        self.username = username
        self.password = password
        self._setup_driver()

        browser = self.driver
        browser.get(VKBoostService.MAIN_PAGE)

        self._input_login()
        self._input_passwrd()

        self._remove_email_check_box()

    async def _input_login(self) -> None:
        """Input login in a form.

        Returns:
            None
        """

        driver = self.driver

        login_btn = driver.find_elements_by_class_name(VKBoostService.LOGIN_BTN)[1]
        login_btn.click()

        login_input = driver.find_element(By.CLASS_NAME, VKBoostService.LOGIN_INPUT)
        login_input.send_keys(self.username + Keys.ENTER)

    async def _input_passwrd(self) -> None:
        """Input password in a form.

        Returns:
            None
        """

        self.driver.find_element(By.CLASS_NAME, VKBoostService.SWITCH_TO_PASSWORD).click()

        password_input = self.driver.find_element(
            By.CLASS_NAME, VKBoostService.PASSWORD_INPUT
        )

        password_input.send_keys(self.password + Keys.ENTER)

    async def _setup_driver(self) -> None:
        """Setup driver.

        Returns:
            None
        """

        options = uc.ChromeOptions()
        options.add_argument("--headless")

        self.driver = uc.Chrome(version_main=100, options=options)
        self.driver.implicitly_wait(5)

    async def _remove_email_check_box(self) -> None:
        """Remove email check box.

        Returns:
            None
        """

        browser = self.driver

        try:
            WebDriverWait(browser, VKBoostService.TIME_OUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, VKBoostService.EMAIL_BOX))
            )

            input_email = browser.find_element_by_id(VKBoostService.EMAIL_INPUT)
            input_email.send_keys(Keys.ESCAPE)

        except exceptions.TimeoutException:
            logger.info("No email checkbox was found.")

    async def like_post(self, post: str) -> None:
        """Add like for post.

        Args:
            post(str): Post link.

        Returns:
            None
        """
        browser = self.driver
        browser.get(post)

        like_btn = WebDriverWait(browser, VKBoostService.TIME_OUT).until(
            EC.presence_of_element_located((By.XPATH, VKBoostService.LIKE_BTN))
        )

        ActionChains(browser).move_to_element(like_btn).click(like_btn).perform()

        WebDriverWait(browser, VKBoostService.TIME_OUT).until(
            EC.presence_of_element_located((By.XPATH, VKBoostService.LIKED_POST))
        )

        self.driver.close()

    async def subscribe(self, profile: str) -> None:
        """Add one sub to profile.

        Args:
            profile(str): Profile link.

        Returns:
            None
        """
        browser = self.driver
        browser.get(profile)

        browser.find_elements_by_class_name(VKBoostService.SUBSCRIBE_BTN)[1].click()

        WebDriverWait(browser, VKBoostService.TIME_OUT).until(
            EC.presence_of_element_located(
                (By.XPATH, VKBoostService.PAGE_ACTIONS)
            )
        )

        self.driver.close()
