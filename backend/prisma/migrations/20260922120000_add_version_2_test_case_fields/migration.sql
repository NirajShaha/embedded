-- Add fields introduced by Pentesting_DataBase_Version_2.xlsx.
ALTER TABLE `test_cases`
    ADD COLUMN `test_case_name` VARCHAR(255) NULL,
    ADD COLUMN `pre_condition` LONGTEXT NULL,
    ADD COLUMN `impact` LONGTEXT NULL;