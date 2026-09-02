from src.core.mapper_base import MapperBase
from src.domains.pauses.mapper import PauseMapper
from src.domains.shifts.entity import ShiftEntity
from src.domains.shifts.models import DbShift


class ShiftMapper(MapperBase[ShiftEntity, DbShift]):
    domain_model = ShiftEntity
    db_model = DbShift

    @classmethod
    def from_domain(cls, shift: ShiftEntity) -> DbShift:
        db_shift = DbShift(**shift.model_dump(exclude={"pauses"}))
        db_shift.pauses = [PauseMapper.from_domain(pause) for pause in shift.pauses]
        return db_shift

    @classmethod
    def update_model_from_domain(
        cls,
        db_model: DbShift,
        domain_model: ShiftEntity,
    ) -> None:
        for field, value in domain_model.model_dump(exclude={"id", "pauses"}).items():
            setattr(db_model, field, value)

        db_model.pauses = PauseMapper.upsert_all(db_model.pauses, domain_model.pauses)
