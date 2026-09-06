from messaging.entity import BaseDomainEvent, EventEnvelope
from messaging.models import DbEvent


class MessagingMapper:
    @classmethod
    def from_domain(cls, event: type[BaseDomainEvent]) -> DbEvent:
        data = event.model_dump(exclude={"reference_id", "occurrence_datetime"})
        event_type = type(event).__name__

        return DbEvent(
            type=event_type,
            subject=event.reference_id,
            data=data,
            occurred_at=event.occurrence_datetime
        )

    @classmethod
    def to_domain(cls, db_event: DbEvent) -> EventEnvelope:
         return EventEnvelope(
            id=db_event.id,
            type=db_event.type,
            subject=db_event.subject,
            data=db_event.data,
         )


