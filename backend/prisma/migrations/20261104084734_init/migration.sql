-- DropForeignKey
ALTER TABLE `test_case_buckets` DROP FOREIGN KEY `fk_buckets_case`;

-- DropForeignKey
ALTER TABLE `test_case_buckets` DROP FOREIGN KEY `fk_buckets_run`;

-- DropForeignKey
ALTER TABLE `test_packets` DROP FOREIGN KEY `fk_packets_case`;

-- DropForeignKey
ALTER TABLE `test_packets` DROP FOREIGN KEY `fk_packets_run`;

-- DropForeignKey
ALTER TABLE `test_run_cases` DROP FOREIGN KEY `fk_run_cases_case`;

-- DropForeignKey
ALTER TABLE `test_run_cases` DROP FOREIGN KEY `fk_run_cases_run`;

-- DropForeignKey
ALTER TABLE `test_run_events` DROP FOREIGN KEY `fk_run_events_run`;

-- DropForeignKey
ALTER TABLE `test_runs` DROP FOREIGN KEY `fk_test_runs_project`;

-- AddForeignKey
ALTER TABLE `test_runs` ADD CONSTRAINT `test_runs_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_run_cases` ADD CONSTRAINT `test_run_cases_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `test_runs`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_run_cases` ADD CONSTRAINT `test_run_cases_ibfk_2` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_packets` ADD CONSTRAINT `test_packets_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `test_runs`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_packets` ADD CONSTRAINT `test_packets_ibfk_2` FOREIGN KEY (`case_id`) REFERENCES `test_run_cases`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_buckets` ADD CONSTRAINT `test_case_buckets_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `test_runs`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_buckets` ADD CONSTRAINT `test_case_buckets_ibfk_2` FOREIGN KEY (`case_id`) REFERENCES `test_run_cases`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_run_events` ADD CONSTRAINT `test_run_events_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `test_runs`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;
