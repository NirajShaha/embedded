-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: embedded_db
-- ------------------------------------------------------
-- Server version	9.5.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '999e4fe4-6bd8-11f1-9caa-c85acfbd4c6d:1-81172';

--
-- Table structure for table `_prisma_migrations`
--

DROP TABLE IF EXISTS `_prisma_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `_prisma_migrations` (
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `checksum` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `finished_at` datetime(3) DEFAULT NULL,
  `migration_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `logs` text COLLATE utf8mb4_unicode_ci,
  `rolled_back_at` datetime(3) DEFAULT NULL,
  `started_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `applied_steps_count` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `_prisma_migrations`
--

LOCK TABLES `_prisma_migrations` WRITE;
/*!40000 ALTER TABLE `_prisma_migrations` DISABLE KEYS */;
INSERT INTO `_prisma_migrations` VALUES ('0715a46d-59e5-4da9-8994-9f48c3d2140b','d0c499f5c154c43ef40458ada384d6b96b8d36c7ed744fa91ecbf3821d0ecc91','2026-09-22 10:21:11.789','20260922150000_remove_assets_and_automation',NULL,NULL,'2026-09-22 10:21:11.497',1),('232e43d2-e40a-46ab-9e74-ddcbd8f02733','c59180b7f8d3f68bd98ea0d1a0f2311a5b1aea2f09b424fdd7dda7b7e7f3df2c','2026-09-22 14:05:21.932','20260922160000_add_classification_overrides',NULL,NULL,'2026-09-22 14:05:21.904',1),('2d8f3113-e3f1-4e41-bfde-d55a8adef0ff','97ade63a9242219c58cb4bb47e58193c39a3ab55e6fb56517254df3235fd242a','2026-09-17 09:32:36.511','20260907092929_init',NULL,NULL,'2026-09-17 09:32:35.217',1),('30636140-9d39-4e1a-8611-5c1f0a0f86f1','7da4bb4d1a8e0cb30953ec3ea04e23c02f71bd7b7fda1d03d1c84563f52091d7','2026-09-17 09:32:36.893','20260907120838_add_users_and_audit_columns',NULL,NULL,'2026-09-17 09:32:36.514',1),('4284cbc2-6abe-4076-8fbd-4d66cb375a29','0e7a7e30c53e05fede4d1da5ad58d0f92607032caf029db698ae07fa1ab0eed1','2026-09-23 11:14:38.186','20260923090000_remove_classification_overrides',NULL,NULL,'2026-09-23 11:14:38.151',1),('75f6d115-0a1c-4d08-80b3-d32a2013872c','29d5f1ef1db24e7f0cb9aaee37856de4ae5fe16a85842a2983f20f174b6d888f','2026-09-22 09:43:51.772','20260922130000_add_version_2_override_fields',NULL,NULL,'2026-09-22 09:43:51.746',1),('7898373b-e52a-4acd-b682-1a939d1d871b','28dd9c86bfbc7edfeca534111c06def128468a019115eac2b9632cd8999592d7',NULL,'20260924090000_add_execution_engine','A migration failed to apply. New migrations cannot be applied before the error is recovered from. Read more about how to resolve migration issues in a production database: https://pris.ly/d/migrate-resolve\n\nMigration name: 20260924090000_add_execution_engine\n\nDatabase error code: 1064\n\nDatabase error:\nYou have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near \'UTC_TIMESTAMP(6),\n    `updated_at` DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6)\' at line 30\n\nPlease check the query number 1 from the migration file.\n\n   0: sql_schema_connector::apply_migration::apply_script\n           with migration_name=\"20260924090000_add_execution_engine\"\n             at schema-engine\\connectors\\sql-schema-connector\\src\\apply_migration.rs:106\n   1: schema_core::commands::apply_migrations::Applying migration\n           with migration_name=\"20260924090000_add_execution_engine\"\n             at schema-engine\\core\\src\\commands\\apply_migrations.rs:91\n   2: schema_core::state::ApplyMigrations\n             at schema-engine\\core\\src\\state.rs:226','2026-09-24 15:04:23.658','2026-09-24 15:03:38.018',0),('9a4a29a0-a486-4cc7-aa7d-d14b4d63f50d','2d86b2f115384c17b815d97d6cb4da0d67ba38dcdc5a9405a9c7847c92fa68fc','2026-09-22 09:46:14.906','20260922140000_expand_severity_name',NULL,NULL,'2026-09-22 09:46:14.847',1),('a7f1144b-3800-4067-a6ce-5d53deb36055','b211ba7eed861be6fa1fd6046693f82da15ed029aef30567036d09718db37f67','2026-09-22 09:33:58.218','20260922120000_add_version_2_test_case_fields',NULL,NULL,'2026-09-22 09:33:58.171',1),('a8d26605-5652-4389-84ba-92c04891a789','4f0079b4cbf3942e0caa3de4dfbf3a5ea6f495eea218b5654a9b34625f1d2271','2026-09-17 09:32:36.998','20260908115216_add_test_case_soft_delete',NULL,NULL,'2026-09-17 09:32:36.896',1),('cdb75f4e-5f75-4232-8131-3895735e78ef','37a75e966e009155e8fa1b77a449d5a76c9f6b3be195dfe9bbc15b6d3591e626','2026-09-24 15:04:26.908','20260924090000_add_execution_engine',NULL,NULL,'2026-09-24 15:04:26.783',1),('d143b7eb-ecdc-4e7b-b534-9cfce1d1cd09','dfdd2e09a79a5f9b7778dfa3d52fcace564f0b2d246f1db167d2c283c0ab4bec','2026-09-17 09:32:46.891','20260917093246_add_users',NULL,NULL,'2026-09-17 09:32:46.542',1);
/*!40000 ALTER TABLE `_prisma_migrations` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-27 17:39:17
