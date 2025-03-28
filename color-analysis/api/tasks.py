# tasks.py
import io
import time
from PIL import Image
from celery_app import celery_app

# Import your analysis function and any dependencies
from pipeline import pipeline, segmentation_filter
from palette_classification import color_processing, palette
from metrics_and_losses import metrics
from utils import segmentation_labels, utils
from collections import OrderedDict

import glob
import json
import torch
import torch.backends
import math

# --- (Initialize global variables as in your original script) ---
device = "mps:0" if torch.backends.mps.is_available() else "cpu"
verbose = False
segmentation_model = "cloud"
query = "dress"
n_plotted_retrieved_clothes = 50
print("Using device " + device)

palettes_path = "palette_classification/palettes/"
cloth_dataset_path = "dresscode_test_dataset/"
palette_mappings_path = "palette_classification/clothing_palette_mappings/"

palette_filenames = glob.glob(palettes_path + "*.csv")
reference_palettes = [
    palette.PaletteRGB().load(filename.replace("\\", "/"), header=True)
    for filename in palette_filenames
]

palette_mappings_dict = {}
for category in ["dresses", "lower_body", "upper_body"]:
    mapping_dict_filename = (
        palette_mappings_path + category + "/" + category + "_palette_mappings.json"
    )
    with open(mapping_dict_filename) as mapping_file:
        palette_mappings_dict[category] = json.load(mapping_file)

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

    # Thresholds
    # I: 0.422, V: 0.390, C: 0.2

    # Autumn
    # metrics vector (SIVC)
    # 1000
    # Warm, 0.211, 0.195, 0.1
    autumn = ([1, 0.5, 0.5, 0.25], 'autumn')

    # Spring
    # 1111
    # Warm, 0.844, 0.780, 0.4
    spring = ([1, 0.5, 0.5, 0.45], 'spring')

    # Summer
    # 0010
    # Cold, 0.211, 0.780, 0.1
    summer = ([0, 0.211, 0.480, 0.1], 'summer')

    # Winter
    # 0101
    # Cold, 0.844, 0.195, 0.4
    winter = ([0, 0.422, 0.195, 0.2], 'winter')

    seasons = [autumn, spring, summer, winter]

    thresholds = (0.200, 0.422, 0.390)
    subtone = palette.compute_subtone(dominants[skin_idx])
    intensity = palette.compute_intensity(dominants[skin_idx])
    value = palette.compute_value(dominants[skin_idx], dominants[hair_idx], dominants[eyes_idx])
    contrast = palette.compute_contrast(dominants[hair_idx], dominants[skin_idx])
    dominants_palette.compute_metrics_vector(subtone, intensity, value, contrast, thresholds)

    min_sqrt_dist = math.inf
    season = ''
    vector = [1 if subtone == 'warm' else 0, intensity, value, contrast]
    for (vals, desc) in seasons:
        sqr_dist = sum([(vals[i] - vector[i]) ** 2 for i in range(4)])
        sqrt_dist = math.sqrt(sqr_dist)
        if sqrt_dist < min_sqrt_dist:
            season = desc
            min_sqrt_dist = sqrt_dist

    return {"Season": season, "Subtone": subtone, "Int": str(intensity), "Val": str(value), "Con": str(contrast), "Mtrx": str(dominants_palette.metrics_vector())}


@celery_app.task(name="tasks.process_image_task")
def process_image_task(file_contents: bytes) -> dict:
    """
    Celery task that receives the raw file bytes, processes the image,
    and returns the analysis result.
    """
    try:
        image = Image.open(io.BytesIO(file_contents)).convert("RGB")
    except Exception as e:
        return {"error": f"Unable to open image: {str(e)}"}

    max_size = 300
    width, height = image.size
    if width > height:
        new_width = max_size
        new_height = int((height / width) * max_size)
    else:
        new_height = max_size
        new_width = int((width / height) * max_size)

    pre_resize = time.time()
    resized_image = image.resize((new_width, new_height), Image.NEAREST)
    post_resize = time.time()
    result = analyze(resized_image)
    post_analyze = time.time()
    result["resize_time"] = str(post_resize - pre_resize)
    result["analyze_time"] = str(post_analyze - post_resize)
    return result
