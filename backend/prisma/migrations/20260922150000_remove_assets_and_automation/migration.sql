ALTER TABLE `test_cases`
    DROP FOREIGN KEY `test_cases_ibfk_8`,
    DROP COLUMN `asset_id`,
    DROP COLUMN `automation_possible`;

ALTER TABLE `project_test_case_overrides`
    DROP COLUMN `automation_possible`;

DROP TABLE `assets`;