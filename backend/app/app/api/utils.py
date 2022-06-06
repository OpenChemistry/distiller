from fastapi import UploadFile
from passlib.context import CryptContext
from app.core.constants import BLOCKSIZE
from aiofiles.threadpool.binary import  AsyncBufferedIOBase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

async def upload_to_file(upload: UploadFile, fp:  AsyncBufferedIOBase):
    bytes = upload.file.read(BLOCKSIZE)

    while len(bytes) > 0:
        await fp.write(bytes)
        bytes = upload.file.read(BLOCKSIZE)