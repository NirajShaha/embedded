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
-- Table structure for table `objectives`
--

DROP TABLE IF EXISTS `objectives`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `objectives` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `category_id` bigint NOT NULL,
  `name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_obj` (`category_id`,`name`(255)),
  CONSTRAINT `objectives_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `objectives`
--

LOCK TABLES `objectives` WRITE;
/*!40000 ALTER TABLE `objectives` DISABLE KEYS */;
INSERT INTO `objectives` VALUES (2,2,'Study the System and Prepare a Working Setup on the Bench'),(3,3,'Investigate the hardware components'),(4,4,'Assess JTAG Security'),(5,5,'Assess UART Security'),(6,6,'Assess SPI Security'),(7,7,'AssessCCP/XCP Security'),(8,8,'Assess DXCPL Security'),(9,9,'Assess UDS security'),(10,9,'Assess ECU Availability and Resilience'),(11,9,'Assess Input Validation and Robustness'),(12,10,'Assess UDS security'),(13,10,'Assess ECU Availability and Resilience'),(14,10,'Assess Input Validation and Robustness'),(15,10,'Assess Information Disclosure'),(16,11,'Assess UDS security'),(17,11,'Assess ECU Availability and Resilience'),(18,11,'Assess Input Validation and Robustness'),(19,12,'Assess UDS security'),(20,12,'Assess ECU Availability and Resilience'),(21,12,'Assess Input Validation and Robustness'),(22,12,'Assess Information Disclosure'),(23,13,'Assess CAN Security'),(24,14,'Assess LIN Security'),(25,15,'Assess FlexRay Security'),(26,16,'Assess Ethernet/DoIP Security'),(27,17,'Assess Authentication Mechanisms for Secure Download'),(28,17,'Assess Confidentiality Mechanisms for Secure Download'),(29,17,'Assess Software Download Authorization Controls'),(30,17,'Assess Software Download Availability and Resilience'),(31,17,'Assess Arbitrary Code Execution Protections'),(32,17,'Assess Downloadable Configuration File Security'),(33,17,'Assess CAN-Based Software Transfer Security'),(34,18,'Assess Authentication Mechanisms for Secure Download'),(35,18,'Assess Confidentiality Mechanisms for Secure Download'),(36,18,'Assess Software Download Authorization Controls'),(37,18,'Assess Software Download Availability and Resilience'),(38,18,'Assess Arbitrary Code Execution Protections'),(39,18,'Assess Downloadable Configuration File Security'),(40,18,'Assess LIN-Based Software Transfer Security'),(41,19,'Assess Authentication Mechanisms for Secure Download'),(42,19,'Assess Confidentiality Mechanisms for Secure Download'),(43,19,'Assess Software Download Authorization Controls'),(44,19,'Assess Software Download Availability and Resilience'),(45,19,'Assess Arbitrary Code Execution Protections'),(46,19,'Assess Downloadable Configuration File Security'),(47,19,'Assess FlexRay-Based Software Transfer Security'),(48,20,'Assess Authentication Mechanisms for Secure Download'),(49,20,'Assess Confidentiality Mechanisms for Secure Download'),(50,20,'Assess Software Download Authorization Controls'),(51,20,'Assess Software Download Availability and Resilience'),(52,20,'Assess Arbitrary Code Execution Protections'),(53,20,'Assess Downloadable Configuration File Security'),(54,20,'Assess Ethernet-Based Software Transfer Security'),(55,21,'Assess Secure Boot Security');
/*!40000 ALTER TABLE `objectives` ENABLE KEYS */;
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
