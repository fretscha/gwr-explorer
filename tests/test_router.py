from config.db_router import GwrRouter


class _FakeMeta:
    def __init__(self, managed, app_label="src"):
        self.managed = managed
        self.app_label = app_label


class _FakeModel:
    def __init__(self, managed):
        self._meta = _FakeMeta(managed)


def test_unmanaged_model_reads_from_gwr():
    assert GwrRouter().db_for_read(_FakeModel(managed=False)) == "gwr"


def test_managed_model_reads_from_default():
    assert GwrRouter().db_for_read(_FakeModel(managed=True)) == "default"


def test_write_to_source_model_is_forbidden():
    import pytest

    with pytest.raises(PermissionError):
        GwrRouter().db_for_write(_FakeModel(managed=False))


def test_migrate_blocked_on_gwr_alias():
    assert GwrRouter().allow_migrate("gwr", "src") is False
    assert GwrRouter().allow_migrate("default", "src") is True
