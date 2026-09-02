from pydantic import BaseModel

from src.core.base import Base


class MapperBase[DomainModel: BaseModel, DbModel: Base]:
    db_model: type[DbModel]
    domain_model: type[DomainModel]

    @classmethod
    def get_db_model(cls) -> type[DbModel]:
        return cls.db_model

    @classmethod
    def get_domain_model(cls) -> type[DomainModel]:
        return cls.domain_model

    @classmethod
    def to_domain(cls, db_model: DbModel, /) -> DomainModel:
        return cls.domain_model.model_validate(db_model)

    @classmethod
    def from_domain(cls, domain_model: DomainModel, /) -> DbModel:
        return cls.db_model(**domain_model.model_dump())

    @classmethod
    def update_model_from_domain(
        cls,
        db_model: DbModel,
        domain_model: DomainModel,
    ) -> None:
        for field, value in domain_model.model_dump(exclude={"id"}).items():
            setattr(db_model, field, value)
