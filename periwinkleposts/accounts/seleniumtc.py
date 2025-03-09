
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium.webdriver.chrome.service import Service
from selenium import webdriver

class SeleniumTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # options = webdriver.ChromeOptions()
        # options.add_argument("--start-maximized")
        # service = Service(f"{settings.BASE_DIR}/chromedriver")
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()