# Utilities
import matplotlib.pyplot as plt
import pandas as pd
# import getpass

# https://documentation.dataspace.copernicus.eu/notebook-samples/sentinelhub/cloudless_process_api.html

from sentinelhub import (
    SHConfig,
    DataCollection,
    SentinelHubCatalog,
    SentinelHubRequest,
    SentinelHubStatistical,
    BBox,
    bbox_to_dimensions,
    CRS,
    MimeType,
    Geometry,
)

from utils import plot_image

# NOMAINI ŠĪS LĪNIJAS
SH_CLIENT_ID = ""
SH_CLIENT_SECRET = ""

# Only run this cell if you have not created a configuration.

config = SHConfig(
    sh_client_id=SH_CLIENT_ID,
    sh_client_secret=SH_CLIENT_SECRET,
    sh_base_url="https://sh.dataspace.copernicus.eu",
    sh_token_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)

# The bounding box in WGS84 coordinate system is [(longitude and latitude coordinates of lower left and upper right corners)].
# http://bboxfinder.com/#0.000000,0.000000,0.000000,0.000000        <----- koordinātes vislabāk dabūt no šitās mājaslapas
# aoi_coords_wgs84 = [12.292349, 47.810849, 12.569037, 47.967123]
aoi_coords_wgs84 = [23.968306,56.882188,24.142628,56.928257]        # Koordinātes priekš lauka

resolution = 3      # Resolution in meters
aoi_bbox = BBox(bbox=aoi_coords_wgs84, crs=CRS.WGS84)
aoi_size = bbox_to_dimensions(aoi_bbox, resolution=resolution)

print(f"Image shape at {resolution} m resolution: {aoi_size} pixels")

S2l3_cloudless_mosaic = DataCollection.define_byoc(
    collection_id="5460de54-082e-473a-b6ea-d5cbe3c17cca"
)

# Šitais kaut kā apstrādā to bildi
evalscript_true_color = """
//VERSION=3
function setup() {
  return {
    input: ["B04","B03","B02", "dataMask"],
    output: { bands: 4 }
  };
}

// Contrast enhance / highlight compress

const maxR = 3.0; // max reflectance
const midR = 0.13;
const sat = 1.2;
const gamma = 1.8;
const scalefac = 10000;

function evaluatePixel(smp) {
  const rgbLin = satEnh(sAdj(smp.B04/scalefac), sAdj(smp.B03/scalefac), sAdj(smp.B02/scalefac));
  return [sRGB(rgbLin[0]), sRGB(rgbLin[1]), sRGB(rgbLin[2]), smp.dataMask];
}

function sAdj(a) {
  return adjGamma(adj(a, midR, 1, maxR));
}

const gOff = 0.01;
const gOffPow = Math.pow(gOff, gamma);
const gOffRange = Math.pow(1 + gOff, gamma) - gOffPow;

function adjGamma(b) {
  return (Math.pow((b + gOff), gamma) - gOffPow)/gOffRange;
}

// Saturation enhancement
function satEnh(r, g, b) {
  const avgS = (r + g + b) / 3.0 * (1 - sat);
  return [clip(avgS + r * sat), clip(avgS + g * sat), clip(avgS + b * sat)];
}

function clip(s) {
  return s < 0 ? 0 : s > 1 ? 1 : s;
}

//contrast enhancement with highlight compression
function adj(a, tx, ty, maxC) {
  var ar = clip(a / maxC, 0, 1);
  return ar * (ar * (tx/maxC + ty -1) - ty) / (ar * (2 * tx/maxC - 1) - tx/maxC);
}

const sRGB = (c) => c <= 0.0031308 ? (12.92 * c) : (1.055 * Math.pow(c, 0.41666666666) - 0.055);"""

# Te taisa pieprasījumu uz serveri lai dabūtu bildi
request_true_color = SentinelHubRequest(
    evalscript=evalscript_true_color,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=S2l3_cloudless_mosaic,
            time_interval=("2023-07-01", "2023-07-02"),
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
    bbox=aoi_bbox,
    size=aoi_size,
    config=config,
    data_folder="./data",
)

true_color_imgs = request_true_color.get_data(save_data=True)

print(
    f"Returned data is of type = {type(true_color_imgs)} and length {len(true_color_imgs)}."
)
print(
    f"Single element in the list is of type {type(true_color_imgs[-1])} and has shape {true_color_imgs[-1].shape}"
)

image = true_color_imgs[0]
print(f"Image type: {image.dtype}")

# plot function
# factor 1/255 to scale between 0-1
# factor 1 to keep brightness scaling that was already handled in the evalscript
plot_image(image, factor=1 / 255, clip_range=(0, 1))    # Uztaisa vizuāli bildi un saglabā. Faila nosaukumu var mainīt utils.py

