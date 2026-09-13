"""The importer caches ch.zip and only downloads when forced or missing."""
import urllib.request
from pathlib import Path

import pytest

from src.management.commands.import_gwr import Command


def _opts(**over):
    base = {"file": None, "force_download": False, "cache": None, "url": "http://example.test/ch.zip"}
    base.update(over)
    return base


def test_reuses_cache_without_downloading(tmp_path, monkeypatch):
    cache = tmp_path / "ch.zip"
    cache.write_bytes(b"cached")
    calls = []
    monkeypatch.setattr(urllib.request, "urlretrieve", lambda *a, **k: calls.append(a))

    result = Command()._obtain(_opts(cache=str(cache)))

    assert result == cache
    assert calls == [], "must not re-download when the cache already exists"


def test_downloads_when_cache_missing(tmp_path, monkeypatch):
    cache = tmp_path / "sub" / "ch.zip"  # parent dir does not exist yet

    def fake_download(url, dest, **kwargs):
        Path(dest).write_bytes(b"fresh")

    monkeypatch.setattr(urllib.request, "urlretrieve", fake_download)

    result = Command()._obtain(_opts(cache=str(cache)))

    assert result == cache
    assert cache.read_bytes() == b"fresh"


def test_force_download_replaces_existing_cache(tmp_path, monkeypatch):
    cache = tmp_path / "ch.zip"
    cache.write_bytes(b"old")
    monkeypatch.setattr(urllib.request, "urlretrieve", lambda url, dest, **kw: Path(dest).write_bytes(b"new"))

    Command()._obtain(_opts(cache=str(cache), force_download=True))

    assert cache.read_bytes() == b"new"


def test_explicit_file_bypasses_cache(tmp_path, monkeypatch):
    src = tmp_path / "local.zip"
    src.write_bytes(b"local")
    monkeypatch.setattr(
        urllib.request, "urlretrieve", lambda *a, **k: pytest.fail("must not download when --file is given")
    )

    result = Command()._obtain(_opts(file=str(src)))

    assert result == Path(src)
