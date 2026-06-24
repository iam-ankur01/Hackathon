"""Small persistent Firestore-compatible store for local development."""
from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy


class LocalDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict | None):
        self.id = doc_id
        self._data = deepcopy(data) if data is not None else None

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return deepcopy(self._data)


class LocalDocumentReference:
    def __init__(self, db: "LocalDB", collection: str, doc_id: str):
        self._db = db
        self._collection = collection
        self.id = doc_id

    def get(self) -> LocalDocumentSnapshot:
        return LocalDocumentSnapshot(
            self.id, self._db._read_document(self._collection, self.id)
        )

    def set(self, data: dict):
        self._db._write_document(self._collection, self.id, data, merge=False)

    def update(self, data: dict):
        self._db._write_document(self._collection, self.id, data, merge=True)

    def delete(self):
        self._db._delete_document(self._collection, self.id)


class LocalQuery:
    def __init__(
        self,
        db: "LocalDB",
        collection: str,
        filters: list[tuple[str, str, object]] | None = None,
        result_limit: int | None = None,
    ):
        self._db = db
        self._collection = collection
        self._filters = filters or []
        self._result_limit = result_limit

    def where(self, field: str, operator: str, value) -> "LocalQuery":
        if operator != "==":
            raise NotImplementedError("Local database currently supports only == queries")
        return LocalQuery(
            self._db,
            self._collection,
            [*self._filters, (field, operator, value)],
            self._result_limit,
        )

    def limit(self, count: int) -> "LocalQuery":
        return LocalQuery(
            self._db, self._collection, self._filters, max(0, int(count))
        )

    def stream(self):
        rows = self._db._read_collection(self._collection)
        snapshots = []
        for doc_id, data in rows.items():
            if all(data.get(field) == value for field, _, value in self._filters):
                snapshots.append(LocalDocumentSnapshot(doc_id, data))
        if self._result_limit is not None:
            snapshots = snapshots[: self._result_limit]
        return iter(snapshots)


class LocalCollectionReference(LocalQuery):
    def __init__(self, db: "LocalDB", collection: str):
        super().__init__(db, collection)

    def document(self, doc_id: str | None = None) -> LocalDocumentReference:
        return LocalDocumentReference(
            self._db, self._collection, doc_id or uuid.uuid4().hex
        )


class LocalDB:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._save({})

    def collection(self, name: str) -> LocalCollectionReference:
        return LocalCollectionReference(self, name)

    def _load(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, data: dict):
        temp_path = f"{self.path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.path)

    def _read_collection(self, name: str) -> dict:
        with self._lock:
            return deepcopy(self._load().get(name, {}))

    def _read_document(self, collection: str, doc_id: str) -> dict | None:
        with self._lock:
            return deepcopy(self._load().get(collection, {}).get(doc_id))

    def _write_document(self, collection: str, doc_id: str, values: dict, merge: bool):
        with self._lock:
            data = self._load()
            documents = data.setdefault(collection, {})
            if merge:
                documents.setdefault(doc_id, {}).update(deepcopy(values))
            else:
                documents[doc_id] = deepcopy(values)
            self._save(data)

    def _delete_document(self, collection: str, doc_id: str):
        with self._lock:
            data = self._load()
            data.get(collection, {}).pop(doc_id, None)
            self._save(data)
