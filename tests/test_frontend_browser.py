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
from frontend.layout import NAVIGATION_GROUPS, PAGE_META, TAGLINE, TAGLINE_ZH


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


@pytest.fixture
def candidate_workspace_url(tmp_path: Path) -> Iterator[str]:
    """Run the candidate-graph interaction test in an isolated service state."""

    root = Path(__file__).resolve().parents[1]
    runtime = tmp_path / "runtime"
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
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                if httpx.get(f"{base_url}/api/v1/health", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if process.poll() is not None:
                raise RuntimeError("candidate frontend fixture exited before becoming healthy")
            time.sleep(0.1)
        else:
            raise RuntimeError("candidate frontend fixture did not become healthy")
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
    page.get_by_role("option", name=label, exact=True).last.click()
    expect(control).to_have_value(label, timeout=15_000)


def _open_workspace_page(page: Page, group_id: str, page_id: str) -> None:
    sidebar = page.locator("#workspace-sidebar")
    if "open" not in (sidebar.get_attribute("class") or ""):
        page.get_by_role("button", name="Toggle Sidebar").click()
        page.wait_for_function(
            "document.querySelector('#workspace-sidebar').classList.contains('open')"
        )
    group_label, pages = NAVIGATION_GROUPS[group_id]
    _select_option(page, "navigation-group", tr(group_label))
    if len(pages) > 1:
        page_label = next(label for label, candidate in pages if candidate == page_id)
        page.locator("#navigation-page").wait_for(state="visible", timeout=15_000)
        _select_option(page, "navigation-page", tr(page_label))
    expected_title = tr(PAGE_META[page_id][0])
    expect(page.locator(".workspace-page-header:visible h1")).to_have_text(
        expected_title,
        timeout=15_000,
    )
    if page.viewport_size and page.viewport_size["width"] <= 900:
        page.get_by_role("button", name="Toggle Sidebar").click()
        page.wait_for_function(
            "!document.querySelector('#workspace-sidebar').classList.contains('open')"
        )


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
        expect(page.locator("#workspace-brand")).to_contain_text(TAGLINE)
        expect(page.locator("#workspace-brand")).to_contain_text("Development build")
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
        settings_outcome = page.locator("#settings-outcome")
        expect(settings_outcome).to_contain_text("Settings saved · Graph store ", timeout=15_000)
        assert settings_outcome.evaluate(
            "element => element.scrollHeight <= element.clientHeight + 1"
        )
        operator.fill("paper-demo")
        page.locator("#language-switch input[type='checkbox']").click()
        expect(page.locator("html")).to_have_attribute("lang", "zh-CN", timeout=15_000)
        expect(page.get_by_text("工作区", exact=True)).to_be_visible()
        expect(page.locator("#workspace-brand")).to_contain_text(TAGLINE_ZH)
        expect(page.locator("#workspace-brand")).to_contain_text("开发版本")
        expect(operator).to_have_value("paper-demo")
        expect(page.locator("#ocr-device input[role='combobox']")).to_have_value(
            "自动（当前：CPU）"
        )
        expect(settings_outcome).to_contain_text("设置已保存 · 图存储 ", timeout=15_000)
        assert settings_outcome.evaluate(
            "element => element.scrollHeight <= element.clientHeight + 1"
        )
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
def test_schema_valid_marker_is_bilingual_and_invalidated_on_change(
    workspace_url: str, tmp_path: Path
) -> None:
    schema_path = tmp_path / "schema.yaml"
    schema_path.write_text(
        """schema_id: browser-schema
version: "1"
strict: false
entity_types:
  - id: Organization
relations:
  - id: collaborates_with
    domain: [Organization]
    range: [Organization]
""",
        encoding="utf-8",
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)

        schema_file = page.locator("#schema-file-input input[type='file']")
        schema_file.set_input_files(schema_path)
        expect(page.get_by_text("schema.yaml", exact=True)).to_be_visible(timeout=15_000)
        page.wait_for_timeout(750)
        page.get_by_role("button", name="Validate Schema", exact=True).click()
        valid = page.locator(".schema-validation-valid")
        expect(valid).to_contain_text("✓ Valid", timeout=15_000)
        expect(valid).to_contain_text("Schema browser-schema")
        expect(valid).to_contain_text("Entity types 1")
        expect(valid).to_contain_text("Relations 1")
        expect(valid).to_contain_text("Hash ")
        assert not re.search(r"[\u4e00-\u9fff]", valid.inner_text())

        page.locator("#language-switch input[type='checkbox']").click()
        expect(valid).to_contain_text("✓ 有效", timeout=15_000)
        expect(valid).to_contain_text("版本 1")
        expect(valid).to_contain_text("实体类型 1")
        expect(valid).to_contain_text("关系 1")

        _select_option(page, "schema-source", "文本输入")
        expect(page.get_by_text("尚未校验 Schema", exact=True)).to_be_visible(timeout=15_000)
        expect(page.locator(".schema-validation-valid")).to_have_count(0)
        browser.close()


@pytest.mark.browser
def test_candidate_graph_click_opens_traceable_evidence(
    candidate_workspace_url: str, tmp_path: Path
) -> None:
    schema_path = tmp_path / "graph-schema.yaml"
    schema_path.write_text(
        """schema_id: candidate-graph
version: "1"
strict: false
entity_types:
  - id: Software
  - id: Organization
relations:
  - id: developed_by
    domain: [Software]
    range: [Organization]
""",
        encoding="utf-8",
    )
    document_path = tmp_path / "candidate.md"
    document_path.write_text(
        "PrismKE | developed_by | OpenAI | Software | Organization | 0.95\n",
        encoding="utf-8",
    )
    base_url = candidate_workspace_url.removesuffix("/ui/")
    response = httpx.post(
        f"{base_url}/api/v1/runs",
        files={
            "document": (document_path.name, document_path.read_bytes(), "text/markdown"),
            "schema": (schema_path.name, schema_path.read_bytes(), "application/yaml"),
        },
        data={"provider": "mock", "task_mode": "entity_extraction"},
        timeout=30,
    )
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    for _ in range(200):
        execution = httpx.get(
            f"{base_url}/api/v1/runs/{run_id}/execution",
            timeout=5,
        ).json()
        if not execution["active"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("candidate graph fixture execution timed out")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(candidate_workspace_url, wait_until="domcontentloaded", timeout=60_000)
        _open_workspace_page(page, "build-execution", "build")

        current_run = page.locator("#current-run input")
        current_run.click()
        page.get_by_role("option").filter(has_text="candidate.md").click()
        expect(page.locator("#result-insight")).to_contain_text("Task mode", timeout=15_000)

        plot = page.locator("#candidate-result-plot .js-plotly-plot")
        plot.wait_for(state="visible", timeout=30_000)
        page.wait_for_function(
            """() => {
              const plot = document.querySelector('#candidate-result-plot .js-plotly-plot');
              return plot?.dataset.prismkeClickBound === 'true' &&
                (plot?.data || []).some(item =>
                Array.isArray(item.customdata) && item.customdata.length
              );
            }""",
            timeout=30_000,
        )
        points = plot.locator(".scatterlayer .point")
        assert points.count() > 0
        points.first.click(force=True)
        bridge = page.locator(
            "#candidate-plot-selection input, #candidate-plot-selection textarea"
        )
        expect(bridge).not_to_have_value("", timeout=5_000)
        item_id = bridge.input_value()
        expect(page.locator("#candidate-result-evidence")).to_contain_text(
            item_id,
            timeout=15_000,
        )
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
def test_status_cards_actions_and_visual_review_are_geometrically_aligned(
    workspace_url: str,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")

        def blue_border_count() -> int:
            return page.locator(".block.workspace-metrics:visible").first.evaluate(
                """element => [element, ...element.querySelectorAll('*')].filter(node => {
                  const style = getComputedStyle(node);
                  return parseFloat(style.borderLeftWidth) > 0
                    && style.borderLeftStyle !== 'none';
                }).length"""
            )

        assert blue_border_count() == 1
        _open_workspace_page(page, "build-execution", "build")
        assert blue_border_count() == 1

        for group_id, page_id in (
            ("build-execution", "execution"),
            ("review-validation", "entity-review"),
            ("review-validation", "claim-review"),
            ("media-knowledge", "visual-review"),
        ):
            _open_workspace_page(page, group_id, page_id)
            action_row = page.locator(".compact-action-row:visible").first
            field_panel = action_row.locator(":scope > .compact-action-fields")
            button = action_row.locator("button.compact-action-button")
            panel_box = field_panel.bounding_box()
            button_box = button.bounding_box()
            assert panel_box is not None and button_box is not None
            assert 60 <= panel_box["height"] <= 72
            assert abs(panel_box["height"] - button_box["height"]) <= 2
            alignments = action_row.locator(".compact-inline-field").evaluate_all(
                """fields => fields.map(field => {
                  const label = field.querySelector('.compact-inline-label');
                  const input = field.querySelector('input');
                  if (!label || !input) return null;
                  const a = label.getBoundingClientRect();
                  const b = input.getBoundingClientRect();
                  return Math.abs((a.y + a.height / 2) - (b.y + b.height / 2));
                })"""
            )
            assert alignments and all(item is not None and item <= 3 for item in alignments)

        preview_box = page.locator("#visual-review-preview").bounding_box()
        detail_box = page.locator("#visual-review-detail").bounding_box()
        assert preview_box is not None and detail_box is not None
        assert abs(preview_box["height"] - detail_box["height"]) <= 2
        browser.close()


@pytest.mark.browser
def test_sidebar_urls_and_detail_panels_show_their_complete_content(
    workspace_url: str,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")

        page.get_by_text("Models and graph storage", exact=True).click()
        url_fields = page.locator("#workspace-sidebar .sidebar-url-field textarea")
        expect(url_fields).to_have_count(2)
        long_base_url = (
            "https://ws-1hdqnxiyhm6e2w5j.cn-beijing.maas.aliyuncs.com/"
            "compatible-mode/v1"
        )
        for index in range(2):
            field = url_fields.nth(index)
            field.fill(long_base_url)
            assert field.input_value() == long_base_url
            dimensions = field.evaluate(
                "element => ({client: element.clientHeight, scroll: element.scrollHeight})"
            )
            assert dimensions["scroll"] <= dimensions["client"] + 1

        _open_workspace_page(page, "build-execution", "build")
        build_detail = page.locator("#build-technical-detail")
        build_toggle = build_detail.locator(":scope > button.label-wrap")
        if not page.locator("#build-run-summary").is_visible():
            build_toggle.click()
        expect(page.locator("#build-run-summary")).to_be_visible()
        build_input_box = page.locator("#build-input-panel").bounding_box()
        build_status_box = page.locator("#build-status-panel").bounding_box()
        assert build_input_box is not None and build_status_box is not None
        assert abs(
            (build_input_box["y"] + build_input_box["height"])
            - (build_status_box["y"] + build_status_box["height"])
        ) <= 2

        for group_id, page_id, preview_id, detail_id, json_id in (
            (
                "media-knowledge",
                "media",
                "media-preview",
                "media-detail",
                "media-detail-json",
            ),
            (
                "media-knowledge",
                "visual-review",
                "visual-review-preview",
                "visual-review-detail",
                "visual-review-detail-json",
            ),
        ):
            _open_workspace_page(page, group_id, page_id)
            detail = page.locator(f"#{detail_id}")
            toggle = detail.locator(":scope > button.label-wrap")
            if not page.locator(f"#{json_id}").is_visible():
                toggle.click()
            expect(page.locator(f"#{json_id}")).to_be_visible()
            preview_box = page.locator(f"#{preview_id}").bounding_box()
            detail_box = detail.bounding_box()
            json_box = page.locator(f"#{json_id}").bounding_box()
            assert preview_box is not None and detail_box is not None and json_box is not None
            assert abs(preview_box["height"] - detail_box["height"]) <= 2
            assert json_box["x"] >= detail_box["x"] - 1
            assert (
                json_box["x"] + json_box["width"]
                <= detail_box["x"] + detail_box["width"] + 2
            )
            assert (
                detail_box["y"] + detail_box["height"]
                - (json_box["y"] + json_box["height"])
            ) <= 12

        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    ("width", "height"),
    [(2560, 1392), (1440, 900), (820, 1180), (390, 844)],
)
def test_detail_accordions_collapse_to_headers_and_expand_without_clipping(
    workspace_url: str,
    width: int,
    height: int,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")

        _open_workspace_page(page, "build-execution", "build")
        build_detail = page.locator("#build-technical-detail")
        build_json = page.locator("#build-run-summary")
        build_metric = page.locator("#build-status-panel > .workspace-metrics")
        assert build_detail.bounding_box()["height"] <= 48  # type: ignore[index]
        assert build_metric.bounding_box()["height"] <= 80  # type: ignore[index]
        expect(build_json).to_be_hidden()
        build_toggle = build_detail.locator(":scope > button.label-wrap")
        build_toggle.click()
        expect(build_toggle).to_have_class(re.compile(r"\bopen\b"))
        expect(build_json).to_be_visible()
        if width > 900:
            input_box = page.locator("#build-input-panel").bounding_box()
            status_box = page.locator("#build-status-panel").bounding_box()
            assert input_box is not None and status_box is not None
            assert abs(
                input_box["y"] + input_box["height"]
                - status_box["y"]
                - status_box["height"]
            ) <= 2
        build_toggle.click()
        expect(build_toggle).not_to_have_class(re.compile(r"\bopen\b"))
        expect(build_json).to_be_hidden()
        assert build_detail.bounding_box()["height"] <= 48  # type: ignore[index]

        for page_id, detail_id, json_id, preview_id in (
            ("media", "media-detail", "media-detail-json", "media-preview"),
            (
                "visual-review",
                "visual-review-detail",
                "visual-review-detail-json",
                "visual-review-preview",
            ),
        ):
            _open_workspace_page(page, "media-knowledge", page_id)
            detail = page.locator(f"#{detail_id}")
            json_output = page.locator(f"#{json_id}")
            if json_output.is_visible():
                toggle = detail.locator(":scope > button.label-wrap")
                toggle.click()
                expect(toggle).not_to_have_class(re.compile(r"\bopen\b"))
            expect(json_output).to_be_hidden()
            collapsed_box = detail.bounding_box()
            assert collapsed_box is not None and collapsed_box["height"] <= 48

            toggle = detail.locator(":scope > button.label-wrap")
            toggle.click()
            expect(toggle).to_have_class(re.compile(r"\bopen\b"))
            expect(json_output).to_be_visible()
            detail_box = detail.bounding_box()
            json_box = json_output.bounding_box()
            preview_box = page.locator(f"#{preview_id}").bounding_box()
            assert detail_box is not None and json_box is not None and preview_box is not None
            if width > 900:
                assert abs(detail_box["height"] - preview_box["height"]) <= 2
            assert json_box["x"] >= detail_box["x"] - 1
            assert (
                json_box["x"] + json_box["width"]
                <= detail_box["x"] + detail_box["width"] + 2
            )

        assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 1
        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(("width", "height"), [(2560, 1392), (1440, 900)])
def test_agent_trace_table_fills_wide_container(
    workspace_url: str,
    width: int,
    height: int,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")
        _open_workspace_page(page, "agents", "agents")

        grid = page.locator("#agent-trace-table[role='grid']")
        if grid.count() == 0:
            grid = page.locator("#agent-trace-table [role='grid']")
        table = grid.locator("table.header-table")
        grid_box = grid.bounding_box()
        table_box = table.bounding_box()
        assert grid_box is not None and table_box is not None
        assert table_box["width"] >= grid_box["width"] * 0.99

        header_cells = table.locator("th").evaluate_all(
            "cells => cells.map(cell => cell.getBoundingClientRect())"
        )
        assert len(header_cells) == 7
        covered_width = max(cell["right"] for cell in header_cells) - min(
            cell["left"] for cell in header_cells
        )
        assert covered_width >= grid_box["width"] * 0.99
        assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 1
        browser.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    ("width", "height", "single_row"),
    [(2560, 1392, True), (1440, 900, True), (820, 1180, True), (390, 844, False)],
)
def test_case_filters_use_responsive_single_row_layout(
    workspace_url: str,
    width: int,
    height: int,
    single_row: bool,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.removeItem('{LOCALE_STORAGE_KEY}')")
        page.goto(workspace_url, wait_until="domcontentloaded", timeout=60_000)
        page.locator("#workspace-logo img").wait_for(state="visible")
        _open_workspace_page(page, "cases-reflection", "cases")
        row_positions = page.locator("#case-filter-row").evaluate(
            """element => [...element.querySelectorAll(':scope > .compact-inline-field')]
              .map(child => child.getBoundingClientRect())
              .filter(rect => rect.width > 0 && rect.height > 0)
              .map(rect => Math.round(rect.y))"""
        )
        assert len(row_positions) == 4
        if single_row:
            assert max(row_positions) - min(row_positions) <= 2
            alignments = page.locator(
                "#case-filter-row .compact-inline-field:not(.compact-inline-checkbox)"
            ).evaluate_all(
                """fields => fields.map(field => {
                  const label = field.querySelector('.compact-inline-label');
                  const input = field.querySelector('input');
                  const a = label.getBoundingClientRect();
                  const b = input.getBoundingClientRect();
                  return Math.abs((a.y + a.height / 2) - (b.y + b.height / 2));
                })"""
            )
            assert len(alignments) == 3
            assert all(item <= 3 for item in alignments)
        else:
            assert len(set(row_positions)) > 1
        assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 1
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
