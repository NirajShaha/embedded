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
-- Table structure for table `references_master`
--

DROP TABLE IF EXISTS `references_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `references_master` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ref_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ref` (`ref_text`(255))
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `references_master`
--

LOCK TABLES `references_master` WRITE;
/*!40000 ALTER TABLE `references_master` DISABLE KEYS */;
INSERT INTO `references_master` VALUES (1,'Generic ECU penetration-testing library'),(2,'ISO/SAE 21434'),(3,'applicable OEM ECU specification'),(4,'connector drawing'),(5,'wiring diagram'),(6,'and interface-control document.'),(7,'applicable ECU hardware specification'),(8,'component manufacturer datasheets'),(9,'OEM hardware documentation.'),(10,'NIST SP 800-193'),(11,'MCU datasheets and debug-interface reference manuals.'),(12,'MCU memory-protection documentation.'),(13,'MCU debug and memory-protection documentation.'),(14,'MCU vendor security documentation.'),(15,'MCU vendor security documentation'),(16,'OEM firmware-protection requirements.'),(17,'UART interface documentation'),(18,'applicable MCU reference manuals.'),(19,'applicable MCU documentation'),(20,'OEM hardware security requirements.'),(21,'OEM firmware-protection requirements'),(22,'MCU bootloader documentation.'),(23,'OEM security requirements'),(24,'embedded-system hardening guidance.'),(25,'applicable SPI memory datasheet'),(26,'MCU and SoC reference manual'),(27,'applicable SPI peripheral and memory datasheets'),(28,'MCU/SoC reference manual'),(29,'OEM hardware-security requirements.'),(30,'applicable SPI flash datasheet'),(31,'MCU/SoC secure-boot documentation'),(32,'OEM firmware-integrity and hardware-security requirements.'),(33,'CCP 2.1 Specification'),(34,'ASAM XCP Standard'),(35,'UNECE R155 Annex 5.'),(36,'CCP Specification'),(37,'ISO/SAE 21434.'),(38,'OEM HSM architecture specification.'),(39,'UNECE R155 Annex 5'),(40,'applicable OEM calibration and measurement specification.'),(41,'applicable OEM calibration-management specification'),(42,'OEM DXCPL specification'),(43,'OEM UCB configuration documentation'),(44,'applicable ECU security architecture requirements.'),(45,'ECU security architecture requirements.'),(46,'applicable protocol and diagnostic specification'),(47,'applicable protocol and diagnostic specification.'),(48,'ISO 14229'),(49,'applicable ODX/PDX and diagnostic specification.'),(50,'applicable diagnostic and safety specification.'),(51,'applicable diagnostic specification.'),(52,'applicable Security Access specification.'),(53,'ISO 15765-2 where UDS over CAN/CAN-FD is applicable'),(54,'applicable network and diagnostic specification.'),(55,'applicable communication and diagnostic specification.'),(56,'applicable diagnostic and transport specification.'),(57,'applicable routine'),(58,'diagnostic'),(59,'and recovery specification.'),(60,'applicable DTC and diagnostic specification.'),(61,'ISO 15765-2'),(62,'ISO 14229 where applicable'),(63,'ISO 17987-2 and ISO 17987-3'),(64,'LIN 2.2A'),(65,'applicable LDF/NCF and diagnostic specification.'),(66,'ISO 10681-1 and ISO 10681-2'),(67,'ISO 17458-1 and ISO 17458-2'),(68,'applicable FIBEX/ARXML and diagnostic specification.'),(69,'ISO 13400-2'),(70,'IEEE 802.3'),(71,'applicable network architecture'),(72,'firewall'),(73,'ODX/PDX'),(74,'and diagnostic specification.'),(75,'ISO 11898'),(76,'applicable vehicle communication specification.'),(77,'AUTOSAR Secure Onboard Communication (SecOC) Specification'),(78,'applicable OEM cybersecurity specification.'),(79,'ISO 11898-1'),(80,'applicable AUTOSAR and OEM vehicle communication specification.'),(81,'ISO 17987-2'),(82,'ISO 17987-3'),(83,'applicable LDF/NCF and ECU communication specification.'),(84,'ISO 10681-1'),(85,'ISO 10681-2'),(86,'ISO 17458-1'),(87,'ISO 17458-2'),(88,'applicable FIBEX/ARXML and ECU communication specification.'),(89,'applicable network architecture and diagnostic specification.'),(90,'applicable software download specification.'),(91,'applicable configuration management specification.'),(92,'ISO 17987'),(93,'applicable LIN and OEM software-download specification.'),(94,'FlexRay Protocol Specification'),(95,'AUTOSAR FlexRay ISO Transport Layer'),(96,'OEM FlexRay software-download specification.'),(97,'AUTOSAR Diagnostic over IP'),(98,'OEM Ethernet/DoIP software-download specification.'),(99,'OEM Secure Boot specification.'),(100,'OEM Secure Boot requirements.'),(101,'OEM rollback-protection requirements.'),(102,'Secure Boot architecture requirements'),(103,'OEM bootloader security specification.');
/*!40000 ALTER TABLE `references_master` ENABLE KEYS */;
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

-- Dump completed on 2026-10-27 17:39:14
