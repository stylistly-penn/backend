# main.py
import io
from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from celery.result import AsyncResult
from tasks import process_image_task  # Import our Celery task
from fastapi.middleware.cors import CORSMiddleware

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
    print("HERE2")
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
