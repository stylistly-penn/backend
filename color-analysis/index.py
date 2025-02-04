from typing import OrderedDict, Union

from fastapi import FastAPI
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

app = FastAPI()

@app.get("/")
def read_root():
    return {"Message": "Welcome to Stylistly!"}

@app.get("/items/{item_id}")
def read_item(item_id: str, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/analyze/{image_path}")
def analyze_image(image_path: str, q: Union[str, None] = None):
    input = Image.open(image_path).convert('RGB')
    
    sf = segmentation_filter.SegmentationFilter(segmentation_model)
    pl.add_filter(sf)

    img, masks = pl.execute(input, device, verbose)
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
    subtone = palette.compute_subtone(dominants[lips_idx])
    intensity = palette.compute_intensity(dominants[skin_idx])
    value = palette.compute_value(dominants[skin_idx], dominants[hair_idx], dominants[eyes_idx])
    contrast = palette.compute_contrast(dominants[hair_idx], dominants[eyes_idx])
    dominants_palette.compute_metrics_vector(subtone, intensity, value, contrast, thresholds)

    season_palette = palette.classify_user_palette(dominants_palette, reference_palettes)

    return {"Season": season_palette.description(), "Subtone": subtone}