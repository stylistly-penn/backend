FROM jjanzic/docker-python3-opencv:latest

WORKDIR /api

COPY ./api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./api .

CMD ["fastapi", "dev", "index.py"]