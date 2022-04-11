-- MySQL dump 10.13  Distrib 8.0.23, for Linux (x86_64)
--
-- Host: localhost    Database: eplant_soybean
-- ------------------------------------------------------
-- Server version	8.0.23-3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `eplant_soybean`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `eplant_soybean` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `eplant_soybean`;

--
-- Table structure for table `isoforms`
--

DROP TABLE IF EXISTS `isoforms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `isoforms` (
  `gene` varchar(20) NOT NULL,
  `isoform` varchar(24) NOT NULL,
  KEY `idx_gene_isoform` (`gene`,`isoform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `isoforms`
--

LOCK TABLES `isoforms` WRITE;
/*!40000 ALTER TABLE `isoforms` DISABLE KEYS */;
INSERT INTO `isoforms` VALUES ('Glyma.01G000100','Glyma.01G000100'),('Glyma.01G000200','Glyma.01G000200'),('Glyma.001G000400','Glyma.001G000400');
/*!40000 ALTER TABLE `isoforms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gene_annotation`
--

DROP TABLE IF EXISTS `gene_annotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gene_annotation` (
  `gene` varchar(20) NOT NULL,
  `annotation` mediumtext NOT NULL,
  PRIMARY KEY (`gene`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gene_annotation`
-- NOTE: The native eplant DB has '.1' transcript extensions for soybean hence it is here below
-- 

LOCK TABLES `gene_annotation` WRITE;
/*!40000 ALTER TABLE `gene_annotation` DISABLE KEYS */;
INSERT INTO `gene_annotation` VALUES ('Glyma.01G000100.1', '2.2.1.9//4.2.1.113//4.2.99.20 - 2-succinyl-5-enolpyruvyl-6-hydroxy-3-cyclohexene-1-carboxylic-acid synthase / SEPHCHC synthase // o-succinylbenzoate synthase / OSBS // 2-succinyl-6-hydroxy-2,4-cyclohexadiene-1-carboxylate synthase / SHCHC synthase (1 of 10)');
/*!40000 ALTER TABLE `gene_annotation` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-06-26 19:08:20
