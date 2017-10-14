-- MySQL dump 10.13  Distrib 5.7.19, for Linux (x86_64)
--
-- Host: localhost    Database: crossover_db
-- ------------------------------------------------------
-- Server version	5.7.19

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `collected_stats`
--

DROP TABLE IF EXISTS `collected_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `collected_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip_addr` varchar(45) NOT NULL,
  `os` varchar(45) DEFAULT NULL,
  `cpu_usage` varchar(45) DEFAULT NULL,
  `mem_usage` varchar(45) DEFAULT NULL,
  `uptime` varchar(45) DEFAULT NULL,
  `event_logs` longtext,
  `collection_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `consulted_for_alerts` tinyint(1) DEFAULT '0' COMMENT 'This field is used to indicate whether the spcific record was consulted (and potentially generated an alert) or not. THe alerter modle uses this field in order to trigger alerts.',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;


