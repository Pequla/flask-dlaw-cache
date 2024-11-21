CREATE DATABASE IF NOT EXISTS `python_cache`;
USE `python_cache`;

CREATE TABLE `player_data` (
  `player_id` int unsigned NOT NULL AUTO_INCREMENT,
  `discord_id` varchar(255) NOT NULL,
  `uuid` varchar(255) NOT NULL,
  `minecraft_name` varchar(255) NOT NULL,
  `discord_name` varchar(255) NOT NULL,
  `discord_joined_at` varchar(255) NOT NULL,
  `link_created_at` varchar(255) NOT NULL,
  `cached_at` varchar(255) NOT NULL,
  PRIMARY KEY (`player_id`)
) ENGINE=InnoDB