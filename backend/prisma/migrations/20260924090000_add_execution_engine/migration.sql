-- Execution engine tables.
--
-- Design notes:
-- * test_runs is the resumable unit of work. A run stuck in `running` after a
--   backend restart is recovered to `paused` at boot (see recover_incomplete_runs)
--   so the UI can resume from the next uncompleted case.
-- * test_run_cases carries a resume cursor: (status, attempt, packets_sent).
--   A retried case increments `attempt` and streams a fresh deterministic
--   packet sequence; attempts are never mixed.
-- * test_packets stores every transmitted frame so charts and the report page
--   always render true execution data. For 4-5h production scripts, add a
--   retention job or downsample old partitions; the per-second
--   test_case_buckets rollup already covers long-term trends.
-- * test_run_events is the append-only audit log backing the report timeline.

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `test_run_events` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `run_id` BIGINT NOT NULL,
    `event_type` VARCHAR(40) NOT NULL,
    `payload` JSON NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    KEY `ix_run_events_run_id` (`run_id`),
    CONSTRAINT `fk_run_events_run` FOREIGN KEY (`run_id`)
        REFERENCES `test_runs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
