
from src.core.mapper_base import MapperBase
from src.domains.pauses.entity import PauseEntity
from src.domains.pauses.models import DbPause


class PauseMapper(MapperBase[PauseEntity, DbPause]):
    domain_model = PauseEntity
    db_model = DbPause

    @staticmethod
    def upsert_all(
        db_pauses: list[DbPause],
        pauses: list[PauseEntity],
    ) -> list[DbPause]:
        existing_pauses = {pause.id: pause for pause in db_pauses}
        updated_pauses: list[DbPause] = []

        for pause in pauses:
            db_pause = existing_pauses.get(pause.id)
            if db_pause is None:
                updated_pauses.append(PauseMapper.from_domain(pause))
                continue

            PauseMapper.update_model_from_domain(db_pause, pause)
            updated_pauses.append(db_pause)

        return updated_pauses
