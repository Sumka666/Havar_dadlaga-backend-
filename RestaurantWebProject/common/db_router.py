class AppDatabaseRouter:

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'admin_panel':
            return 'admin_db'
        if model._meta.app_label == 'api':
            return 'api_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'admin_panel':
            return 'admin_db'
        if model._meta.app_label == 'api':
            return 'api_db'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'admin_panel':
            return db == 'admin_db'
        if app_label == 'api':
            return db == 'api_db'
        return db == 'default'
