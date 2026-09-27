"""Configuration loader for the Rule Engine."""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "rule_config.yaml"


class Config:
    """Wrapper class for rule engine configuration parameters."""

    def __init__(self, raw_config: Dict[str, Any]):
        self.raw_config = raw_config
        self.units = raw_config.get("units", {
            "canonical_otr": "cm3/m2/day",
            "canonical_wvtr": "g/m2/day",
        })
        self.rules = raw_config.get("rules", {})
        self.food_categories = raw_config.get("food_categories", {})

    @classmethod
    def load_from_yaml(cls, path: Optional[Path | str] = None) -> "Config":
        """Load configuration from a YAML file."""
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(data)

    def get_rule_config(self, rule_name: str) -> Dict[str, Any]:
        """Get parameters for a specific rule."""
        return self.rules.get(rule_name, {})

    def get_category_bounds(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Get OTR/WVTR min/max requirement bounds for a food category."""
        return self.food_categories.get(category_name)
