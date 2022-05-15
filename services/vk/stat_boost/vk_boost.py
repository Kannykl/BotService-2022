"""VK boost service module"""
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
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

        self.username = f"+7{username}"
        self.password = password
        self._setup_driver()

        browser = self.driver
        browser.get(VKBoostService.MAIN_PAGE)

        self._input_login()
        self._input_passwrd()
        self._remove_email_check_box()

    def _input_login(self) -> None:
        """Input login in a form.

        Returns:
            None
        """

        driver = self.driver
        login_btn = driver.find_elements(By.CLASS_NAME, VKBoostService.LOGIN_BTN)[0]
        login_btn.click()
        login_input = driver.find_element(By.CLASS_NAME, VKBoostService.LOGIN_INPUT)
        login_input.send_keys(self.username + Keys.ENTER)

    def _input_passwrd(self) -> None:
        """Input password in a form.

        Returns:
            None
        """
        try:
            self.driver.find_elements(By.CLASS_NAME, VKBoostService.SWITCH_TO_PASSWORD)[
                0
            ].click()

            password_input = self.driver.find_elements(
                By.CLASS_NAME, VKBoostService.PASSWORD_INPUT
            )[1]

        except NoSuchElementException:
            logger.error("Error during input passwrd: didnt find an element")
            self.driver.quit()
            return

        password_input.send_keys(self.password + Keys.ENTER)

    def _setup_driver(self) -> None:
        """Setup driver.

        Returns:
            None
        """

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Remote("http://selenium_boost:4444/wd/hub", options=options)
        self.driver.implicitly_wait(5)

    def _remove_email_check_box(self) -> None:
        """Remove email check box.

        Returns:
            None
        """

        browser = self.driver

        try:
            WebDriverWait(browser, VKBoostService.TIME_OUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, VKBoostService.EMAIL_BOX)
                )
            )

            input_email = browser.find_element(By.ID, VKBoostService.EMAIL_INPUT)
            input_email.send_keys(Keys.ESCAPE)

        except exceptions.TimeoutException:
            logger.info("No email checkbox was found.")

    def like_post(self, post: str) -> None:
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

    def subscribe(self, profile: str) -> None:
        """Add one sub to profile.

        Args:
            profile(str): Profile link.

        Returns:
            None
        """
        browser = self.driver
        browser.get(profile)

        try:
            sub_btn = browser.find_elements(By.CLASS_NAME, VKBoostService.SUBSCRIBE_BTN)
            sub_btn[1].click()

        except NoSuchElementException:
            logger.info(f"This {profile} already like by this bot.")

        try:
            WebDriverWait(browser, VKBoostService.TIME_OUT).until(
                EC.presence_of_element_located((By.XPATH, VKBoostService.PAGE_ACTIONS))
            )

        except TimeoutException:
            logger.info(f"Like to {profile} added.")

        self.driver.close()
