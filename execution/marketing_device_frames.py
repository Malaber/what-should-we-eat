"""Place authentic screenshots inside the matching Apple product artwork."""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
from io import BytesIO
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MONKR = "https://raw.githubusercontent.com/blaineam/Monkr/508b92e23947762052ee6913592b05b2fafb6733/static/devices/"
IPAD_M5 = ("https://raw.githubusercontent.com/6639835/iphone-mockup/d927b1720edd274a9cc757dd528e7f3dedf22d4d/"
           "frames/iPad%20Pro%20%28M5%29%2013-inch/iPad%20Pro%20%28M5%29%2013-inch%20-%20Silver%20-%20Portrait.png")
SOURCE_FRAMES = {
    (1179, 2556): ("iphone-15-pro", MONKR + "iphone-15-pro/natural-titanium.png",
                   "1f3db237fd209b68dab0261fa31e5b23572757469ebb8c12c5d6a6c666966cb7"),
    (1206, 2622): ("iphone-17-pro", MONKR + "iphone-17-pro/silver.png",
                   "150ddbad34638d2d49ed725ba5325196b0a7d3d58ae2f45adb996f0fc89649ca"),
    (1398, 2034): ("iphone-duo-outer-closed", MONKR + "iphone-duo-outer-closed/star-white.png",
                   "1129243087c318fdb993ee64fe1e0df6db27b33d1d8176cd9f4be59a88925145"),
    (2048, 2732): ("ipad-pro-13", MONKR + "ipad-pro-13/silver.png",
                   "25f64a2121ae4a7294306a693795ad1a48f44a2f65345f24d1738f41bc9c90f3"),
    (2064, 2752): ("ipad-pro-13-m5", IPAD_M5,
                   "0565de2da914c2b289074941c4c1d3ff04d2aad71d2ec27ec67a7876074c4024"),
}


@dataclass(frozen=True)
class DeviceFrame:
    bezel: Image.Image
    display_mask: Image.Image
    display_origin: tuple[int, int]

    def compose(self, screenshot):
        device = Image.new("RGBA", self.bezel.size)
        device.paste(screenshot.resize(self.display_mask.size, Image.Resampling.LANCZOS),
                     self.display_origin, self.display_mask)
        device.alpha_composite(self.bezel)
        return device


def prepare_frame(bezel):
    alpha = bezel.getchannel("A")
    bounds = alpha.getbbox()
    if not bounds or alpha.getpixel((bezel.width // 2, bezel.height // 2)) >= 128:
        raise ValueError("The device image needs a transparent display aperture")
    # The aperture is enclosed by the hardware. Flood from the middle to
    # distinguish it from transparent pixels outside the outer silhouette.
    aperture = alpha.point(lambda pixel: 0 if pixel < 128 else 255)
    ImageDraw.floodfill(aperture, (bezel.width // 2, bezel.height // 2), 128)
    aperture = aperture.point(lambda pixel: 255 if pixel == 128 else 0)
    screen = aperture.getbbox()
    if not screen or any((screen[0] <= bounds[0], screen[1] <= bounds[1],
                          screen[2] >= bounds[2], screen[3] >= bounds[3])):
        raise ValueError("The device display mask leaks outside the bezel")
    return DeviceFrame(bezel.crop(bounds), aperture.crop(screen), (screen[0] - bounds[0], screen[1] - bounds[1]))


def frame_bytes(name, url, digest):
    directory = Path(os.environ.get("ONIONARY_BEZELS_DIRECTORY", ROOT / ".tmp/marketing-device-frames"))
    path = directory / f"{name}.png"
    if path.exists():
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Pinned Apple bezel checksum mismatch: {path}")
        return data
    with urlopen(url, timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000 or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Pinned Apple bezel checksum mismatch: {url}")
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, delete=False) as upload:
        upload.write(data)
        temporary = Path(upload.name)
    temporary.replace(path)
    return data


@lru_cache(maxsize=len(SOURCE_FRAMES))
def load_frame(capture_size):
    if capture_size not in SOURCE_FRAMES:
        raise ValueError(f"No product bezel for the native capture size {capture_size}")
    with Image.open(BytesIO(frame_bytes(*SOURCE_FRAMES[capture_size]))) as image:
        frame = prepare_frame(image.convert("RGBA"))
    if any(abs(actual - expected) > 2 for actual, expected in zip(frame.display_mask.size, capture_size, strict=True)):
        raise ValueError(f"The Apple bezel display does not match the native capture: {capture_size}")
    return frame
