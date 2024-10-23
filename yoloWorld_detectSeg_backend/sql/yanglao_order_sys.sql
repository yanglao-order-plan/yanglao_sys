/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80032
 Source Host           : localhost:3306
 Source Schema         : yolov5_garbage_detect

 Target Server Type    : MySQL
 Target Server Version : 80032
 File Encoding         : 65001

 Date: 20/05/2023 21:24:16
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Records of alembic_version
-- ----------------------------
BEGIN;
INSERT INTO `alembic_version` VALUES ('6475298b24f3');
COMMIT;

-- ----------------------------
-- Table structure for captcha
-- ----------------------------
DROP TABLE IF EXISTS `captcha`;
CREATE TABLE `captcha` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) DEFAULT NULL COMMENT '验证邮箱',
  `captcha` varchar(100) NOT NULL COMMENT '验证码',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `is_used` tinyint(1) DEFAULT NULL COMMENT '是否使用',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------
-- Table structure for dataset
-- ----------------------------
DROP TABLE IF EXISTS `dataset`;
CREATE TABLE `dataset` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '数据集id',
  `name` varchar(100) NOT NULL COMMENT '数据集名称',
  `class_num` int NOT NULL COMMENT '类别数量',
  `total_num` int NOT NULL COMMENT '总数量',
  `train_num` int NOT NULL COMMENT '训练集数量',
  `val_num` int NOT NULL COMMENT '验证集数量',
  `test_exist` tinyint(1) NOT NULL COMMENT '是否存在测试集',
  `test_num` int DEFAULT NULL COMMENT '测试集数量',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Records of dataset
-- ----------------------------
BEGIN;
INSERT INTO `dataset` VALUES (1, 'COCO', 80, 123287, 118287, 5000, 0, 20288);
INSERT INTO `dataset` VALUES (2, 'Sample', 6, 1200, 972, 108, 1, 120);
INSERT INTO `dataset` VALUES (3, 'TACO', 8, 1086, 869, 108, 1, 109);
INSERT INTO `dataset` VALUES (4, 'Garbage', 43, 14964, 12120, 1347, 1, 1497);
COMMIT;

-- ----------------------------
-- Table structure for result
-- ----------------------------
DROP TABLE IF EXISTS `result`;
CREATE TABLE `result` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '结果id',
  `img_path` text NOT NULL COMMENT '原始图片路径',
  `data` text NOT NULL COMMENT '结果数据',
  `plot_path` varchar(100) NOT NULL COMMENT '结果图片路径',
  `start_time` datetime DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `hyper` JSON DEFAULT NULL COMMENT '动态超参数',
  `user_id` int DEFAULT NULL,
  `release_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  FOREIGN KEY (`release_id`) REFERENCES `release` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for task_type
-- ----------------------------
DROP TABLE IF EXISTS `task_type`;
CREATE TABLE `task_type` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '任务类型ID',
  `name` VARCHAR(50) NOT NULL COMMENT '任务类型名称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入任务类型数据
BEGIN;
INSERT INTO `task_type` VALUES
(1, 'close_set'),
(2, 'open_set'),
(3, 'combi');
COMMIT;

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `name` VARCHAR(50) NOT NULL COMMENT '任务名称',
  `type_id` int DEFAULT NULL COMMENT '任务类型ID',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`type_id`) REFERENCES `task_type` (`id`)
  UNIQUE KEY `unique_name_type` (`name`, `type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入任务数据
BEGIN;
INSERT INTO `task` VALUES
(1, 'classification', 1),
(2, 'object_detection', 1),
(3, 'rotate_object_detection', 1),
(4, 'semantic_segmentation', 1),
(5, 'pose_estimation', 1),
(6, 'face_detection', 1),
(7, 'track_object_detection', 1),
(8, 'track_segmentation', 1),
(9, 'track_rotate_object_detection', 1),
(10, 'track_pose_estimation', 1),
(11, 'car_plate_detection', 1),
(12, 'attribute_recognition', 1),
(13, 'background_removal', 1),
(14, 'optical_character_recognition', 1),
(15, 'classification', 2),
(16, 'object_detection', 2),
(17, 'semantic_segmentation', 2),
(18, 'depth_estimation', 2),
(19, 'detection_segmentation', 3),
(20, 'classification_detection', 3);
COMMIT;

-- ----------------------------
-- Table structure for flow
-- ----------------------------
DROP TABLE IF EXISTS `flow`;
CREATE TABLE `flow` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '流程ID',
  `name` VARCHAR(100) NOT NULL COMMENT '流程名称',
  `task_id` INT NOT NULL COMMENT '任务ID',
  PRIMARY KEY (`id`),
  -- 外键约束
  FOREIGN KEY (`task_id`) REFERENCES `task` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入工作流数据
BEGIN;
INSERT INTO `flow` VALUES
(1, 'yolo11_cls', 1),
(2, 'internimage_cls', 1),
(3, 'yolov5_cls', 1),
(4, 'yolov8_cls', 1),
(5, 'yolo11', 2),
(6, 'yolo_nas', 2),
(7, 'yolov10', 2),
(8, 'yolov5', 2),
(9, 'yolov6', 2),
(10, 'yolov7', 2),
(11, 'yolov8', 2),
(12, 'yolov9', 2),
(13, 'gold_yolo', 2),
(14, 'damo_yolo', 2),
(15, 'rtdetr', 2),
(16, 'rtdetrv2', 2),
(17, 'yolox', 2),
(18, 'yolov8_sahi', 2),
(19, 'yolov5_resnet', 2),
(20, 'yolo11_obb', 3),
(21, 'yolov5_obb', 3),
(22, 'yolov8_obb', 3),
(23, 'yolo11_seg', 4),
(24, 'yolov5_seg', 4),
(25, 'yolov8_seg', 4),
(26, 'yolo11_pose', 5),
(27, 'yolov8_pose', 5),
(28, 'rtmdet_pose', 5),
(29, 'yolox_dwpose', 5),
(30, 'yolov6_face', 6),
(31, 'yolo11_det_track', 7),
(32, 'yolov5_det_track', 7),
(33, 'yolov8_det_track', 7),
(34, 'yolo11_seg_track', 8),
(35, 'yolov8_seg_track', 8),
(36, 'yolo11_obb_track', 9),
(37, 'yolov8_obb_track', 9),
(38, 'yolo11_pose_track', 10),
(39, 'yolov8_pose_track', 10),
(40, 'yolov5_car_plate', 11),
(41, 'pulc_attribute', 12),
(42, 'rmbg', 13),
(43, 'ppocr_v4', 14),
(44, 'ram', 15),
(45, 'yolow', 16),
(46, 'grounding_dino', 16),
(47, 'segment_anything', 17),
(48, 'segment_anything_2', 17),
(49, 'segment_anything_2_video', 17),
(50, 'sam_hq', 17),
(51, 'sam_med2d', 17),
(52, 'edge_sam', 17),
(53, 'efficientvit_sam', 17),
(54, 'depth_anything', 18),
(55, 'depth_anything_v2', 18),
(56, 'grounding_sam', 19),
(57, 'grounding_sam2', 19),
(58, 'yolov8_efficientvit_sam', 19),
(59, 'yolov5_sam', 19),
(60, 'yolov5_ram', 20),
(61, 'yolow_ram', 20);
COMMIT;

-- ----------------------------
-- Table structure for version
-- ----------------------------
DROP TABLE IF EXISTS `release`;
CREATE TABLE `release` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '版本ID',
  `name` VARCHAR(100) NOT NULL COMMENT '版本名称',
  `show_name` VARCHAR(100) NOT NULL COMMENT '显示名称',
  `flow_id` INT NOT NULL COMMENT '流程ID',
  `keys` JSON NOT NULL COMMENT '关键字组',
  `params` JSON NOT NULL COMMENT '固定参数组',
  PRIMARY KEY (`id`),
  -- 外键约束
  FOREIGN KEY (`flow_id`) REFERENCES `flow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入版本数据

-- ----------------------------
-- Relation structure for weights
-- ----------------------------
DROP TABLE IF EXISTS `release_weight`;
CREATE TABLE `release_weight` (
  `release_id` INT NOT NULL COMMENT '版本ID',
  `weight_id` INT NOT NULL COMMENT '权重ID',
  `key` VARCHAR(100) NOT NULL COMMENT '关键字',
  -- 外键约束
  PRIMARY KEY (`release_id`, `weight_id`),
  FOREIGN KEY (`release_id`) REFERENCES `release` (`id`),
  FOREIGN KEY (`weight_id`) REFERENCES `weight` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for weights
-- ----------------------------
DROP TABLE IF EXISTS `weight`;
CREATE TABLE `weight` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '权重id',
  `name` varchar(100) NOT NULL COMMENT '权重名称',
  `local_path` text NULL COMMENT '本地路径',
  `online_url` text NULL COMMENT '在线链接',
  `enable` tinyint(1) NOT NULL COMMENT '是否启用',
  `dataset_id` INT NULL COMMENT '数据集ID',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for learn
-- ----------------------------
-- DROP TABLE IF EXISTS `weight`;
-- CREATE TABLE `weight` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '权重id',
--   `name` varchar(100) NOT NULL COMMENT '权重名称',
--   `relative_path` text NOT NULL COMMENT '权重相对路径',
--   `absolute_path` text COMMENT '权重绝对路径',
--   `online_url` text COMMENT '权重在线链接',
--   `enable` tinyint(1) NOT NULL COMMENT '是否启用',
--   PRIMARY KEY (`id`),
--   KEY `dataset_id` (`dataset_id`),
--   KEY `mode_id` (`mode_id`),
--   CONSTRAINT `weight_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
-- ) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for image
-- ----------------------------
-- DROP TABLE IF EXISTS `image`;
-- CREATE TABLE `image` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '图片id',
--   `name` varchar(100) NOT NULL COMMENT '图片名称',
--   `absolute_path` text COMMENT '图片绝对路径',
--   `relative_path` text COMMENT '图片相对路径',
--   `type` varchar(100) NOT NULL COMMENT '图片类型',
--   `dataset_id` int DEFAULT NULL,
--   PRIMARY KEY (`id`),
--   KEY `dataset_id` (`dataset_id`),
--   CONSTRAINT `image_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------
-- Table structure for image_label_info
-- ----------------------------
-- DROP TABLE IF EXISTS `sample`;
-- CREATE TABLE `sample` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '样本id',
--   `image_id` int DEFAULT NULL COMMENT '图片id',
--   `label_id` int DEFAULT NULL COMMENT '标签id',
--   PRIMARY KEY (`id`),
--   KEY `image_id` (`image_id`),
--   KEY `label_id` (`label_id`),
--   CONSTRAINT `image_label_info_ibfk_1` FOREIGN KEY (`image_id`) REFERENCES `image` (`id`),
--   CONSTRAINT `image_label_info_ibfk_2` FOREIGN KEY (`label_id`) REFERENCES `label` (`id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------
-- Table structure for label
-- ----------------------------
-- DROP TABLE IF EXISTS `label`;
-- CREATE TABLE `label` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '标注id',
--   `name` varchar(100) NOT NULL COMMENT '标注信息',
--   `subtask_id` int DEFAULT NULL,
--   PRIMARY KEY (`id`),
--   KEY `dataset_id` (`dataset_id`),
--   CONSTRAINT `label_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for role
-- ----------------------------
DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '角色id',
  `name` varchar(100) NOT NULL COMMENT '角色名称',
  `desc` varchar(100) NOT NULL COMMENT '角色描述',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Records of role
-- ----------------------------
BEGIN;
INSERT INTO `role` VALUES (1, 'admin', '管理员');
INSERT INTO `role` VALUES (2, 'user', '普通用户');
COMMIT;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户id',
  `username` varchar(100) NOT NULL COMMENT '用户名',
  `password` varchar(500) NOT NULL COMMENT '密码',
  `email` varchar(100) NOT NULL COMMENT '邮箱',
  `join_time` datetime DEFAULT NULL COMMENT '加入时间',
  `status` tinyint(1) DEFAULT NULL COMMENT '是否启用',
  `role_id` int DEFAULT NULL COMMENT '用户角色',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  FOREIGN KEY (`role_id`) REFERENCES `role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2007 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



-- ----------------------------
-- Table structure for service
-- ----------------------------
-- DROP TABLE IF EXISTS `service`;
-- CREATE TABLE `service` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '服务id',
--   `name` varchar(100) NOT NULL COMMENT '服务名称',
--   `model_version` varchar(100) NOT NULL COMMENT '模型版本',
--   `task_id` int DEFAULT NULL,
--   PRIMARY KEY (`id`),
--   KEY `model_id` (`model_id`),
--   CONSTRAINT `model_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `task` (`id`)
-- ) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------
-- Table structure for order
-- ----------------------------
-- DROP TABLE IF EXISTS `order`;
-- CREATE TABLE `order` (
--   `id` int NOT NULL AUTO_INCREMENT COMMENT '工单id',
--   `model_name` varchar(100) NOT NULL COMMENT '工单编号',
--   `model_version` varchar(100) NOT NULL COMMENT '模型版本',
--   `task_id` int DEFAULT NULL,
--   PRIMARY KEY (`id`),
--   KEY `model_id` (`model_id`),
--   CONSTRAINT `model_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `task` (`id`)
-- ) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ----------------------------
-- Records of weights
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
