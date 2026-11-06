from playwright.sync_api import Page

from config.config import UI_BASE


class LandingPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.get_by_role("textbox", name="username")
        self.password_input = page.get_by_role("textbox", name="password")
        self.login_button = page.locator("button[type='submit']")

    def load(self):
        self.page.goto(UI_BASE)

    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
