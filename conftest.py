import os
import re
import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from utils.logger import logger

ARTIFACTS = Path("artifacts")

load_dotenv()
HEADLESS = os.getenv("HEADLESS", "true").lower() in ["true", "1", "t", "y", "yes"]


def _safe(name):
    return re.sub(r"[^\w.-]", "_", name)


def pytest_sessionstart(session):
    if hasattr(session.config, "workerinput"):
        return
    if ARTIFACTS.exists():
        shutil.rmtree(ARTIFACTS)
    for sub in ("screenshots", "videos", "traces"):
        (ARTIFACTS / sub).mkdir(parents=True, exist_ok=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            shot_dir = ARTIFACTS / "screenshots"
            shot_dir.mkdir(parents=True, exist_ok=True)
            path = shot_dir / f"{_safe(item.name)}.png"
            page.screenshot(path=str(path), full_page=True)
            logger.info("Screenshot saved %s", path)


@contextmanager
def _traced_context(browser, request, **kwargs):
    video_dir = ARTIFACTS / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(record_video_dir=str(video_dir), **kwargs)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    try:
        yield context
    finally:
        rep_call = getattr(request.node, "rep_call", None)
        rep_setup = getattr(request.node, "rep_setup", None)

        failed = bool(
            (rep_call and rep_call.failed) or (rep_setup and rep_setup.failed)
        )

        trace_path = None
        if failed:
            trace_dir = ARTIFACTS / "traces"
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / f"{_safe(request.node.name)}.zip"

        try:
            context.tracing.stop(path=trace_path)
        except Exception as e:
            logger.error("Failed to stop tracing: %s", e)

        pages = context.pages
        try:
            context.close()
        finally:
            if not failed:
                for page in pages:
                    if page.video:
                        page.video.delete()


@pytest.fixture(scope="session")
def pw_browser():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        yield browser
        browser.close()


@pytest.fixture
def page(pw_browser, request):
    with _traced_context(pw_browser, request) as context:
        yield context.new_page()
