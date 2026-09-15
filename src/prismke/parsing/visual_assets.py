"""Select non-overlapping visual assets for OCR and VLM analysis."""

from prismke.domain import DocumentIR, MediaAsset


def select_analysis_assets(document: DocumentIR) -> list[MediaAsset]:
    """Prefer a rendered scan over embedded images from the same textless PDF page."""

    rendered_scan_pages = {
        asset.page_number
        for asset in document.media_assets
        if asset.origin == "pdf_page_render"
        and asset.requires_ocr
        and asset.page_number is not None
    }
    return [
        asset
        for asset in document.media_assets
        if not (
            asset.origin == "pdf_embedded"
            and asset.page_number in rendered_scan_pages
        )
    ]
