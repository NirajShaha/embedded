ALTER TABLE `project_test_case_overrides`
    ADD COLUMN `category_id` BIGINT NULL,
    ADD COLUMN `objective_id` BIGINT NULL,
    ADD COLUMN `protocol_id` BIGINT NULL,
    ADD COLUMN `attack_vector_id` BIGINT NULL,
    ADD COLUMN `test_type_id` BIGINT NULL,
    ADD COLUMN `severity_id` BIGINT NULL,
    ADD COLUMN `threat_id` BIGINT NULL;