"""Firebase Admin SDK initialization + Firestore / Storage helpers."""
import json
import os
import uuid
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore, storage

from .config import settings

_db = None
_bucket = None


def init_firebase():
    global _db, _bucket
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
    """Upload a local file to Firebase Storage; return public URL.
    Falls back to returning the local path if no bucket configured."""
    if _bucket is None:
        return local_path
    ext = os.path.splitext(local_path)[1]
    blob_name = f"{dest_folder}/{uuid.uuid4().hex}{ext}"
    blob = _bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url
