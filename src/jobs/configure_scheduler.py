from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.jobs.close_open_shifts import close_open_shifts


scheduler = AsyncIOScheduler()

scheduler.add_job(
    close_open_shifts,
    trigger="interval",
    minutes=1,
    id="close-open-shifts",
    coalesce=True,
    max_instances=1,
    replace_existing=True,
)
