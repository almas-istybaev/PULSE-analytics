# MinIO API Cheatsheet (FastAPI + React)

## Backend: Python (FastAPI)

### 1. Configuration (`config.py` or similar)
```python
import ssl
from minio import Minio
from passlib.context import CryptContext # example other imports

MINIO_ENDPOINT = "localhost:9000" # or from env
MINIO_ROOT_USER = "minioadmin"
MINIO_ROOT_PASSWORD = "minioadmin"
MINIO_BUCKET_NAME = "ecommerce-assets"

# Initialize client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=False # Set to True if using HTTPS
)

# Ensure bucket exists and is public
def init_minio():
    found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
    if not found:
        minio_client.make_bucket(MINIO_BUCKET_NAME)
        # Make bucket public for reading
        policy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetBucketLocation","s3:ListBucket","s3:ListBucketMultipartUploads"],"Resource":["arn:aws:s3:::%s"]},{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject","s3:ListMultipartUploadParts","s3:PutObject","s3:AbortMultipartUpload","s3:DeleteObject"],"Resource":["arn:aws:s3:::%s/*"]}]}' % (MINIO_BUCKET_NAME, MINIO_BUCKET_NAME)
        # Note: In production restrict Put/Delete to auth only, and only make GetObject Public.
        read_only_policy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::%s/*"]}]}' % MINIO_BUCKET_NAME

        minio_client.set_bucket_policy(MINIO_BUCKET_NAME, read_only_policy)
```

### 2. Upload Endpoint (FastAPI buffers file)
Use this if you want to resize the image using Pillow before uploading.
```python
from fastapi import APIRouter, UploadFile, File
import uuid
import io

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # 1. Read file
    content = await file.read()
    
    # 2. (Optional) Resize image with PIL here
    
    # 3. Generate unique object name
    ext = file.filename.split('.')[-1]
    object_name = f"products/{uuid.uuid4()}.{ext}"
    
    # 4. Upload to Minio
    file_data = io.BytesIO(content)
    minio_client.put_object(
        MINIO_BUCKET_NAME, 
        object_name, 
        file_data, 
        length=len(content),
        content_type=file.content_type
    )
    
    return {"object_name": object_name, "url": f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"}
```

### 3. Presigned URL Upload Endpoint (Direct Upload)
Use this for large files.
```python
from datetime import timedelta

@router.get("/presigned-url")
def get_presigned_url(filename: str):
    ext = filename.split('.')[-1]
    object_name = f"products/{uuid.uuid4()}.{ext}"
    
    # Client has 1 hour to PUT the file to this URL
    url = minio_client.presigned_put_object(
        MINIO_BUCKET_NAME, 
        object_name, 
        expires=timedelta(hours=1)
    )
    return {"upload_url": url, "object_name": object_name}
```

### 4. Delete Object
```python
@router.delete("/delete/{object_name}")
def delete_image(object_name: str):
    minio_client.remove_object(MINIO_BUCKET_NAME, object_name)
    return {"status": "deleted"}
```

---

## Frontend: React

### 1. Simple Rendering (Public Bucket)
Because the bucket policy allows `s3:GetObject` publicly, you just construct the URL.
```tsx
const MINIO_URL = "http://localhost:9000/ecommerce-assets";

interface ProductImageProps {
  objectName: string; // e.g. "products/123.jpg"
}

export const ProductImage: React.FC<ProductImageProps> = ({ objectName }) => {
  return (
    <img 
      src={`${MINIO_URL}/${objectName}`} 
      alt="Product" 
      loading="lazy"
    />
  );
};
```

### 2. File Upload via Presigned URL (Recommended for perf)
```tsx
const uploadImage = async (file: File) => {
    // 1. Get presigned URL from FastAPI
    const { data } = await axios.get(`/api/v1/presigned-url?filename=${file.name}`);
    
    // 2. PUT file directly to MinIO
    await axios.put(data.upload_url, file, {
        headers: {
            'Content-Type': file.type
        }
    });

    // 3. Save data.object_name to your database logic
    return data.object_name;
};
```
