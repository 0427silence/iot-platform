-- ============================================================
-- 告警规则种子数据
-- 执行时机: 启动 simulator 注册设备后
-- 执行方式: mysql -u root -p < db/seed_alarms.sql
-- ============================================================

USE iot_platform;

INSERT INTO alarm_rules (device_id, metric_name, operator, threshold_value, is_active) VALUES
('sensor-temp-001',   'temperature',   '>', 40.00, 1),
('sensor-humid-002',  'humidity',      '>', 80.00, 1),
('sensor-env-003',    'temperature',   '>', 35.00, 1),
('sensor-indoor-004', 'temperature',   '>', 35.00, 1),
(NULL,                'battery_level', '<', 10.00, 1);
