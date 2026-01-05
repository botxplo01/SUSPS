# DATA SOURCES


The following are the data sources used in the system demo. All files are required for the system to run:

1. Demographics & Population
   -----------------------------

    a.) Population Density `[.tif]`: <https://www.worldpop.org/>;
    b.) Population Gridded Estimates `[.tif]`: <https://data.grid3.org/maps/20603f61a7fb4686b46deb437a18be65/about>;
    c.) Census data `[.csv]`: <https://www.macrotrends.net/global-metrics/cities/21711/nairobi/population>;

2. Mobility & Transport
   -----------------------------

    a.) Matatu Routes _(informal transport)_ `[shapefiles]`: <http://digitalmatatus.com/map.html>;
    b.) Traffic Data `[API]`: <https://developer.tomtom.com/documentation>;
    c.) Road Networks `[.pbf]`: <https://download.geofabrik.de/africa/kenya.html>;

3. Environmental & Climate
   -----------------------------

    a.) **Weather & climate:**
         - OpenWeather API key `[API]`: <https://openweathermap.org/api>;
         - OpenAQ API key `[API]`: <https://docs.openaq.org/docs>; or AirQo key `[API]`: <https://airqo.net/products/api>;
         - Air Quality Data `[.csv]`: <https://airqo.net/home>;

    b.) **Land cover & urban change** `[.tif]`:
         - Kenya Land Coverage: <https://geoportal.icpac.net/layers/kenyalandcover2015:geonode:kenyalandcover2015>;

4. Energy & Infrastructure
   -----------------------------

   a.) Energy Access and Usage Data (multiple files) `[.csv]`: <https://africa-energy-portal.org/aep/country/kenya> (expand charts under _Key Indicators_ to download files);

5. Smart City and Urban Growth
   -----------------------------

   a.) GRID3 (part 1) `[.tif]`: <https://data.grid3.org/datasets/51a70dbde2b243d8ad0aab36d37ef48b_0/explore>;
   b.) GRID3 (part 2) `[.tif]`: <https://data.grid3.org/maps/33ea771867fc4059a7a09b01643aad36/about>;

---

# FILE STRUCTURE and DIRECTORIES

Create **`data/<CITY>`** at the project root _(replace `<CITY>` with actual city or area name, e.g., `data/Nairobi`)_, then create the following sub-directories:

- **`data/<CITY>/processed`:** to locally store processed files _(keep empty, as it will be populated during preprocessing)_
- **`data/<CITY>/raw`:** to locally store raw files from **Data Sources**

Under **`data/<CITY/raw`**, ensure that you create the following sub-directories and organize local files from **Data Sources** into them:

1. **`data/<CITY>/raw/Demographics_and_Population`:** stores raw _DEMOGRAPHICS & POPULATION_ data files
2. **`data/<CITY>/raw/Energy_and_Infrastructure`:** stores raw _ENERGY & INFRASTRUCTURE_ data files
3. **`data/<CITY>/raw/Environmental_and_Climate`:** stores raw _ENVIRONMENTAL & CLIMATE_ data files
4. **`data/<CITY>/raw/Mobility_and_Transport`:** stores raw _MOBILITY & TRANSPORT_ data files
5. **`data/<CITY>/raw/Mobility_and_Transport`:** stores raw _SMART CITY & URBAN GROWTH_ data files

**Note**: Make sure to adhere to the sub-directory names to avoid directory name issues

---
