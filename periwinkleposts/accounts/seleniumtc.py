
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import os

class SeleniumTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Check if running in GitHub Actions
        is_ci = os.getenv('CI', 'false') == 'true'
        
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        
        if is_ci:
            options.add_argument("--headless")  # Run headless in CI
        else:
            # Run normal browser window locally
            options.add_argument("--start-maximized")  # Optionally maximize the window for local testing
        
        # Initialize the WebDriver
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(10)
        

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()