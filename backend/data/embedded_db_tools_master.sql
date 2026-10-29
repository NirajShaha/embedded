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
-- Table structure for table `tools_master`
--

DROP TABLE IF EXISTS `tools_master`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tools_master` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tool_name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tool` (`tool_name`(255))
) ENGINE=InnoDB AUTO_INCREMENT=242 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_master`
--

LOCK TABLES `tools_master` WRITE;
/*!40000 ALTER TABLE `tools_master` DISABLE KEYS */;
INSERT INTO `tools_master` VALUES (1,'ECU connector documentation'),(2,'wiring diagrams'),(3,'digital multimeter'),(4,'continuity tester'),(5,'regulated power-supply documentation'),(6,'breakout harness'),(7,'connector inspection tools'),(8,'and applicable network database files.'),(9,'Current-limited regulated DC power supply'),(10,'oscilloscope'),(11,'fused power leads'),(12,'relay or ignition-control arrangement'),(13,'termination resistors'),(14,'and connector-adapter hardware.'),(15,'CANoe'),(16,'CANalyzer'),(17,'Vehicle Spy'),(18,'Wireshark'),(19,'SavvyCAN'),(20,'BUSMASTER'),(21,'logic analyser'),(22,'SocketCAN/python-can tools'),(23,'LIN analyser'),(24,'FlexRay interface'),(25,'Automotive Ethernet interface'),(26,'and compatible hardware such as Vector'),(27,'Kvaser'),(28,'PEAK'),(29,'Intrepid'),(30,'or equivalent interfaces.'),(31,'programmable relay or ignition controller'),(32,'diagnostic client'),(33,'protocol-compatible network interface'),(34,'and OEM service tools where available.'),(35,'Magnifying lamp'),(36,'digital microscope'),(37,'PCB inspection tools'),(38,'digital camera'),(39,'multimeter'),(40,'component identification databases'),(41,'manufacturer datasheets'),(42,'hardware teardown tools'),(43,'and OEM hardware documentation.'),(44,'JTAGulator'),(45,'SEGGER J-Link'),(46,'Lauterbach TRACE32'),(47,'DAP MiniWiggler'),(48,'OpenOCD'),(49,'Bus Pirate'),(50,'and PCB inspection tools.'),(51,'memory analysis tools'),(52,'hex editors'),(53,'firmware analysis tools'),(54,'and applicable MCU debug utilities.'),(55,'memory programming utilities'),(56,'and MCU-specific debug tools.'),(57,'glitching tools where authorized'),(58,'and MCU vendor utilities.'),(59,'binary editors'),(60,'reverse-engineering tools'),(61,'and MCU-specific programming utilities.'),(62,'USB-to-UART adapters'),(63,'FTDI adapters'),(64,'CP210x adapters'),(65,'terminal software'),(66,'and serial communication utilities.'),(67,'serial-monitoring tools'),(68,'and console interaction tools.'),(69,'serial-bootloader utilities'),(70,'and OEM programming tools.'),(71,'command-interaction utilities'),(72,'and UART monitoring tools'),(73,'magnifying equipment'),(74,'SOIC test clip'),(75,'SPI probes'),(76,'CH341A programmer'),(77,'Dediprog programmer'),(78,'FlashcatUSB'),(79,'Hydrabus'),(80,'flashrom'),(81,'hex editor'),(82,'Binwalk'),(83,'Ghidra'),(84,'and applicable memory-manufacturer utilities.'),(85,'protocol analyser'),(86,'GreatFET'),(87,'ChipWhisperer or equivalent authorized laboratory platform'),(88,'SPI development board'),(89,'microcontroller-based SPI test interface'),(90,'PCB probes'),(91,'and memory-manufacturer documentation.'),(92,'SPI programmer'),(93,'CH341A'),(94,'Dediprog'),(95,'binary comparison tool'),(96,'ETAS INCA'),(97,'ATI Vision'),(98,'CANape'),(99,'SocketCAN tools'),(100,'XCP diagnostic clients.'),(101,'custom XCP clients.'),(102,'OEM XCP tools'),(103,'CANalyzer.'),(104,'firmware-analysis tools'),(105,'reverse-engineering tools.'),(106,'custom CCP/XCP clients'),(107,'SocketCAN/python-can scripts'),(108,'network monitoring tools'),(109,'and protocol-analysis tools.'),(110,'OEM calibration tools'),(111,'CCP/XCP diagnostic clients'),(112,'and network communication interfaces'),(113,'UDS diagnostic clients'),(114,'OEM service tools'),(115,'and compatible communication hardware such as Vector VN1630A/VN1640A'),(116,'PEAK PCAN'),(117,'or Intrepid ValueCAN.'),(118,'Vector VN1630A/VN1640A'),(119,'Intrepid ValueCAN'),(120,'and equivalent diagnostic communication hardware'),(121,'and equivalent diagnostic communication hardware.'),(122,'SocketCAN/python-can based scripts'),(123,'OEM diagnostic tools'),(124,'aftermarket diagnostic tools'),(125,'UDS scanner/enumeration tools'),(126,'CAN/CAN-FD interface hardware (e.g.'),(127,'Intrepid ValueCAN).'),(128,'Python (python-can'),(129,'udsoncan) scripts'),(130,'CAPL scripts'),(131,'PCAN'),(132,'ValueCAN.'),(133,'UDS scanner tools'),(134,'CAN/CAN-FD interface hardware.'),(135,'and compatible CAN/CAN-FD interface hardware such as Vector VN1630A/VN1640A'),(136,'SocketCAN/python-can and udsoncan scripts'),(137,'ODX/PDX viewers'),(138,'and compatible CAN/CAN-FD interface hardware.'),(139,'measurement equipment'),(140,'UDS clients'),(141,'fault simulation equipment'),(142,'Vector vFlash'),(143,'OEM flashing tools'),(144,'OEM diagnostic or flashing tools'),(145,'programmable power supply'),(146,'debugger or recovery interface where authorized'),(147,'CANoe with CAPL'),(148,'SocketCAN utilities'),(149,'can-utils'),(150,'custom Python scripts using python-can or udsoncan'),(151,'network traffic generators'),(152,'bus-load monitoring tools'),(153,'SocketCAN/can-utils'),(154,'bus monitoring tools'),(155,'multiple CAN/CAN-FD communication interfaces where required'),(156,'traffic generation tools'),(157,'timing analysis tools'),(158,'and compatible interface hardware such as Vector'),(159,'UDS Routine Control clients'),(160,'timing and communication monitoring tools'),(161,'authorized recovery or debugging interface where required'),(162,'fault injection or signal simulation equipment where required'),(163,'SocketCAN/python-can'),(164,'can-isotp scripts'),(165,'CANoe or CANalyzer with LIN option'),(166,'Vehicle Spy with LIN-capable hardware'),(167,'PEAK PLIN-View Pro/PLIN-USB'),(168,'NI-XNET LIN tools'),(169,'custom LIN diagnostic scripts or test modules'),(170,'LDF/NCF viewers where available'),(171,'and compatible LIN interface hardware such as Vector VN1630A/VN1640A'),(172,'PEAK PLIN-USB'),(173,'NI-XNET LIN interfaces'),(174,'or Intrepid LIN-capable hardware.'),(175,'CANoe or CANalyzer with FlexRay option'),(176,'Vehicle Spy with FlexRay-capable hardware'),(177,'FIBEX or AUTOSAR ARXML viewers'),(178,'CAPL or custom FlexRay diagnostic test modules'),(179,'and compatible FlexRay interface hardware such as Vector VN7570/VN7610/VN7640 or Intrepid FlexRay-capable hardware.'),(180,'CANoe or CANalyzer with Ethernet/DoIP option'),(181,'OEM diagnostic and flashing tools'),(182,'Nmap where authorized'),(183,'Scapy'),(184,'python-doipclient or custom DoIP test scripts'),(185,'packet-capture and traffic-generation tools'),(186,'and compatible Automotive Ethernet interfaces such as Vector VN5610A/VN5620/VN5640 or Intrepid Automotive Ethernet hardware.'),(187,'Boofuzz'),(188,'custom fuzzing frameworks'),(189,'CAN fault injection tools'),(190,'custom ECU simulation platforms'),(191,'AUTOSAR security analysis tools'),(192,'cryptographic validation tools'),(193,'Wireshark where applicable'),(194,'custom python-can or CAPL test scripts'),(195,'CAN fault-injection equipment where required'),(196,'and compatible CAN/CAN-FD interfaces such as Vector VN1630A/VN1640A'),(197,'CANoe/CANalyzer with LIN option'),(198,'NI-XNET'),(199,'PEAK PLIN-View Pro'),(200,'custom LIN scripts'),(201,'and compatible LIN interface hardware.'),(202,'CANoe/CANalyzer with FlexRay option'),(203,'Vehicle Spy with FlexRay support'),(204,'FIBEX/ARXML viewers where available'),(205,'CAPL or custom FlexRay test modules'),(206,'and compatible FlexRay interface hardware.'),(207,'CANoe/CANalyzer with Ethernet/DoIP option'),(208,'custom DoIP client scripts'),(209,'and compatible Automotive Ethernet interface hardware.'),(210,'software manipulation tools'),(211,'OEM flashing/configuration tools'),(212,'CANoe.LIN'),(213,'CANalyzer.LIN'),(214,'LIN Interactive Scheduler'),(215,'OEM flashing or diagnostic tool'),(216,'LDF/AUTOSAR network description'),(217,'UDS diagnostic client'),(218,'and LIN-capable Vector VN interface hardware.'),(219,'CANoe.FlexRay'),(220,'CANalyzer.FlexRay'),(221,'FIBEX/AUTOSAR cluster database'),(222,'ODX/PDX/CDD diagnostic description'),(223,'FrTP diagnostic client'),(224,'and compatible FlexRay interface hardware such as Vector VN7600.'),(225,'CANoe.Ethernet'),(226,'CANalyzer.Ethernet'),(227,'DoIP diagnostic client'),(228,'OEM flashing tool'),(229,'approved socket/packet test scripts'),(230,'Automotive Ethernet interface or TAP'),(231,'and TLS testing tools where applicable.'),(232,'SPI programmers'),(233,'JTAG tools'),(234,'UART bootloader tools'),(235,'and hex editors.'),(236,'JTAG debuggers'),(237,'firmware analysis utilities'),(238,'and binary editing tools.'),(239,'software version analysis tools.'),(240,'bootloader analysis tools'),(241,'firmware reverse-engineering tools.');
/*!40000 ALTER TABLE `tools_master` ENABLE KEYS */;
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

-- Dump completed on 2026-10-27 17:39:18
