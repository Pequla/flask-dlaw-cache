CREATE DATABASE IF NOT EXISTS `python_cache`;
USE `python_cache`;

CREATE TABLE IF NOT EXISTS `player_data` (
  `playerId` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `discordId` char(50) NOT NULL DEFAULT '0',
  `uuid` char(50) NOT NULL DEFAULT '0',
  `minecraft_name` char(50) NOT NULL DEFAULT '0',
  `discord_name` char(50) NOT NULL DEFAULT '0',
  `discord_joined_at` char(50) NOT NULL DEFAULT '0',
  `link_created_at` char(50) NOT NULL DEFAULT '0',
  `cached_at` char(50) NOT NULL DEFAULT '0',
  PRIMARY KEY (`playerId`)
) ENGINE=InnoDB ;
