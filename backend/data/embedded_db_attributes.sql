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
-- Table structure for table `attributes`
--

DROP TABLE IF EXISTS `attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attributes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `attributes_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `attribute_groups` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attributes`
--

LOCK TABLES `attributes` WRITE;
/*!40000 ALTER TABLE `attributes` DISABLE KEYS */;
INSERT INTO `attributes` VALUES (1,1,'Tracking'),(2,1,'Reporting'),(3,1,'Automation'),(4,1,'Notifications'),(5,2,'REST API'),(6,2,'Webhooks'),(7,2,'Email'),(8,2,'Slack'),(9,3,'Cloud'),(10,3,'On-Premise'),(11,3,'Hybrid'),(12,3,'Edge'),(13,4,'Small'),(14,4,'Medium'),(15,4,'Large'),(16,4,'Enterprise'),(17,5,'SSO'),(18,5,'2FA'),(19,5,'Audit Logs'),(20,5,'Encryption'),(21,6,'Web'),(22,6,'Mobile'),(23,6,'Desktop'),(24,6,'CLI'),(25,7,'English'),(26,7,'Spanish'),(27,7,'French'),(28,7,'German'),(29,8,'Low Latency'),(30,8,'High Throughput'),(31,8,'Reliable'),(32,8,'Efficient'),(33,9,'Batch'),(34,9,'Streaming'),(35,9,'Real-time'),(36,9,'Archival'),(37,10,'Self-service'),(38,10,'Chat'),(39,10,'Phone'),(40,10,'SLA'),(41,11,'PostgreSQL'),(42,11,'Redis'),(43,11,'S3'),(44,11,'Local Disk'),(45,12,'Dashboards'),(46,12,'Custom Queries'),(47,12,'Export'),(48,12,'Forecasts'),(49,13,'Roles'),(50,13,'Permissions'),(51,13,'Teams'),(52,13,'Whitelist'),(53,14,'Email'),(54,14,'Push'),(55,14,'SMS'),(56,14,'In-app'),(57,15,'GDPR'),(58,15,'SOC2'),(59,15,'ISO 27001'),(60,15,'HIPAA'),(61,16,'Sensor'),(62,16,'Controller'),(63,16,'Gateway'),(64,16,'Chip'),(65,17,'MQTT'),(66,17,'Modbus'),(67,17,'HTTP'),(68,17,'BLE'),(69,18,'Battery'),(70,18,'Mains'),(71,18,'Solar'),(72,18,'PoE'),(73,19,'Wi-Fi'),(74,19,'Ethernet'),(75,19,'Cellular'),(76,19,'Zigbee'),(77,20,'Input'),(78,20,'Display'),(79,20,'Actuator'),(80,20,'Communication');
/*!40000 ALTER TABLE `attributes` ENABLE KEYS */;
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
