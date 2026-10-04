"""Run Alembic migrations when enabled for this container process."""

from collections.abc import Callable
from pathlib import Path

import structlog
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)
ALEMBIC_CONFIG_PATH = Path("alembic.ini")
MigrationRunner = Callable[[Config, str], None]


def run_configured_migrations(
    settings: Settings,
    *,
    config_path: Path = ALEMBIC_CONFIG_PATH,
    migration_runner: MigrationRunner = alembic_upgrade,
) -> bool:
    """Upgrade to the latest revision only when this process owns migrations."""
    if not settings.run_migrations:
        logger.info("database_migrations_skipped")
        return False
    migration_runner(Config(str(config_path)), "head")
    logger.info("database_migrations_applied")
    return True


def main() -> None:
    """Apply the configured container migration policy."""
    settings = get_settings()
    configure_logging(settings.log_level)
    run_configured_migrations(settings)


if __name__ == "__main__":
    main()
