import boto3
from botocore.client import Config

# Данные Cloudflare R2
ACCESS_KEY = "xcas41dasde"
SECRET_KEY = "asd123asdasw"
BUCKET_NAME = "your-bucket-name"
ENDPOINT_URL = "https://your-account-id.r2.cloudflarestorage.com"
OBJECT_NAME = "folder_in_bucket/local_file.txt"

# Создание клиента S3
s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

# Генерация временной ссылки (действует 1 час)
url = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": BUCKET_NAME, "Key": OBJECT_NAME},
    ExpiresIn=3600,  # Срок действия ссылки (в секундах)
)

print(f"Временная ссылка на файл: {url}")
