"""Idempotent creation of the execution-engine tables.

A fresh database created with ``prisma migrate deploy`` already has these
tables. But because this project can also be bootstrapped in other ways
(SQLAlchemy models, a hand-created schema), the script-run and simulated
execution features can't assume the tables exist. Calling
:func:`ensure_execution_tables` on startup guarantees they do, regardless of
how the database was provisioned. Every statement is ``CREATE TABLE IF NOT
EXISTS`` so it is safe to run on every boot and never touches existing data.

The DDL here must stay in sync with
``prisma/migrations/20260924090000_add_execution_engine/migration.sql``.
"""

from __future__ import annotations

from app.prisma_client import db


_DDL: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS `test_runs` (
        `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
        `project_id` INT NOT NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'running',
        `total_cases` INT NOT NULL,
        `completed_cases` INT NOT NULL DEFAULT 0,
        `passed_cases` INT NOT NULL DEFAULT 0,
        `failed_cases` INT NOT NULL DEFAULT 0,
        `current_position` INT NULL,
        `duration_per_case_s` DOUBLE NOT NULL DEFAULT 90,
        `packet_loss_rate` DOUBLE NOT NULL DEFAULT 0.02,
        `started_at` DATETIME(6) NULL,
        `finished_at` DATETIME(6) NULL,
        `created_by` BIGINT NULL,
        `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        KEY `ix_test_runs_project_id` (`project_id`),
        KEY `ix_test_runs_status` (`status`),
        CONSTRAINT `fk_test_runs_project` FOREIGN KEY (`project_id`)
            REFERENCES `projects` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `test_run_cases` (
        `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
        `run_id` BIGINT NOT NULL,
        `position` INT NOT NULL,
        `test_case_id` BIGINT NOT NULL,
        `test_case_name` TEXT NULL,
        `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
        `attempt` INT NOT NULL DEFAULT 0,
        `packets_planned` INT NOT NULL DEFAULT 0,
        `packets_sent` INT NOT NULL DEFAULT 0,
        `packets_acked` INT NOT NULL DEFAULT 0,
        `packets_nacked` INT NOT NULL DEFAULT 0,
        `avg_rtt_ms` DOUBLE NULL,
        `started_at` DATETIME(6) NULL,
        `finished_at` DATETIME(6) NULL,
        `duration_ms` BIGINT NULL,
        `error` TEXT NULL,
        `fault_start_seq` INT NULL,
        `fault_end_seq` INT NULL,
        UNIQUE KEY `uq_run_position` (`run_id`, `position`),
        KEY `ix_run_cases_run_id` (`run_id`),
        KEY `ix_run_cases_status` (`run_id`, `status`),
        CONSTRAINT `fk_run_cases_run` FOREIGN KEY (`run_id`)
            REFERENCES `test_runs` (`id`) ON DELETE CASCADE,
        CONSTRAINT `fk_run_cases_case` FOREIGN KEY (`test_case_id`)
            REFERENCES `test_cases` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `test_packets` (
        `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
        `run_id` BIGINT NOT NULL,
        `case_id` BIGINT NOT NULL,
        `seq` INT NOT NULL,
        `seq_global` BIGINT NOT NULL,
        `payload_hex` VARCHAR(64) NOT NULL,
        `ack` TINYINT(1) NOT NULL DEFAULT 1,
        `rtt_ms` DOUBLE NOT NULL DEFAULT 0,
        `sent_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        KEY `ix_packets_run_seq` (`run_id`, `seq_global`),
        KEY `ix_packets_case` (`case_id`, `seq`),
        CONSTRAINT `fk_packets_run` FOREIGN KEY (`run_id`)
            REFERENCES `test_runs` (`id`) ON DELETE CASCADE,
        CONSTRAINT `fk_packets_case` FOREIGN KEY (`case_id`)
            REFERENCES `test_run_cases` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `test_case_buckets` (
        `run_id` BIGINT NOT NULL,
        `case_id` BIGINT NOT NULL,
        `bucket_index` INT NOT NULL,
        `packets` INT NOT NULL DEFAULT 0,
        `acked` INT NOT NULL DEFAULT 0,
        `nacked` INT NOT NULL DEFAULT 0,
        `avg_rtt_ms` DOUBLE NULL,
        PRIMARY KEY (`run_id`, `case_id`, `bucket_index`),
        CONSTRAINT `fk_buckets_run` FOREIGN KEY (`run_id`)
            REFERENCES `test_runs` (`id`) ON DELETE CASCADE,
        CONSTRAINT `fk_buckets_case` FOREIGN KEY (`case_id`)
            REFERENCES `test_run_cases` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS `test_run_events` (
        `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
        `run_id` BIGINT NOT NULL,
        `event_type` VARCHAR(40) NOT NULL,
        `payload` JSON NULL,
        `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        KEY `ix_run_events_run_id` (`run_id`),
        CONSTRAINT `fk_run_events_run` FOREIGN KEY (`run_id`)
            REFERENCES `test_runs` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


async def ensure_execution_tables() -> None:
    """Create the execution-engine tables if they are missing. Idempotent."""
    for statement in _DDL:
        await db.execute_raw(statement)
