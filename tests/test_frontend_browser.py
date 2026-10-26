from __future__ import annotations

import json
import os
import re
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

from frontend.i18n import LOCALE_STORAGE_KEY, tr
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


def _visible_nontechnical_chinese(page: Page) -> list[str]:
    return page.evaluate(
        """
        () => {
          const results = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          let node;
          while ((node = walker.nextNode())) {
            const parent = node.parentElement;
            const ignored = 'pre, code, textarea, script, style, [data-prismke-no-i18n]';
            if (!parent || parent.closest(ignored)) continue;
            const style = getComputedStyle(parent);
            if (style.display === 'none' || style.visibility === 'hidden') continue;
            const text = (node.textContent || '').trim();
            if (/[\u4e00-\u9fff]/.test(text)) results.push(text);
          }
          document.querySelectorAll('input, textarea').forEach(control => {
            if (control.type === 'hidden' || control.closest('[data-prismke-no-i18n]')) return;
            const style = getComputedStyle(control);
            if (style.display === 'none' || style.visibility === 'hidden') return;
            const value = control.value || '';
            if (/[\u4e00-\u9fff]/.test(value)) results.push(value);
          });
          return [...new Set(results)];
        }
        """
    )


@pytest.mark.browser
def test_default_english_schema_error_and_chinese_switch_preserve_output(
    workspace_url: str, tmp_path: Path
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        expect(page.locator("html")).to_have_attribute("lang", "en", timeout=15_000)
        expect(page.get_by_text("Workspace", exact=True)).to_be_visible()
        page.get_by_role("button", name="Validate Schema", exact=True).click()

        toast = page.locator(".toast-wrap, [role='alert']").filter(has_text="Error").last
        toast.wait_for(state="visible", timeout=15_000)
        expect(toast).to_contain_text("Upload a Schema file.")
        expect(page.get_by_text("Schema has not been validated", exact=True)).to_be_visible()

        page.get_by_text("Models and graph storage", exact=True).click()
        expect(page.locator("#ocr-device input[role='combobox']")).to_have_value(
            "Automatic (current: CPU)"
        )
        expect(page.locator("#key-configuration-status")).not_to_contain_text("密钥状态")
        expect(page.locator("#key-configuration-status")).to_contain_text("Key status")
        expect(page.locator("#neo4j-password-status")).not_to_contain_text("密码")
        operator = page.locator("#config-operator textarea, #config-operator input")
        expect(operator).to_have_value("Administrator")
        page.get_by_role("button", name="Save settings", exact=True).click()
        settings_outcome = page.locator("#settings-outcome textarea, #settings-outcome input")
        expect(settings_outcome).to_have_value(
            re.compile(r"^Settings saved · Graph store "),
            timeout=15_000,
        )
        assert settings_outcome.input_value().startswith("Settings saved · Graph store ")
        operator.fill("paper-demo")
        page.locator("#language-switch input[type='checkbox']").click()
        expect(page.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
        expect(page.get_by_text("工作区", exact=True)).to_be_visible()
        expect(operator).to_have_value("paper-demo")
        expect(page.locator("#ocr-device input[role='combobox']")).to_have_value(
            "自动（当前：CPU）"
        )
        expect(settings_outcome).to_have_value(re.compile(r"^设置已保存 · 图存储 "), timeout=15_000)
        assert settings_outcome.input_value().startswith("设置已保存 · 图存储 ")
        page.get_by_role("button", name="校验 Schema", exact=True).click()
        chinese_toast = page.locator(".toast-wrap, [role='alert']").filter(has_text="错误").last
        chinese_toast.wait_for(state="visible", timeout=15_000)
        expect(chinese_toast).to_contain_text("请上传 Schema 文件")
        expect(page.get_by_text("尚未校验 Schema", exact=True)).to_be_visible()
        page.reload(wait_until="domcontentloaded")
        expect(page.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
        _write_screenshot(page, tmp_path / "bilingual-error-toast.png", full_page=False)
        browser.close()


@pytest.mark.browser
def test_locale_storage_keyboard_tab_sync_and_session_isolation(workspace_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.add_init_script(
            f"localStorage.setItem('{LOCALE_STORAGE_KEY}', 'unsupported-locale')"
        )
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        expect(page.locator("html")).to_have_attribute("lang", "en", timeout=15_000)

        switch = page.locator("#language-switch input[type='checkbox']")
        switch.focus()
        switch.press("Enter")
        expect(page.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
        expect(page.locator("#language-switch")).to_have_attribute("aria-checked", "true")
        assert page.evaluate(f"localStorage.getItem('{LOCALE_STORAGE_KEY}')") == "zh-CN"

        sibling = context.new_page()
        sibling.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        expect(sibling.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
        sibling_switch = sibling.locator("#language-switch input[type='checkbox']")
        sibling_switch.focus()
        sibling_switch.press("Space")
        expect(sibling.locator("html")).to_have_attribute("lang", "en", timeout=15_000)
        expect(page.locator("html")).to_have_attribute("lang", "en", timeout=15_000)

        isolated = browser.new_context().new_page()
        isolated.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        expect(isolated.locator("html")).to_have_attribute("lang", "en", timeout=15_000)
        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    ("name", "width", "height"),
    [
        ("wide", 2560, 1392),
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
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)

        logo = page.locator("#workspace-logo img")
        logo.wait_for(state="visible")
        natural_size = logo.evaluate(
            "element => ({width: element.naturalWidth, height: element.naturalHeight})"
        )
        assert natural_size["width"] > 0
        assert natural_size["height"] > 0
        logo_box = logo.bounding_box()
        assert logo_box is not None
        header_box = page.locator("#workspace-header").bounding_box()
        topbar_box = page.locator("#workspace-topbar").bounding_box()
        brand_box = page.locator("#workspace-brand").bounding_box()
        assert header_box is not None
        assert topbar_box is not None
        assert brand_box is not None
        assert logo_box["width"] <= brand_box["width"] * 0.9 + 1
        brand_content_width = page.locator("#workspace-brand").evaluate(
            """element => {
              const style = getComputedStyle(element);
              return element.clientWidth
                - parseFloat(style.paddingLeft)
                - parseFloat(style.paddingRight);
            }"""
        )
        if width > 520:
            expected_logo_width = min(
                brand_content_width * 0.36,
                (brand_box["height"] - 62) * 3,
                620,
            )
        else:
            expected_logo_width = min(
                brand_content_width * 0.62,
                (brand_box["height"] - 64) * 3,
                280,
            )
        rendered_ratio = logo_box["width"] / logo_box["height"]
        natural_ratio = natural_size["width"] / natural_size["height"]
        assert abs(rendered_ratio - natural_ratio) <= natural_ratio * 0.02
        assert expected_logo_width * 0.82 <= logo_box["width"] <= (
            expected_logo_width + 3
        )
        language_switch_box = page.locator("#language-switch").bounding_box()
        assert language_switch_box is not None
        assert language_switch_box["x"] >= topbar_box["x"]
        assert language_switch_box["x"] + language_switch_box["width"] <= (
            topbar_box["x"] + topbar_box["width"] + 1
        )
        assert language_switch_box["y"] >= topbar_box["y"]
        assert language_switch_box["y"] + language_switch_box["height"] <= (
            topbar_box["y"] + topbar_box["height"] + 1
        )
        assert abs(brand_box["y"] - (topbar_box["y"] + topbar_box["height"])) <= 2
        logo_overlaps_switch = not (
            logo_box["x"] + logo_box["width"] <= language_switch_box["x"]
            or language_switch_box["x"] + language_switch_box["width"] <= logo_box["x"]
            or logo_box["y"] + logo_box["height"] <= language_switch_box["y"]
            or language_switch_box["y"] + language_switch_box["height"] <= logo_box["y"]
        )
        assert not logo_overlaps_switch
        if width > 900:
            expected_topbar_height = min(max(48, height * 0.05), 72)
            expected_brand_height = min(max(132, height * 0.15), 230)
        elif width > 520:
            expected_topbar_height = min(max(46, height * 0.05), 60)
            expected_brand_height = min(max(132, height * 0.15), 190)
        else:
            expected_topbar_height = 48
            expected_brand_height = 140
        assert abs(topbar_box["height"] - expected_topbar_height) <= 2
        assert abs(brand_box["height"] - expected_brand_height) <= 2
        assert abs(header_box["height"] - (topbar_box["height"] + brand_box["height"])) <= 2
        assert "An auditable and traceable" in page.locator("#workspace-brand").inner_text()
        assert page.locator("#workspace-brand").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        ) == page.locator(".gradio-container").evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        switch_overflow = page.locator("#language-switch").evaluate(
            """element => [element, ...element.querySelectorAll('*')].map(node => ({
              tag: node.tagName,
              id: node.id,
              classes: node.className,
              overflowX: getComputedStyle(node).overflowX,
              overflowY: getComputedStyle(node).overflowY,
              clientWidth: node.clientWidth,
              scrollWidth: node.scrollWidth,
              clientHeight: node.clientHeight,
              scrollHeight: node.scrollHeight,
            }))"""
        )
        overflowing_switch_nodes = [
            item
            for item in switch_overflow
            if not (
                item["overflowX"] not in {"auto", "scroll"}
                and item["overflowY"] not in {"auto", "scroll"}
                and item["scrollWidth"] <= item["clientWidth"]
                and item["scrollHeight"] <= item["clientHeight"]
            )
        ]
        assert overflowing_switch_nodes == [], json.dumps(overflowing_switch_nodes)

        sidebar = page.locator("#workspace-sidebar")
        toggle = page.get_by_role("button", name="Toggle Sidebar")
        if width <= 900:
            page.wait_for_function(
                "!document.querySelector('#workspace-sidebar').classList.contains('open')"
            )
            assert brand_box["width"] >= width * 0.98
            toggle.click()
            page.wait_for_function(
                "document.querySelector('#workspace-sidebar').classList.contains('open')"
            )

        _select_option(page, "navigation-group", tr("构建与执行"))
        page.locator("#navigation-page").wait_for(state="visible")
        heading = page.locator(".workspace-page-header:visible h1")
        heading.wait_for(state="visible")
        expect(heading).to_have_text(tr("新建抽取与构建"), timeout=60_000)
        tabs_box = page.locator("#workspace-tabs").bounding_box()
        assert tabs_box is not None
        expected_brand_gap = min(max(8, height * 0.01), 16) if width > 520 else 8
        assert abs(tabs_box["y"] - (brand_box["y"] + brand_box["height"]) - expected_brand_gap) <= 2

        if width <= 900:
            if "open" in (sidebar.get_attribute("class") or ""):
                toggle.click()
                page.wait_for_function(
                    "!document.querySelector('#workspace-sidebar').classList.contains('open')"
                )
            page.wait_for_timeout(400)
        else:
            assert "open" in (sidebar.get_attribute("class") or "")
        if width > 900:
            sidebar_box = sidebar.bounding_box()
            assert sidebar_box is not None
            assert abs(sidebar_box["width"] / width - 0.2) <= 0.01
            parent_width = page.locator(".sidebar-parent").evaluate(
                "element => element.clientWidth"
            )
            assert abs(tabs_box["width"] / (parent_width - sidebar_box["width"]) - 0.9) <= 0.02

            open_tabs_width = tabs_box["width"]
            toggle.click()
            page.wait_for_function(
                "!document.querySelector('#workspace-sidebar').classList.contains('open')"
            )
            page.wait_for_function(
                "Math.abs(document.querySelector('#workspace-tabs').getBoundingClientRect().x "
                "/ window.innerWidth - 0.05) < 0.01"
            )
            expect(toggle).to_be_visible()
            expect(toggle).to_have_attribute("aria-expanded", "false")
            assert sidebar.evaluate("element => getComputedStyle(element).visibility") == "hidden"
            collapsed_tabs_box = page.locator("#workspace-tabs").bounding_box()
            assert collapsed_tabs_box is not None
            assert collapsed_tabs_box["width"] > open_tabs_width
            assert abs(collapsed_tabs_box["x"] / width - 0.05) <= 0.01
            toggle.click()
            page.wait_for_function(
                "document.querySelector('#workspace-sidebar').classList.contains('open')"
            )
            expect(toggle).to_have_attribute("aria-expanded", "true")

            resizer = page.locator("#workspace-resizer")
            resizer.wait_for(state="visible")
            before = sidebar.bounding_box()
            resizer.focus()
            resizer.press("ArrowRight")
            after = sidebar.bounding_box()
            assert before and after and after["width"] > before["width"]
            assert (
                page.evaluate("localStorage.getItem('prismke.workspace.sidebar.ratio')") is not None
            )
            assert after["width"] / width <= 0.3
            resizer.press("End")
            maximum = sidebar.bounding_box()
            assert maximum is not None
            assert abs(maximum["width"] / width - 0.3) <= 0.01
            resizer.press("Home")
            minimum = sidebar.bounding_box()
            assert minimum is not None
            assert abs(minimum["width"] / width - 0.1) <= 0.01

        if name == "mobile":
            table_metrics = page.locator(".virtual-table-viewport:visible").evaluate_all(
                """elements => elements.map(element => ({
                  clientWidth: element.clientWidth,
                  scrollWidth: element.scrollWidth,
                  headerWhiteSpace: getComputedStyle(element.querySelector('th span')).whiteSpace,
                }))"""
            )
            assert table_metrics
            assert any(item["scrollWidth"] > item["clientWidth"] for item in table_metrics)
            assert all(item["headerWhiteSpace"] == "nowrap" for item in table_metrics)

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
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")

        if group_id != "overview":
            _select_option(page, "navigation-group", tr(group_label))
            if len(pages) > 1:
                expect(page.locator("#navigation-page input")).to_have_value(
                    tr(pages[0][0]), timeout=60_000
                )
        for page_label, page_id in pages:
            if len(pages) > 1:
                page.locator("#navigation-page").wait_for(state="visible", timeout=60_000)
                _select_option(page, "navigation-page", tr(page_label))
            heading = page.locator(".workspace-page-header:visible h1")
            heading.wait_for(state="visible")
            expected_title = tr(PAGE_META[page_id][0])
            expect(heading).to_have_text(expected_title, timeout=60_000)
            assert heading.inner_text() == expected_title
            page.wait_for_timeout(150)
            chinese = _visible_nontechnical_chinese(page)
            assert chinese == [], json.dumps(chinese, ensure_ascii=True)
            switch = page.locator("#language-switch input[type='checkbox']")
            switch.click()
            expect(page.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
            expect(heading).to_have_text(PAGE_META[page_id][0], timeout=15_000)
            switch.click()
            expect(page.locator("html")).to_have_attribute("lang", "en", timeout=15_000)
            expect(heading).to_have_text(expected_title, timeout=15_000)
            _write_screenshot(
                page,
                screenshot_root / f"desktop-{page_id}.png",
                full_page=False,
            )
            page.wait_for_timeout(750)

        browser.close()
