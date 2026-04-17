# ===== main.py =====
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from checker import check_group3_presence_tickets, check_wrong_assignee_tickets
from config import (
    CHECK_INTERVAL_MINUTES,
    CRM_URL,
    CRM_URL_GROUP3,
    CRM_URL_RETAIL_WAREHOUSE,
    get_telegram_destinations,
)
from notifier import send_alerts
from scraper import get_tickets
from state import init_db


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    # Reduce zgomotul din librarii HTTP/Telegram (request logs per mesaj trimis).
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def job() -> None:
    logging.info("=== Rulare job ===")
    try:
        # IT Core
        tickets_core = await get_tickets(CRM_URL)
        core_alerts = check_wrong_assignee_tickets(tickets_core)

        if core_alerts:
            logging.info("%s alerte (IT Core - persoane nepermise)", len(core_alerts))
            await send_alerts(core_alerts, title="ALERTA IT Core")
        else:
            logging.info("IT Core: nicio alerta necesara")

        # IT Departament
        if CRM_URL_GROUP3:
            tickets_dep = await get_tickets(CRM_URL_GROUP3)
            dep_alerts = check_group3_presence_tickets(tickets_dep)

            if dep_alerts:
                logging.info(
                    "%s alerte (IT Departament - whitelist + IT Dispacher)",
                    len(dep_alerts),
                )
                await send_alerts(dep_alerts, title="ALERTA IT Departament")
            else:
                logging.info("IT Departament: nicio potrivire")
        else:
            logging.info("CRM_URL_GROUP3 lipseste in .env")

        # Retail & Warehouse (aceeasi logica precum IT Departament)
        if CRM_URL_RETAIL_WAREHOUSE:
            tickets_retail = await get_tickets(CRM_URL_RETAIL_WAREHOUSE)
            retail_alerts = check_group3_presence_tickets(tickets_retail)

            if retail_alerts:
                logging.info(
                    "%s alerte (Retail & Warehouse - whitelist + IT Dispacher)",
                    len(retail_alerts),
                )
                await send_alerts(retail_alerts, title="ALERTA Retail & Warehouse")
            else:
                logging.info("Retail & Warehouse: nicio potrivire")
        else:
            logging.info("CRM_URL_RETAIL_WAREHOUSE lipseste in .env")

    except Exception as e:
        logging.error("Eroare la job: %s", e, exc_info=True)


async def main() -> None:
    setup_logging()
    init_db()
    destinations = get_telegram_destinations()

    logging.info("========================================================")
    logging.info("  CRM alerts bot — pornire")
    logging.info("========================================================")
    logging.info("Destinatii Telegram active: %s", len(destinations))
    for dest in destinations:
        if dest["thread_id"] is None:
            logging.info(" - chat_id=%s (main chat)", dest["chat_id"])
        else:
            logging.info(
                " - chat_id=%s, message_thread_id=%s",
                dest["chat_id"],
                dest["thread_id"],
            )

    scheduler = AsyncIOScheduler(job_defaults={"coalesce": True, "max_instances": 1})
    scheduler.add_job(job, "interval", minutes=CHECK_INTERVAL_MINUTES)
    scheduler.start()

    logging.info(
        "Bot pornit. Verificare la fiecare %s minute. (Ctrl+C opreste procesul.)",
        CHECK_INTERVAL_MINUTES,
    )

    # Ruleaza imediat la start
    await job()

    # Bug fix #5: Ctrl+C curat, fara stack trace si fara scheduler warnings.
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logging.info("Bot oprit.")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass