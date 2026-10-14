from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from playwright.sync_api import Page, expect, sync_playwright

from frontend.layout import NAVIGATION_GROUPS, PAGE_META


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def workspace_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    root = Path(__file__).resolve().parents[1]
    runtime = tmp_path_factory.mktemp("frontend-runtime")
    port = _free_port()
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(root), existing_pythonpath) if item
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(root / "tests" / "serve_frontend_demo.py"),
            "--port",
            str(port),
            "--runtime",
            str(runtime),
        ],
        cwd=root,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        # A fresh environment may spend more than 30 seconds importing Paddle
        # before Gradio is ready, especially on CPU-only Windows runners.
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if httpx.get(f"{base_url}/api/v1/health", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if process.poll() is not None:
                raise RuntimeError("isolated frontend fixture exited before becoming healthy")
            time.sleep(0.1)
        else:
            raise RuntimeError("isolated frontend fixture did not become healthy")
        yield f"{base_url}/ui/"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _select_option(page: Page, elem_id: str, label: str) -> None:
    control = page.locator(f"#{elem_id} input")
    control.click()
    page.get_by_role("option", name=label, exact=True).click()
    expect(control).to_have_value(label, timeout=15_000)


def _write_screenshot(page: Page, path: Path, *, full_page: bool) -> None:
    payload = page.screenshot(full_page=full_page)
    last_error: OSError | None = None
    for _ in range(5):
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_bytes(payload)
            os.replace(temporary, path)
            return
        except OSError as exc:
            last_error = exc
            temporary.unlink(missing_ok=True)
            time.sleep(0.05)
    assert last_error is not None
    raise last_error


@pytest.mark.browser
def test_schema_error_uses_one_chinese_toast_and_preserves_output(
    workspace_url: str, tmp_path: Path
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.get_by_role("button", name="校验 Schema", exact=True).click()

        toast = page.locator(".toast-wrap, [role='alert']").filter(has_text="错误").last
        toast.wait_for(state="visible", timeout=15_000)
        expect(toast).to_contain_text("错误")
        expect(toast).to_contain_text("请上传 Schema 文件")
        expect(page.get_by_text("尚未校验 Schema", exact=True)).to_be_visible()
        assert page.get_by_text("Error", exact=True).count() == 0
        _write_screenshot(page, tmp_path / "chinese-error-toast.png", full_page=False)
        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    ("name", "width", "height"),
    [
        ("desktop", 1440, 900),
        ("tablet", 820, 1180),
        ("mobile", 390, 844),
    ],
)
def test_workspace_navigation_branding_and_responsive_layout(
    workspace_url: str,
    tmp_path: Path,
    name: str,
    width: int,
    height: int,
) -> None:
    screenshot_root = Path(os.environ.get("PRISMKE_SCREENSHOT_DIR", tmp_path))
    screenshot_root.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)

        logo = page.locator("#workspace-logo img")
        logo.wait_for(state="visible")
        assert logo.evaluate("element => element.naturalWidth") > 0
        logo_box = logo.bounding_box()
        assert logo_box is not None
        assert logo_box["width"] >= (300 if name == "mobile" else 410)
        assert "An auditable and traceable" in page.locator("#workspace-brand").inner_text()
        assert page.locator("#workspace-brand").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        ) == page.locator(".gradio-container").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )

        sidebar = page.locator("#workspace-sidebar")
        toggle = page.get_by_role("button", name="Toggle Sidebar")
        if name == "mobile":
            page.wait_for_function(
                "!document.querySelector('#workspace-sidebar').classList.contains('open')"
            )
            toggle.click()
            page.wait_for_function(
                "document.querySelector('#workspace-sidebar').classList.contains('open')"
            )

        _select_option(page, "navigation-group", "构建与执行")
        page.locator("#navigation-page").wait_for(state="visible")
        heading = page.locator(".workspace-page-header:visible h1")
        heading.wait_for(state="visible")
        expect(heading).to_have_text("新建抽取与构建", timeout=60_000)

        if name == "mobile":
            if "open" in (sidebar.get_attribute("class") or ""):
                toggle.click()
                page.wait_for_function(
                    "!document.querySelector('#workspace-sidebar').classList.contains('open')"
                )
            page.wait_for_timeout(400)
        else:
            assert "open" in (sidebar.get_attribute("class") or "")
        if name == "desktop":
            resizer = page.locator("#workspace-resizer")
            resizer.wait_for(state="visible")
            before = sidebar.bounding_box()
            resizer.focus()
            resizer.press("ArrowRight")
            after = sidebar.bounding_box()
            assert before and after and after["width"] > before["width"]
            assert (
                page.evaluate("localStorage.getItem('prismke.workspace.sidebar.width')") is not None
            )

        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 1
        _write_screenshot(page, screenshot_root / f"{name}-build.png", full_page=True)
        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    ("group_id", "group_label", "pages"),
    [
        (group_id, group_label, pages)
        for group_id, (group_label, pages) in NAVIGATION_GROUPS.items()
    ],
    ids=list(NAVIGATION_GROUPS),
)
def test_workspace_group_pages_are_reachable(
    workspace_url: str,
    tmp_path: Path,
    group_id: str,
    group_label: str,
    pages: tuple[tuple[str, str], ...],
) -> None:
    screenshot_root = Path(os.environ.get("PRISMKE_SCREENSHOT_DIR", tmp_path)) / "pages" / group_id
    screenshot_root.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")

        if group_id != "overview":
            _select_option(page, "navigation-group", group_label)
            if len(pages) > 1:
                expect(page.locator("#navigation-page input")).to_have_value(
                    pages[0][0], timeout=60_000
                )
        for page_label, page_id in pages:
            if len(pages) > 1:
                page.locator("#navigation-page").wait_for(state="visible", timeout=60_000)
                _select_option(page, "navigation-page", page_label)
            heading = page.locator(".workspace-page-header:visible h1")
            heading.wait_for(state="visible")
            expected_title = PAGE_META[page_id][0]
            expect(heading).to_have_text(expected_title, timeout=60_000)
            assert heading.inner_text() == expected_title
            _write_screenshot(
                page,
                screenshot_root / f"desktop-{page_id}.png",
                full_page=False,
            )
            page.wait_for_timeout(750)

        browser.close()
