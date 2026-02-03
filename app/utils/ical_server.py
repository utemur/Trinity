"""Минимальный HTTP-сервер для iCal экспорта."""

import logging
from datetime import datetime, timedelta

from aiohttp import web

from app.config import config
from app.services.calendar_service import generate_ical_content

logger = logging.getLogger(__name__)


async def ical_handler(request: web.Request) -> web.Response:
    org_id = request.match_info.get("org_id")
    token = request.match_info.get("token")
    if not org_id or not token:
        raise web.HTTPNotFound()

    from app.db.session import async_session_factory
    from app.db.repo import OrganizationRepo, BookingRepo
    from sqlalchemy.orm import selectinload
    from app.db.models import Booking, Organization

    async with async_session_factory() as session:
        org = await OrganizationRepo.get_by_ical_token(session, token)
        if not org or str(org.id) != str(org_id):
            raise web.HTTPNotFound()

        from sqlalchemy import select
        result = await session.execute(
            select(Booking)
            .where(Booking.organization_id == org.id)
            .where(Booking.status.in_(["PENDING", "CONFIRMED"]))
            .where(Booking.start_dt >= datetime.utcnow() - timedelta(days=1))
            .options(selectinload(Booking.service))
            .order_by(Booking.start_dt)
        )
        bookings = result.scalars().all()

    content = generate_ical_content(org, list(bookings))
    return web.Response(
        text=content,
        content_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="calendar.ics"'},
    )


async def run_ical_server() -> None:
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/ical/{org_id}/{token}.ics", ical_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.ICAL_SERVER_PORT)
    await site.start()
    logger.info("iCal server listening on port %s", config.ICAL_SERVER_PORT)
