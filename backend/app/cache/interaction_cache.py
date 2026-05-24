from app.models.schemas import DrugInteraction
from app.utils.normalize import interaction_key


class InteractionCache:
    def __init__(self) -> None:
        self._cache: dict[str, DrugInteraction] = {}

    def build(self, interactions: list[dict]) -> None:
        self._cache = {}
        for raw in interactions:
            interaction = DrugInteraction(**raw)
            self._cache[interaction_key(interaction.drug_a_normalized, interaction.drug_b_normalized)] = interaction

    def lookup(self, drug_a: str, drug_b: str) -> DrugInteraction | None:
        return self._cache.get(interaction_key(drug_a, drug_b))

    @property
    def size(self) -> int:
        return len(self._cache)


interaction_cache = InteractionCache()
