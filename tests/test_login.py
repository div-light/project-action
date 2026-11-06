import re

from playwright.sync_api import Page, expect

from pages.landing_page import LandingPage
from testdata.credentials import PASSWORD, USERNAME
from utils.logger import logger


def test_login(page: Page):
    lp = LandingPage(page)
    lp.load()
    lp.login(USERNAME, PASSWORD)
    expect(page).to_have_url(re.compile(r".*/dashboard/.*"))
    logger.info("User logged in successfully with: %s", USERNAME)
