from datetime import UTC

from src.messaging.entity import BaseDomainEvent, EventEnvelope
from src.messaging.models import DbEvent


class MessagingMapper:
    @classmethod
    def from_domain(cls, event: BaseDomainEvent) -> DbEvent:
        data = event.model_dump(
            mode="json",
            exclude={"reference_id", "occurrence_datetime"},
        )
        event_type = type(event).__name__

        return DbEvent(
            type=event_type,
            subject=event.reference_id,
            data=data,
            occurred_at=event.occurrence_datetime,
        )

    @classmethod
    def to_domain(cls, db_event: DbEvent) -> EventEnvelope:
        occurrence_datetime = db_event.occurred_at
        if occurrence_datetime.tzinfo is None:
            occurrence_datetime = occurrence_datetime.replace(tzinfo=UTC)
        else:
            occurrence_datetime = occurrence_datetime.astimezone(UTC)

        return EventEnvelope(
            id=db_event.id,
            type=db_event.type,
            subject=db_event.subject,
            data=db_event.data,
            occurrence_datetime=occurrence_datetime,
        )
