class GwrRouter:
    """Routes unmanaged source models to the read-only 'gwr' DB and guards writes."""

    def _is_source_model(self, model):
        meta = model._meta
        return getattr(meta, "app_label", None) == "src" and getattr(meta, "managed", True) is False

    def db_for_read(self, model, **hints):
        return "gwr" if self._is_source_model(model) else "default"

    def db_for_write(self, model, **hints):
        if self._is_source_model(model):
            raise PermissionError("The GWR source database is read-only.")
        return "default"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db != "gwr"
