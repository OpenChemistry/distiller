from typing import Generator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings
from app.crud import user as crud
from app.db.session import SessionLocal
from app.schemas import TokenData

# DB


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# API key
api_key_query = APIKeyQuery(name=settings.API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=settings.API_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):
    if api_key_query == settings.API_KEY:
        return api_key_query
    elif api_key_header == settings.API_KEY:
        return api_key_header
    elif api_key_cookie == settings.API_KEY:
        return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
oauth2_scheme_no_error = OAuth2PasswordBearer(
    tokenUrl="/api/v1/token", auto_error=False
)


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def oauth2_password_bearer_or_api_key(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_no_error),
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):

    if token is not None:
        return await get_current_user(db, token)
    else:
        return await get_api_key(api_key_query, api_key_header, api_key_cookie)
