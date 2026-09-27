"""Base Rule interface and abstract rule classes."""

from abc import ABC, abstractmethod
from typing import Optional

from src.rule_engine.config import Config
from src.rule_engine.models import FoodProfile, Material, PackagingContext, RuleResult


class BaseRule(ABC):
    """Abstract base rule class that every rule implements."""

    rule_id: str
    name: str
    group: str  # "REGULATORY" or "PHYSICS"

    def __init__(self, config: Optional[Config] = None):
        self.config = config

    @abstractmethod
    def evaluate(
        self,
        food: FoodProfile,
        material: Material,
        context: PackagingContext,
    ) -> RuleResult:
        """Evaluate rule against food, material, and context."""
        pass
