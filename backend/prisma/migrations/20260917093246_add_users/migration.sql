-- CreateTable
CREATE TABLE `project_test_case_overrides` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `project_id` INTEGER NOT NULL,
    `test_case_id` BIGINT NOT NULL,
    `action_test_case` LONGTEXT NULL,
    `source_scope_status` VARCHAR(100) NULL,
    `description` LONGTEXT NULL,
    `attack_path` LONGTEXT NULL,
    `test_steps` LONGTEXT NULL,
    `expected_output` LONGTEXT NULL,
    `attack_feasibility` TEXT NULL,
    `cia_impact` TEXT NULL,
    `safety_impact` TEXT NULL,
    `automation_possible` VARCHAR(50) NULL,
    `tools_overridden` BOOLEAN NOT NULL DEFAULT false,
    `references_overridden` BOOLEAN NOT NULL DEFAULT false,
    `created_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    `updated_at` TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP(0),

    INDEX `ix_ptco_project_id`(`project_id`),
    INDEX `ix_ptco_test_case_id`(`test_case_id`),
    UNIQUE INDEX `uq_project_test_case`(`project_id`, `test_case_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `project_test_case_override_tools` (
    `override_id` INTEGER NOT NULL,
    `tool_id` BIGINT NOT NULL,

    INDEX `ix_ptcot_tool_id`(`tool_id`),
    PRIMARY KEY (`override_id`, `tool_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `project_test_case_override_references` (
    `override_id` INTEGER NOT NULL,
    `reference_id` BIGINT NOT NULL,

    INDEX `ix_ptcor_reference_id`(`reference_id`),
    PRIMARY KEY (`override_id`, `reference_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `project_test_case_overrides` ADD CONSTRAINT `ptco_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_test_case_overrides` ADD CONSTRAINT `ptco_ibfk_2` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_test_case_override_tools` ADD CONSTRAINT `ptcot_ibfk_1` FOREIGN KEY (`override_id`) REFERENCES `project_test_case_overrides`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_test_case_override_tools` ADD CONSTRAINT `ptcot_ibfk_2` FOREIGN KEY (`tool_id`) REFERENCES `tools_master`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_test_case_override_references` ADD CONSTRAINT `ptcor_ibfk_1` FOREIGN KEY (`override_id`) REFERENCES `project_test_case_overrides`(`id`) ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_test_case_override_references` ADD CONSTRAINT `ptcor_ibfk_2` FOREIGN KEY (`reference_id`) REFERENCES `references_master`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
