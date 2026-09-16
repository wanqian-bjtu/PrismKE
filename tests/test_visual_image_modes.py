import base64
from io import BytesIO

from PIL import Image

from prismke.providers.vlm import OpenAICompatibleVLMProvider


def test_cmyk_request_copy_preserves_original(tmp_path):
    path = tmp_path / "source.jpg"
    Image.new("CMYK", (80, 120), (0, 80, 40, 0)).save(path)
    original = path.read_bytes()
    provider = OpenAICompatibleVLMProvider("https://example.test/v1", "test", "test")
    result = provider._image_data_url(str(path))
    with Image.open(BytesIO(base64.b64decode(result.split(",", 1)[1]))) as image:
        assert image.mode == "RGB"
        assert image.size == (80, 120)
    assert path.read_bytes() == original
