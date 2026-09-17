-- AlterTable
ALTER TABLE `test_cases` ADD COLUMN `deleted_at` TIMESTAMP(0) NULL;

-- CreateIndex
CREATE INDEX `ix_test_cases_deleted_at` ON `test_cases`(`deleted_at`);
