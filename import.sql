-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 使用数据库
USE your_database_name;

-- 创建 device 表
CREATE TABLE `device` (
  `id` varchar(32) NOT NULL,
  `addr` varchar(20) DEFAULT NULL,
  `equipmentName` varchar(100) DEFAULT NULL,
  `installationSite` varchar(100) DEFAULT NULL,
  `equipmentType` tinyint(1) DEFAULT NULL,
  `ratio` decimal(10,2) DEFAULT NULL,
  `rate` decimal(10,4) DEFAULT NULL,
  `acctId` varchar(20) DEFAULT NULL,
  `status` tinyint(1) DEFAULT NULL,
  `properties` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`properties`)),
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_acctId` (`acctId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 创建 data 表
CREATE TABLE `data` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(32) NOT NULL,
  `read_time` datetime NOT NULL,
  `total_reading` decimal(15,2) DEFAULT NULL,
  `diff_reading` decimal(15,2) DEFAULT NULL,
  `remainingBalance` decimal(15,6) DEFAULT NULL,
  `equipmentStatus` tinyint(1) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `remark` varchar(255) DEFAULT NULL,
  `unStandard` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_device_time` (`device_id`,`read_time`),
  CONSTRAINT `data_ibfk_1` FOREIGN KEY (`device_id`) REFERENCES `device` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;