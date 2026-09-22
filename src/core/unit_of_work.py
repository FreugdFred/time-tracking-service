from types import TracebackType

from dependency_container import Dependency
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    session: AsyncSession

    async def __aenter__(self) -> AsyncSession:
        self.session = Dependency.get(AsyncSession)
        return self.session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()

        except BaseException:
            await self.session.rollback()
            raise

        finally:
            await self.session.close()