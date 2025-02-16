from typing import OrderedDict, Union

from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
import torch
import cv2
from PIL import Image
from pipeline import pipeline, segmentation_filter, user_palette_classification_filter, retrieval_filter
import torch.backends
from metrics_and_losses import metrics
from utils import segmentation_labels, utils
import matplotlib.pyplot as plt
from palette_classification import color_processing, palette
import glob
import json
import io
import time

device = 'mps:0' if torch.backends.mps.is_available() else 'cpu'
verbose = False
segmentation_model = 'cloud' # should be in ['local', 'cloud']
query = 'dress' # should be in ['dress', 'upper_body', 'lower_body']
n_plotted_retrieved_clothes = 50
print("Using device " + device)

# setting paths
palettes_path = 'palette_classification/palettes/'
cloth_dataset_path = 'dresscode_test_dataset/'
palette_mappings_path = 'palette_classification/clothing_palette_mappings/'

# loading reference palettes for user palette classification filter
palette_filenames = glob.glob(palettes_path + '*.csv')
reference_palettes = [palette.PaletteRGB().load(
    palette_filename.replace('\\', '/'), header=True) for palette_filename in palette_filenames]

# loading palette mappings for retrieval filter
palette_mappings_dict = {}
for category in ['dresses', 'lower_body', 'upper_body']:
    mapping_dict_filename = palette_mappings_path + category + '/' + category + '_palette_mappings.json'
    with open(mapping_dict_filename) as mapping_dict_file:
        palette_mappings_dict[category] = json.load(mapping_dict_file)

# instantiating pipeline
pl = pipeline.Pipeline()

sf = segmentation_filter.SegmentationFilter(segmentation_model)
pl.add_filter(sf)

def analyze(image: Image.Image) -> dict["Season": str, "Subtone": str]:
    img, masks = pl.execute(image, device, verbose)
    img_segmented = color_processing.colorize_segmentation_masks(masks, segmentation_labels.labels)

    labels = OrderedDict({ label: segmentation_labels.labels[label] for label in ['skin', 'hair', 'lips', 'eyes'] })

    skin_idx = utils.from_key_to_index(labels, 'skin')
    hair_idx = utils.from_key_to_index(labels, 'hair')
    lips_idx = utils.from_key_to_index(labels, 'lips')
    eyes_idx = utils.from_key_to_index(labels, 'eyes')

    segmentation_masks = color_processing.compute_segmentation_masks(img_segmented, labels)
    img_masked = color_processing.apply_masks(img, segmentation_masks)

    dominants = color_processing.compute_user_embedding(
    img_masked, n_candidates=(3, 3, 3, 3), distance_fn=metrics.rmse, debug=False)
    dominants_palette = palette.PaletteRGB('dominants', dominants)

    thresholds = (0.200, 0.422, 0.390)
    subtone = palette.compute_subtone(dominants[skin_idx])
    intensity = palette.compute_intensity(dominants[skin_idx])
    value = palette.compute_value(dominants[skin_idx], dominants[hair_idx], dominants[eyes_idx])
    contrast = palette.compute_contrast(dominants[hair_idx], dominants[eyes_idx])
    dominants_palette.compute_metrics_vector(subtone, intensity, value, contrast, thresholds)

    season_palette = palette.classify_user_palette(dominants_palette, reference_palettes)

    return {"Season": season_palette.description(), "Subtone": subtone}

def downsample_image(image: Image.Image, new_width: int, new_height: int, resample_method=Image.Resampling.NEAREST) -> Image.Image:
    """
    Downsamples an image using PIL.

    Args:
        image_path: Path to the input image.
        output_path: Path to save the downsampled image.
        new_width: Desired width of the downsampled image.
        new_height: Desired height of the downsampled image.
        resample_method: Resampling filter to use (e.g., Image.Resampling.LANCZOS, Image.Resampling.BILINEAR).
    """
    try:
        return 
    except Exception as e:
        print(f"An error occurred: {e}")

app = FastAPI()

@app.post("/analyzeupload/")
async def analyze_uploaded_file(file: UploadFile):
    input = Image.frombytes(await file.read())
    return {"filename": str(input)}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')

    max_size = 100

    # Get original dimensions
    width, height = image.size
    
    # Compute new size preserving aspect ratio
    if width > height:
        new_width = max_size
        new_height = int((height / width) * max_size)
    else:
        new_height = max_size
        new_width = int((width / height) * max_size)

    # Resize using NEAREST (fastest but lowest quality)
    pre_resize = time.time()
    resized_image = image.resize((new_width, new_height), Image.NEAREST)
    post_resize = time.time()
    result = analyze(resized_image)
    post_analyze = time.time()
    result["resize_time"] = str(post_resize - pre_resize)
    result["analyze_time"] = str(post_analyze - post_resize)
    return result


@app.get("/")
async def main():
    content = """
        <body>
            <form action="/uploadfile/" enctype="multipart/form-data" method="post">
                <input name="file" type="file">
                <input type="submit">
            </form>
        </body>
    """
    return HTMLResponse(content=content)