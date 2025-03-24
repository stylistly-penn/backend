# main.py
import io
from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from celery.result import AsyncResult
from tasks import process_image_task  # Import our Celery task
from fastapi.middleware.cors import CORSMiddleware
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
import math
from collections import OrderedDict

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

app = FastAPI()

# Enable CORS for localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    """
    Endpoint to accept file uploads. It submits the image processing task to Celery
    and returns the task ID.
    """
    contents = await file.read()
    print("Submitting task with file size:", len(contents))
    task = process_image_task.delay(contents)
    print("Task submitted:", task.id)
    return {"task_id": task.id}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    Endpoint to poll for task results.
    """
    task_result = AsyncResult(task_id)

    print("Task Result is: " + str(task_result))

    if task_result.state == "PENDING":
        # Task is still waiting to be executed
        return {"state": task_result.state, "status": "Task pending..."}
    elif task_result.state == "STARTED":
        # Task is currently processing
        return {"state": task_result.state, "status": "Task in progress..."}
    elif task_result.state == "SUCCESS":
        # Task completed successfully
        return {"state": task_result.state, "result": task_result.result}
    elif task_result.state == "FAILURE":
        # Task failed
        return {"state": task_result.state, "status": str(task_result.info)}
    else:
        return {"state": task_result.state, "status": "Unknown state"}


@app.get("/")
async def main():
    """
    A simple HTML form for testing file uploads.
    """
    content = """
    <html>
        <body>
            <form action="/uploadfile/" enctype="multipart/form-data" method="post">
                <input name="file" type="file">
                <input type="submit">
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=content)
