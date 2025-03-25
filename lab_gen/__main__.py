import uvicorn

from lab_gen.settings import settings


def main() -> None:
    """Entrypoint of the application."""
    uvicorn.run(
        "lab_gen.web.application:get_app",
        workers=settings.workers_count,
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
