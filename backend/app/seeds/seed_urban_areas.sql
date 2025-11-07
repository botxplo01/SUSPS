-- Minimal demo data for urban_areas table (SRID 4326)
-- Two small squares around Lusaka coords
INSERT INTO urban_areas (name, area_type, geometry)
VALUES
  (
    'Demo Area 1',
    'residential',
    ST_SetSRID(
      ST_GeomFromText('MULTIPOLYGON(((28.2800 -15.4300, 28.2800 -15.4200, 28.2900 -15.4200, 28.2900 -15.4300, 28.2800 -15.4300)))'),
      4326
    )
  ),
  (
    'Demo Area 2',
    'commercial',
    ST_SetSRID(
      ST_GeomFromText('MULTIPOLYGON(((28.3000 -15.4200, 28.3000 -15.4100, 28.3100 -15.4100, 28.3100 -15.4200, 28.3000 -15.4200)))'),
      4326
    )
  );
