"""Download dark CartoDB tiles for Austin and composite into a single image."""
import math
import urllib.request
import os
from pathlib import Path

# Austin bounding box (matching projections.ts)
LAT_MIN, LAT_MAX = 30.10, 30.55
LNG_MIN, LNG_MAX = -97.97, -97.53

# Output dimensions (matching MAP_W x MAP_H in projections.ts)
OUT_W, OUT_H = 1344, 1080

ZOOM = 12  # Good detail level for city
TILE_SIZE = 256
TILE_URL = "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"

def lat_lng_to_tile(lat, lng, zoom):
    """Convert lat/lng to tile x,y at given zoom."""
    n = 2 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_lat_lng(x, y, zoom):
    """Convert tile x,y to lat/lng of its NW corner."""
    n = 2 ** zoom
    lng = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lng

# Get tile range
x_min, y_max = lat_lng_to_tile(LAT_MIN, LNG_MIN, ZOOM)  # SW corner
x_max, y_min = lat_lng_to_tile(LAT_MAX, LNG_MAX, ZOOM)  # NE corner

# Include boundary tiles
x_max += 1
y_max += 1

print(f"Zoom {ZOOM}: tiles x=[{x_min}..{x_max}], y=[{y_min}..{y_max}]")
print(f"Total tiles: {(x_max - x_min + 1) * (y_max - y_min + 1)}")

# Download tiles
tile_dir = Path("video/scripts/tiles")
tile_dir.mkdir(parents=True, exist_ok=True)

for tx in range(x_min, x_max + 1):
    for ty in range(y_min, y_max + 1):
        fname = tile_dir / f"{ZOOM}_{tx}_{ty}.png"
        if fname.exists():
            print(f"  cached {tx},{ty}")
            continue
        url = TILE_URL.format(z=ZOOM, x=tx, y=ty)
        print(f"  downloading {tx},{ty} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "ChargePilot-Demo/1.0"})
        try:
            with urllib.request.urlopen(req) as resp:
                fname.write_bytes(resp.read())
        except Exception as e:
            print(f"  FAILED {tx},{ty}: {e}")

# Now composite with PIL
try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image

# @2x tiles are 512x512
TILE_PX = 512

# Get pixel coordinates of our bounding box within the tile grid
def lat_lng_to_pixel(lat, lng, zoom):
    """Convert lat/lng to absolute pixel coordinate at given zoom."""
    n = 2 ** zoom
    px = (lng + 180.0) / 360.0 * n * TILE_PX
    lat_rad = math.radians(lat)
    py = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * TILE_PX
    return px, py

# Pixel coords of our bounding box
px_left, py_bottom = lat_lng_to_pixel(LAT_MIN, LNG_MIN, ZOOM)
px_right, py_top = lat_lng_to_pixel(LAT_MAX, LNG_MAX, ZOOM)

# Pixel coords of tile grid origin
grid_px_left = x_min * TILE_PX
grid_py_top = y_min * TILE_PX

# Create composite of all tiles
grid_w = (x_max - x_min + 1) * TILE_PX
grid_h = (y_max - y_min + 1) * TILE_PX
composite = Image.new("RGB", (grid_w, grid_h), (4, 8, 15))  # Match THEME.bg

for tx in range(x_min, x_max + 1):
    for ty in range(y_min, y_max + 1):
        fname = tile_dir / f"{ZOOM}_{tx}_{ty}.png"
        if not fname.exists():
            continue
        tile_img = Image.open(fname)
        paste_x = (tx - x_min) * TILE_PX
        paste_y = (ty - y_min) * TILE_PX
        composite.paste(tile_img, (paste_x, paste_y))

# Crop to our bounding box
crop_left = int(px_left - grid_px_left)
crop_top = int(py_top - grid_py_top)
crop_right = int(px_right - grid_px_left)
crop_bottom = int(py_bottom - grid_py_top)

cropped = composite.crop((crop_left, crop_top, crop_right, crop_bottom))

# Resize to target dimensions
final = cropped.resize((OUT_W, OUT_H), Image.LANCZOS)

out_path = Path("video/public/austin-map.png")
final.save(out_path, "PNG")
print(f"\nSaved {out_path} ({OUT_W}x{OUT_H})")
