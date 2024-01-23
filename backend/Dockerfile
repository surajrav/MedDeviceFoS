FROM python:3.12

WORKDIR /code

RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc --create-dirs -o ./minio-binaries/mc
RUN chmod +x ./minio-binaries/mc

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY app /code/app

CMD ["./app/app_init.sh"]
