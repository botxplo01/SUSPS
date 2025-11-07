-- Demo traffic flow records for two areas
INSERT INTO traffic_flow (area_id, ts, predicted_volume, actual_volume, congestion_level) VALUES
  (1, '2025-01-01 08:00:00+00', 1100, 1050, 'high'),
  (1, '2025-01-01 18:00:00+00', 900, 870, 'medium'),
  (2, '2025-01-01 08:00:00+00', 600, 580, 'medium'),
  (2, '2025-01-01 18:00:00+00', 450, 430, 'low');
