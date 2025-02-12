import bcrypt
from aiofiles.threadpool.binary import AsyncBufferedIOBase
from fastapi import UploadFile

from app.core.constants import BLOCKSIZE


# See https://github.com/fastapi/fastapi/discussions/11773#discussioncomment-10640267
def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(
        bytes(plain_password, encoding="utf-8"),
        bytes(hashed_password, encoding="utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        bytes(password, encoding="utf-8"),
        bcrypt.gensalt(),
    ).decode()


async def upload_to_file(upload: UploadFile, fp: AsyncBufferedIOBase):
    bytes = upload.file.read(BLOCKSIZE)

    while len(bytes) > 0:
        await fp.write(bytes)
        bytes = upload.file.read(BLOCKSIZE)
