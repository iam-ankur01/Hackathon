"""Firebase Admin SDK initialization + Firestore / Storage helpers."""
import json
import os
import uuid
import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.api_core.exceptions import NotFound

from .config import settings
from .local_db import LocalDB

_db = None
_bucket = None


def init_firebase():
    global _db, _bucket
    if settings.USE_LOCAL_DB:
        if _db is None:
            _db = LocalDB(settings.LOCAL_DB_PATH)
        _bucket = None
        return

    if firebase_admin._apps:
        _db = firestore.client()
        try:
            _bucket = storage.bucket()
        except Exception:
            _bucket = None
        return

    if settings.FIREBASE_CREDENTIALS_JSON:
        cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
    else:
        cred_path = settings.FIREBASE_CREDENTIALS
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase credentials missing. Set FIREBASE_CREDENTIALS_JSON (env) "
                f"or provide a file at {cred_path}."
            )
        cred = credentials.Certificate(cred_path)
    options = {}
    if settings.FIREBASE_STORAGE_BUCKET:
        options["storageBucket"] = settings.FIREBASE_STORAGE_BUCKET

    firebase_admin.initialize_app(cred, options)
    _db = firestore.client()
    if settings.FIREBASE_STORAGE_BUCKET:
        _bucket = storage.bucket()


def get_db():
    if _db is None:
        init_firebase()
    return _db


def upload_file(local_path: str, dest_folder: str = "uploads") -> str:
    """Upload a private file and return a Firebase Storage URI."""
    if _bucket is None:
        if settings.is_production:
            raise RuntimeError("Firebase Storage is required in production")
        return local_path
    ext = os.path.splitext(local_path)[1]
    blob_name = f"{dest_folder}/{uuid.uuid4().hex}{ext}"
    blob = _bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    return f"gs://{_bucket.name}/{blob_name}"


def delete_file(storage_uri: str) -> None:
    """Delete a private Firebase Storage object when present."""
    if not storage_uri or not storage_uri.startswith("gs://"):
        return
    if _bucket is None:
        raise RuntimeError("Firebase Storage is not initialized")
    prefix = f"gs://{_bucket.name}/"
    if not storage_uri.startswith(prefix):
        raise ValueError("Storage URI belongs to a different bucket")
    try:
        _bucket.blob(storage_uri[len(prefix):]).delete()
    except NotFound:
        pass


def download_file(storage_uri: str, local_path: str) -> str:
    """Download a private Firebase Storage object to a temporary path."""
    if not storage_uri.startswith("gs://"):
        return storage_uri
    if _bucket is None:
        raise RuntimeError("Firebase Storage is not initialized")
    prefix = f"gs://{_bucket.name}/"
    if not storage_uri.startswith(prefix):
        raise ValueError("Storage URI belongs to a different bucket")
    blob_name = storage_uri[len(prefix):]
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    _bucket.blob(blob_name).download_to_filename(local_path)
    return local_path
