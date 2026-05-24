from app.database.supabase_client import get_supabase
from app.seed.clinical_data import ALIASES, ALLERGY_CROSS_REACTIVITY, DRUGS, INTERACTIONS
from app.seed.patients import PATIENTS
from app.utils.logger import get_logger
from app.utils.normalize import normalize_drug_name


logger = get_logger(__name__)


class ClinicalRepository:
    _remote_disabled = False

    def __init__(self) -> None:
        self.client = get_supabase()

    def _select(self, table: str, fallback: list[dict], key_fields: tuple[str, ...] = ("id",)) -> list[dict]:
        if not self.client or ClinicalRepository._remote_disabled:
            return fallback
        try:
            remote = self.client.table(table).select("*").execute().data or []
            if not remote:
                return fallback
            return self._merge_seed_with_remote(fallback, remote, key_fields)
        except Exception as exc:
            ClinicalRepository._remote_disabled = True
            logger.warning(
                "Supabase table lookup failed for '%s'; using bundled seed data for this run. "
                "Apply supabase/schema.sql and supabase/seed.sql if you want remote data. Error: %s",
                table,
                exc,
            )
            return fallback

    def _merge_seed_with_remote(self, fallback: list[dict], remote: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
        merged: dict[tuple, dict] = {}
        for row in fallback:
            merged[self._row_key(row, key_fields)] = row
        for row in remote:
            merged[self._row_key(row, key_fields)] = row
        return list(merged.values())

    def _row_key(self, row: dict, key_fields: tuple[str, ...]) -> tuple:
        return tuple(row.get(field) for field in key_fields)

    def get_drugs(self) -> list[dict]:
        return self._select("drugs", DRUGS, ("generic_name_normalized",))

    def get_interactions(self) -> list[dict]:
        return self._select("drug_interactions", INTERACTIONS, ("drug_a_normalized", "drug_b_normalized"))

    def get_allergy_cross_reactivity(self) -> list[dict]:
        return self._select("allergy_cross_reactivity", ALLERGY_CROSS_REACTIVITY, ("allergy_class", "cross_reacts_with"))

    def get_aliases(self) -> list[dict]:
        fallback = [
            {"id": idx + 1, "alias": normalize_drug_name(alias), "actual_drug": normalize_drug_name(actual)}
            for idx, (alias, actual) in enumerate(ALIASES)
        ]
        return self._select("drug_aliases", fallback, ("alias",))

    def get_patients(self) -> list[dict]:
        return self._select("patients", PATIENTS, ("id",))
