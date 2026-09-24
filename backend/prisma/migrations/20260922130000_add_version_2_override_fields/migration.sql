-- Allow Version 2 fields to be overridden per project without changing the master catalogue.
ALTER TABLE `project_test_case_overrides`
    ADD COLUMN `test_case_name` VARCHAR(255) NULL,
    ADD COLUMN `pre_condition` LONGTEXT NULL,
    ADD COLUMN `impact` LONGTEXT NULL;