-- CreateTable
CREATE TABLE `assets` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `asset_name` VARCHAR(500) NOT NULL,

    UNIQUE INDEX `asset_name`(`asset_name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `attack_vectors` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,

    UNIQUE INDEX `name`(`name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `attribute_groups` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `page` INTEGER NOT NULL,
    `name` VARCHAR(200) NOT NULL,

    INDEX `ix_attribute_groups_page`(`page`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `attributes` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `group_id` INTEGER NOT NULL,
    `name` VARCHAR(200) NOT NULL,

    INDEX `group_id`(`group_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `categories` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    UNIQUE INDEX `name`(`name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `objectives` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `category_id` BIGINT NOT NULL,
    `name` TEXT NOT NULL,

    UNIQUE INDEX `uk_obj`(`category_id`, `name`(255)),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `project_ecu_details` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `project_id` INTEGER NOT NULL,
    `ecu_name` VARCHAR(255) NOT NULL,
    `part_number` VARCHAR(255) NOT NULL,
    `ecu_risk_rating` VARCHAR(100) NOT NULL,
    `architecture` VARCHAR(255) NOT NULL,
    `vehicle_line` VARCHAR(255) NOT NULL,
    `year` INTEGER NOT NULL,
    `microcontroller_cpu_provider` VARCHAR(255) NOT NULL,
    `date_hardware_b_sample_available` DATE NULL,
    `date_harness_available` DATE NULL,
    `date_production_intent_software_available` DATE NULL,
    `export_control_classification` VARCHAR(255) NOT NULL,
    `pentest_provider_name` VARCHAR(255) NOT NULL,
    `created_at` DATETIME(0) NOT NULL DEFAULT (now()),
    `updated_at` DATETIME(0) NOT NULL DEFAULT (now()),

    UNIQUE INDEX `ix_project_ecu_details_project_id`(`project_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `project_selections` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `project_id` INTEGER NOT NULL,
    `attribute_id` INTEGER NOT NULL,
    `page` INTEGER NOT NULL,

    INDEX `ix_project_selections_attribute_id`(`attribute_id`),
    INDEX `ix_project_selections_page`(`page`),
    INDEX `ix_project_selections_project_id`(`project_id`),
    UNIQUE INDEX `uq_project_attribute`(`project_id`, `attribute_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `projects` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT NULL,
    `created_at` DATETIME(0) NOT NULL DEFAULT (now()),

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `protocols` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,

    UNIQUE INDEX `name`(`name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `references_master` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `ref_text` TEXT NOT NULL,

    UNIQUE INDEX `uk_ref`(`ref_text`(255)),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `severities` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    `severity_rank` INTEGER NOT NULL,

    UNIQUE INDEX `name`(`name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `test_case_references` (
    `test_case_id` BIGINT NOT NULL,
    `reference_id` BIGINT NOT NULL,

    INDEX `reference_id`(`reference_id`),
    PRIMARY KEY (`test_case_id`, `reference_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `test_case_tools` (
    `test_case_id` BIGINT NOT NULL,
    `tool_id` BIGINT NOT NULL,

    INDEX `tool_id`(`tool_id`),
    PRIMARY KEY (`test_case_id`, `tool_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `test_cases` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `category_id` BIGINT NOT NULL,
    `objective_id` BIGINT NOT NULL,
    `protocol_id` BIGINT NULL,
    `attack_vector_id` BIGINT NULL,
    `test_type_id` BIGINT NULL,
    `severity_id` BIGINT NULL,
    `threat_id` BIGINT NULL,
    `asset_id` BIGINT NULL,
    `action_test_case` LONGTEXT NOT NULL,
    `source_scope_status` VARCHAR(100) NULL,
    `description` LONGTEXT NULL,
    `attack_path` LONGTEXT NULL,
    `test_steps` LONGTEXT NULL,
    `expected_output` LONGTEXT NULL,
    `attack_feasibility` TEXT NULL,
    `cia_impact` TEXT NULL,
    `safety_impact` TEXT NULL,
    `automation_possible` VARCHAR(50) NULL,
    `created_at` TIMESTAMP(0) NULL DEFAULT CURRENT_TIMESTAMP(0),

    INDEX `asset_id`(`asset_id`),
    INDEX `attack_vector_id`(`attack_vector_id`),
    INDEX `category_id`(`category_id`),
    INDEX `objective_id`(`objective_id`),
    INDEX `protocol_id`(`protocol_id`),
    INDEX `severity_id`(`severity_id`),
    INDEX `test_type_id`(`test_type_id`),
    INDEX `threat_id`(`threat_id`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `test_types` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,

    UNIQUE INDEX `name`(`name`),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `threats` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `threat_text` TEXT NOT NULL,

    UNIQUE INDEX `uk_threat`(`threat_text`(255)),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `tools_master` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `tool_name` VARCHAR(1000) NOT NULL,

    UNIQUE INDEX `uk_tool`(`tool_name`(255)),
    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- AddForeignKey
ALTER TABLE `attributes` ADD CONSTRAINT `attributes_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `attribute_groups`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `objectives` ADD CONSTRAINT `objectives_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_ecu_details` ADD CONSTRAINT `project_ecu_details_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_selections` ADD CONSTRAINT `project_selections_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `project_selections` ADD CONSTRAINT `project_selections_ibfk_2` FOREIGN KEY (`attribute_id`) REFERENCES `attributes`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_references` ADD CONSTRAINT `test_case_references_ibfk_1` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_references` ADD CONSTRAINT `test_case_references_ibfk_2` FOREIGN KEY (`reference_id`) REFERENCES `references_master`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_tools` ADD CONSTRAINT `test_case_tools_ibfk_1` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_case_tools` ADD CONSTRAINT `test_case_tools_ibfk_2` FOREIGN KEY (`tool_id`) REFERENCES `tools_master`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_2` FOREIGN KEY (`objective_id`) REFERENCES `objectives`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_3` FOREIGN KEY (`protocol_id`) REFERENCES `protocols`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_4` FOREIGN KEY (`attack_vector_id`) REFERENCES `attack_vectors`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_5` FOREIGN KEY (`test_type_id`) REFERENCES `test_types`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_6` FOREIGN KEY (`severity_id`) REFERENCES `severities`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_7` FOREIGN KEY (`threat_id`) REFERENCES `threats`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE `test_cases` ADD CONSTRAINT `test_cases_ibfk_8` FOREIGN KEY (`asset_id`) REFERENCES `assets`(`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;
