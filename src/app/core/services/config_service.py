import yaml
from pathlib import Path
from typing import Any, Dict
from app.config import settings
from app.core.logic.response import response_registry
from app.core.logic.matchers import MATCHER_REGISTRY
from app.core.logic.actions import ACTION_REGISTRY


class ConfigService:
    def __init__(self):
        self.yaml_path = Path(settings.YAML_CONFIG_PATH)

    def get_constants(self) -> Dict[str, Any]:
        """Retorna as opções disponíveis para preencher dropdowns no front."""
        return {
            "matchers": list(MATCHER_REGISTRY.keys()),
            "actions": list(ACTION_REGISTRY.keys()),
            "response_types": response_registry.list_handlers(),
        }

    def load_triggers_data(self) -> Dict[str, Any]:
        """Lê o YAML e garante a integridade da estrutura para o dashboard."""
        if not self.yaml_path.exists():
            return {"triggers": [], "no_triggers": []}

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for key in ["triggers", "no_triggers"]:
            items = data.get(key, [])
            for item in items:
                item["params"] = item.get("params", {})
                item["name"] = item.get("name", "Sem Nome")
            data[key] = items

        return data

    def save_triggers_data(self, data: Dict[str, Any]) -> bool:
        """Salva as alterações vindas do Dashboard de volta no YAML."""
        try:
            with open(self.yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception:
            return False


config_service = ConfigService()
