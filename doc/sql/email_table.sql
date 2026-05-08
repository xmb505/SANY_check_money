-- 创建 email 表
CREATE TABLE `email` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `device_id` varchar(32) NOT NULL,
  `verifi_code` varchar(10) NOT NULL,
  `created_time` datetime NOT NULL DEFAULT current_timestamp(),
  `verifi_end_time` datetime NOT NULL,
  `verifi_statu` tinyint(1) DEFAULT 0 COMMENT '0=未验证，1=已验证',
  `life_end_time` datetime NOT NULL,
  `change_device_statu` tinyint(1) DEFAULT 0 COMMENT '0=正常，1=切换',
  `updated_time` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `ip_address` varchar(45) DEFAULT NULL,
  `alarm_num` int(11) DEFAULT NULL,
  `equipment_type` tinyint(1) NOT NULL COMMENT '0=电表，1=水表',
  `change_code` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_email_device_type` (`email`, `device_id`, `equipment_type`),
  KEY `idx_email` (`email`),
  KEY `idx_verifi_time` (`verifi_end_time`),
  KEY `idx_life_time` (`life_end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='邮箱订阅表';