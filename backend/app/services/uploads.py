"""Upload validation and sanitising. The processed bytes are what the model sees and what is (optionally) stored; the original is never kept.

Order: declared type -> magic bytes -> header-only size check (decompression-bomb guard BEFORE decoding) -> decode first frame only ->
EXIF orientation -> rebuild the image from raw pixels (drops EXIF/GPS, ICC, text chunks and every other metadata) -> re-encode."""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
MIME = {"image/png": PNG_MAGIC, "image/jpeg": JPEG_MAGIC}


class UploadError(Exception):
    def __init__(self, status: int, code: str):
        super().__init__(code)
        self.status, self.code = status, code


def process_image(data: bytes, declared: str, max_pixels: int) -> tuple[bytes, str]:
    """Returns (sanitised image bytes, mime). Raises UploadError(status, code); codes are error.* template ids."""
    declared = (declared or "").split(";")[0].strip().lower()
    if declared == "application/pdf" or data[:5] == b"%PDF-":
        raise UploadError(415, "pdf_not_supported")
    if declared not in MIME or not data.startswith(MIME[declared]):
        raise UploadError(415, "unsupported_file")  # wrong type, or the bytes do not match what was declared
    try:
        img = Image.open(io.BytesIO(data))  # header only: no pixel data decoded yet
        if img.format not in ("PNG", "JPEG") or img.width * img.height > max_pixels or min(img.size) < 1:
            raise UploadError(422, "image_invalid")
        img.seek(0)
        img.load()  # first frame only (animated PNG / multi-picture JPEG: later frames are ignored)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            flat = Image.new("RGB", rgba.size, "white")
            flat.paste(rgba, mask=rgba.split()[3])
            img = flat
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        clean = Image.frombytes(img.mode, img.size, img.tobytes())  # fresh image: empty .info, no EXIF/ICC/text
        out = io.BytesIO()
        if declared == "image/png":
            clean.save(out, "PNG")
        else:
            clean.save(out, "JPEG", quality=92)
        return out.getvalue(), declared
    except UploadError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError, ValueError, SyntaxError, EOFError):
        raise UploadError(422, "image_invalid")
