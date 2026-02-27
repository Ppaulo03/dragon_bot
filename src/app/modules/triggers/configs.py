from app.kernel.config import Settings


class TriggerConfig(Settings):
    @property
    def YAML_CONFIG_PATH(self):
        return self.SETTINGS_PATH + "/triggers.yaml"


settings = TriggerConfig()
