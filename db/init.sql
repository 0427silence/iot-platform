-- ============================================================
-- IoT Platform - 数据库初始化脚本
-- 适用于: MySQL 8.0+
-- 字符集: utf8mb4
-- 引擎: InnoDB
-- ============================================================

CREATE DATABASE IF NOT EXISTS iot_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE iot_platform;

-- ============================================================
-- 表1: devices - 设备主表
-- 说明: 存储所有注册的 IoT 设备信息
-- ============================================================
DROP TABLE IF EXISTS alarm_logs;
DROP TABLE IF EXISTS alarm_rules;
DROP TABLE IF EXISTS device_data;
DROP TABLE IF EXISTS devices;

CREATE TABLE devices (
    -- 主键ID，自增
    id              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键ID，自增',
    -- 设备唯一标识符（如 ESP32 MAC 地址或自定义编号）
    device_id       VARCHAR(64)     NOT NULL                                COMMENT '设备唯一标识符，如 MAC 地址或自定义编号',
    -- 设备名称，便于人类识别
    device_name     VARCHAR(128)    NOT NULL                                COMMENT '设备名称',
    -- 设备类型: temperature_sensor, humidity_sensor, multi_sensor, gateway 等
    device_type     VARCHAR(64)     NOT NULL                                COMMENT '设备类型，如 temperature_sensor、humidity_sensor、multi_sensor、gateway',
    -- 设备安装位置描述
    location        VARCHAR(256)    DEFAULT NULL                            COMMENT '设备安装位置，如 办公楼3层A区',
    -- 设备状态: 0=离线, 1=在线, 2=故障
    status          TINYINT         NOT NULL DEFAULT 0                      COMMENT '设备状态: 0=离线, 1=在线, 2=故障',
    -- 固件版本号
    firmware_version VARCHAR(32)    DEFAULT NULL                            COMMENT '固件版本号',
    -- 设备最后一次上线/上报数据的时间
    last_online_at  DATETIME        DEFAULT NULL                            COMMENT '设备最后一次上线时间',
    -- 记录创建时间
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP      COMMENT '记录创建时间',
    -- 记录更新时间，自动更新
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间，自动维护',

    PRIMARY KEY (id),
    UNIQUE KEY uk_device_id (device_id),
    KEY idx_device_type (device_type),
    KEY idx_status (status),
    KEY idx_last_online_at (last_online_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='设备主表 - 存储所有注册的 IoT 设备基础信息';


-- ============================================================
-- 表2: device_data - 设备遥测历史数据表
-- 说明: 存储设备上报的所有历史遥测数据，按时间排序
-- ============================================================
CREATE TABLE device_data (
    -- 主键ID，自增
    id              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键ID，自增',
    -- 关联的设备唯一标识符
    device_id       VARCHAR(64)     NOT NULL                               COMMENT '设备唯一标识符，关联 devices.device_id',
    -- 温度读数，单位: 摄氏度，支持两位小数精度
    temperature     DECIMAL(5,2)    DEFAULT NULL                           COMMENT '温度读数，单位摄氏度(℃)，如 26.50',
    -- 湿度读数，单位: 百分比，支持两位小数精度
    humidity        DECIMAL(5,2)    DEFAULT NULL                           COMMENT '湿度读数，单位百分比(%)，如 65.30',
    -- 电池电量，单位: 百分比，支持两位小数精度
    battery_level   DECIMAL(5,2)    DEFAULT NULL                           COMMENT '电池电量百分比(%)，如 85.00',
    -- 信号强度，单位: dBm，通常为负值
    signal_strength INT             DEFAULT NULL                           COMMENT '信号强度，单位 dBm，通常为负数，如 -65',
    -- 扩展数据字段，JSON 格式存储非标准传感器数据
    extra_data      JSON            DEFAULT NULL                           COMMENT '扩展传感器数据，JSON 格式。示例: {"co2": 420, "pm2_5": 35, "light_lux": 1200}',
    -- 设备上报此条数据的时间（设备端时间戳）
    reported_at     DATETIME        NOT NULL                               COMMENT '设备上报数据的时间（设备端时间戳）',
    -- 服务端接收此条数据的时间
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP      COMMENT '服务端接收此条数据的时间',

    PRIMARY KEY (id),
    KEY idx_device_id_time (device_id, reported_at),
    KEY idx_reported_at (reported_at),

    -- 外键约束: 确保数据一致性，设备删除时级联删除其历史数据
    CONSTRAINT fk_device_data_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='设备遥测历史数据表 - 存储所有设备上报的传感器读数和时间序列数据';


-- ============================================================
-- 表3: alarm_rules - 告警规则配置表
-- 说明: 存储用户配置的告警阈值规则，支持设备专属+全局规则
-- ============================================================
CREATE TABLE alarm_rules (
    id              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键ID，自增',
    device_id       VARCHAR(64)     DEFAULT NULL                            COMMENT '设备ID，NULL表示全局规则适用于所有设备',
    metric_name     VARCHAR(32)     NOT NULL                                COMMENT '监控指标: temperature/humidity/battery_level/signal_strength',
    operator        VARCHAR(4)      NOT NULL                                COMMENT '比较运算符: >/</>=/<=/==',
    threshold_value DECIMAL(10,2)   NOT NULL                                COMMENT '告警阈值',
    is_active       TINYINT         NOT NULL DEFAULT 1                      COMMENT '规则启用: 0=停用, 1=启用',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP      COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (id),
    KEY idx_device_id (device_id),
    KEY idx_is_active (is_active),

    CONSTRAINT fk_alarm_rule_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='告警规则配置表 - 用户配置的告警阈值规则';


-- ============================================================
-- 表4: alarm_logs - 告警日志表
-- 说明: 记录每一次告警触发与恢复的完整历史
-- ============================================================
CREATE TABLE alarm_logs (
    id              BIGINT          NOT NULL AUTO_INCREMENT                COMMENT '主键ID，自增',
    device_id       VARCHAR(64)     NOT NULL                               COMMENT '触发告警的设备ID',
    rule_id         BIGINT          NOT NULL                               COMMENT '触发的规则ID',
    alarm_type      VARCHAR(64)     NOT NULL                               COMMENT '告警类型标识，如 temperature_>40.00',
    message         TEXT            NOT NULL                               COMMENT '告警消息内容',
    metric_value    DECIMAL(10,2)   NOT NULL                               COMMENT '触发时的实际指标值',
    threshold_value DECIMAL(10,2)   NOT NULL                               COMMENT '触发时的阈值',
    status          TINYINT         NOT NULL DEFAULT 0                     COMMENT '告警状态: 0=未处理, 1=已恢复',
    triggered_at    DATETIME        NOT NULL                               COMMENT '告警触发时间',
    resolved_at     DATETIME        DEFAULT NULL                           COMMENT '告警恢复时间',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP     COMMENT '服务端记录时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (id),
    KEY idx_device_id (device_id),
    KEY idx_rule_id (rule_id),
    KEY idx_status (status),
    KEY idx_triggered_at (triggered_at),

    CONSTRAINT fk_alarm_log_device
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_alarm_log_rule
        FOREIGN KEY (rule_id) REFERENCES alarm_rules(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='告警日志表 - 记录所有告警触发与恢复事件';
