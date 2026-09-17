-- AlterTable
ALTER TABLE `test_cases` ADD COLUMN `created_by` BIGINT NULL,
    ADD COLUMN `deleted_by` BIGINT NULL,
    ADD COLUMN `updated_at` TIMESTAMP(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
    ADD COLUMN `updated_by` BIGINT NULL;

-- CreateTable
CREATE TABLE `users` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `role` VARCHAR(50) NOT NULL DEFAULT 'USER',
    `created_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    `updated_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),

    UNIQUE INDEX `uk_username`(`username`),
    INDEX `ix_users_username`(`username`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateIndex
CREATE INDEX `ix_test_cases_created_by` ON `test_cases`(`created_by`);

-- CreateIndex
CREATE INDEX `ix_test_cases_updated_by` ON `test_cases`(`updated_by`);

-- CreateIndex
CREATE INDEX `ix_test_cases_deleted_by` ON `test_cases`(`deleted_by`);

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_created_by` FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_deleted_by` FOREIGN KEY (`deleted_by`) REFERENCES `users`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
