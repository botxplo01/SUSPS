-- Demo energy consumption records for two areas
INSERT INTO energy_consumption (area_id, ts, predicted_demand, actual_demand) VALUES
  (1, '2025-01-01 08:00:00+00', 12.5, 12.0),
  (1, '2025-01-01 18:00:00+00', 15.0, 14.2),
  (2, '2025-01-01 08:00:00+00', 7.8, 7.5),
  (2, '2025-01-01 18:00:00+00', 9.3, 9.0);
