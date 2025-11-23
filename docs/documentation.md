# Cover / Title Page

CAVENDISH UNIVERSITY ZAMBIA  
School of Business Information and Technology  
BSC COMP Research/Project Documentation

SMART URBAN SIMULATION AND PREDICTION SYSTEM (SUSPS)

A Research Project Submitted in Partial Fulfilment of the Requirements for the Degree of  
[Degree Name]

by  
Lameck David Musumpuka  
Student Number: 106-461

[Department / School Name]  
Year of Publication: 2025

---

## Declaration

I, **David Lameck**, hereby declare that this research project report entitled **"SMART URBAN SIMULATION AND PREDICTION SYSTEM (SUSPS)"** is my own original work. It has not been submitted, in whole or in part, for the award of a degree or diploma at Cavendish University Zambia or any other institution of higher learning.

Where the work of others has been used, whether in the form of ideas, data, text, tables, figures, or software, this has been clearly acknowledged and referenced in accordance with academic conventions. To the best of my knowledge and belief, this work is free from plagiarism and was conducted in accordance with the ethical guidelines of Cavendish University Zambia.

Signed: _____________________________

Name:   David Lameck

Date:   _____________________________

## Acknowledgement

I wish to express my sincere gratitude to **Cavendish University Zambia** for providing the opportunity, academic environment, and resources that made this project possible. I am especially grateful to my supervisor, **[Supervisor's Name]**, for their guidance, constructive feedback, and encouragement throughout the research and development of this system.

My appreciation also goes to the staff and colleagues in the **[Faculty Name]** for their support, discussions, and suggestions, which helped to refine both the technical and research components of this work. I further acknowledge the contribution of open data and open-source communities whose tools and datasets underpin this project. In particular, I am indebted to initiatives such as WorldPop, GRID3, OpenStreetMap, Digital Matatus, TomTom, OpenWeather, OpenAQ, AirQo, the Africa Energy Portal, ICPAC, and other organisations that make high-quality data freely available for research and public benefit.

To my family and friends, thank you for your unwavering support, patience, and encouragement. Your belief in me has been a constant source of motivation. Above all, I am grateful to God for the strength, health, and perseverance granted to complete this work.

## Dedication

This work is dedicated to my family, whose love, support, and sacrifices have made my education possible, and to all students and practitioners striving to use data and technology to build more sustainable and inclusive African cities.

## Glossary

- **API (Application Programming Interface):** A defined set of rules and endpoints through which software components communicate, typically using HTTP and JSON in this project.
- **AQI (Air Quality Index):** A numerical scale used to communicate how polluted the air currently is or how polluted it is forecast to become.
- **Census trend:** A time-series of official population counts used to estimate growth rates and construct forecast baselines.
- **CSV (Comma-Separated Values):** A plain-text file format used to store tabular data where each row is a record and columns are separated by commas.
- **ETL (Extract, Transform, Load):** A data-processing approach in which raw data are extracted from sources, transformed into a consistent structure, and loaded into storage for analysis.
- **FastAPI:** A modern, high-performance Python web framework used in this project to implement the backend REST API.
- **GeoJSON:** A JSON-based format for encoding a variety of geographic data structures such as points, lines, and polygons.
- **GIS (Geographic Information System):** A system for capturing, storing, analysing, and visualising data that have a spatial or geographic component.
- **GTFS (General Transit Feed Specification):** A standard file format for public transport schedules and associated geographic information.
- **Hotspot:** A spatial unit or area with a relatively high concentration of combined pressures or risks (e.g., high population density, congestion, or energy stress) compared to other units.
- **Hugging Face:** An open-source ecosystem and model hub providing machine learning models and APIs; used here for optional advisory and time-series forecasting.
- **JSON / JSONB:** A lightweight data-interchange format (JSON) and its binary form in PostgreSQL (JSONB) used to store flexible, semi-structured attributes such as parameters and metadata.
- **OSM (OpenStreetMap):** A collaborative project that creates and provides free geographic data, including roads, buildings, and points of interest.
- **Pipeline:** In this context, a sequence of scripts and modules that ingest raw datasets, clean and transform them, and produce processed artefacts used by models and APIs.
- **PostgreSQL:** An open-source relational database management system used to store structured data such as areas, energy consumption, traffic flows, and hotspot scores.
- **PostGIS:** A spatial extension to PostgreSQL that adds support for geometry types and spatial queries.
- **Render:** A cloud platform used to deploy the SUSPS backend API and frontend static site.
- **SDG (Sustainable Development Goal):** A set of global goals adopted by the United Nations; SDG 11 focuses on Sustainable Cities and Communities.
- **SPA (Single-Page Application):** A web application that loads a single HTML page and dynamically updates content on the client side without full page reloads; in this project, implemented using React.
- **SUSPS (Smart Urban Simulation and Prediction System):** The system developed in this project to integrate urban growth, energy, traffic, and environmental data into a unified simulation and decision-support platform.

## Abstract

Urbanisation in many African cities, including Lusaka, is accelerating rapidly, increasing pressure on transport networks, energy systems, land use, and environmental resources. Existing planning processes often rely on fragmented datasets, infrequent census updates, and manual projections, making it difficult for policymakers to anticipate future trends or respond proactively to emerging challenges. Despite the growing availability of open geospatial, mobility, demographic, and environmental datasets, there remains a critical gap in integrated, data-driven platforms that can translate heterogeneous information into actionable insights for urban planning. This project addresses that gap through the design and implementation of the Smart Urban Simulation and Prediction System (SUSPS)—a lightweight, extensible, and free-tier-compatible decision-support tool tailored to the constraints of Lusaka and similar Sub-Saharan African cities.

SUSPS integrates demographic, mobility, energy, environmental, and socio-economic datasets into a unified analytics environment capable of producing baseline forecasts, simulation scenarios, hotspot analysis, and narrative advisories. The system is implemented using a FastAPI backend, a React single-page application, a reproducible Python data pipeline, and optional PostgreSQL/PostGIS support. Nairobi is used as the demonstration city due to its richer open datasets, while the architecture remains portable to Lusaka through configurable city parameters. Methodologically, the study follows a design science approach consisting of problem identification, baseline data study, iterative modelling, system development, and evaluation. Lightweight and interpretable models are used for population growth, energy demand profiling, and traffic-flow approximation, supported by free-tier APIs such as OpenStreetMap, Digital Matatus, OpenWeather, OpenAQ, GRID3, WorldPop, and the Africa Energy Portal. An AI-assisted advisory engine, powered by optional Hugging Face models, translates quantitative results into concise narrative insights for non-technical stakeholders.

Results from the baseline study demonstrate that SUSPS generates realistic and literature-consistent outputs, including population growth trajectories, representative daily traffic profiles, hourly and daily energy-demand curves, and composite spatial hotspots showing areas of overlapping pressure. Automated tests, qualitative checks, and scenario-based analyses confirm that system behaviour is plausible and that outputs can support forward-looking planning discussions. The modular architecture, environment parity tools, and S3-backed raw-data workflow ensure reproducibility across local and cloud deployments.

The project contributes a functional prototype of an integrated urban analytics platform designed specifically for data-scarce cities. It demonstrates that even under constraints of limited data, infrastructure, and institutional capacity, it is feasible to build reproducible, interpretable, and actionable decision-support tools using open datasets, modern web technologies, and lightweight models. By combining growth forecasting, energy profiling, traffic approximation, spatial hotspot mapping, and accessible advisory narratives, SUSPS advances the shift from reactive toward proactive, evidence-informed planning in Lusaka and similar rapidly growing African cities. The system provides a solid foundation for future enhancements, including richer local datasets, more advanced models, stakeholder evaluations, and expanded integration with planning workflows.

## Table of Contents

[This table of contents is indicative; it can be regenerated in Word after conversion.]

## List of Tables

[Table 3.1: Summary of core datasets and data sources – to be inserted here]

[Table 4.1: Baseline results summary – to be inserted here]

[Table 4.2: Example forecast accuracy results (growth, energy, traffic) – to be inserted here]

---

## List of Figures

[Figure 3.1: High-level system architecture diagram – to be inserted here]

[Figure 3.2: Data pipeline and ETL workflow – to be inserted here]

[Figure 3.3: Deployment architecture (local vs Render) – to be inserted here]

[Figure 3.4: SUSPS use-case diagram – to be inserted here]

[Figure 3.5: SUSPS dependency diagram – to be inserted here]

[Figure 3.6: General flowchart for SUSPS – to be inserted here]

[Figure 3.7: SUSPS activity diagram – to be inserted here]

[Figure 3.8: SUSPS deployment diagram on Render – to be inserted here]

[Figure 4.1: Database entity–relationship diagram – to be inserted here]

[Figure 5.1: Sample dashboard screenshot (urban growth, energy, traffic) – to be inserted here]

[Figure 5.2: Hotspot and optimal zones map screenshot – to be inserted here]

---

# CHAPTER ONE: INTRODUCTION

## 1.0 Introduction

Urbanisation is transforming cities across the globe, with more than half of the world’s population now living in urban areas and this share projected to increase further in the coming decades (United Nations, 2019). Rapid and often unplanned growth creates pressure on transport networks, housing, land use, and energy systems, and these pressures are particularly acute in developing regions where planning capacity and resources may be constrained (UN-Habitat, 2020; World Bank, 2021). In many Sub-Saharan African countries these pressures are intensified by limited institutional capacity and gaps in data-driven planning. As a result, infrastructure investments frequently lag behind demand, congestion worsens, and service delivery becomes unreliable.

Zambia is experiencing these dynamics, particularly in Lusaka and fast-growing towns (World Bank, 2021). Population growth, expansion of informal settlements, and rising motorisation are placing sustained pressure on existing roads, power infrastructure, and public services. Planning processes have traditionally relied on infrequent census snapshots, static master plans, and manual projections, which struggle to keep pace with changes on the ground. At the same time, there is an increasing availability of open geospatial data, mobility datasets, and environmental information that could support more proactive planning if integrated into a coherent decision-support system (Lemmens et al., 2017; Zheng et al., 2014).

The Smart Urban Simulation and Prediction System (SUSPS) has been developed to address this gap. SUSPS integrates demographic, mobility, energy, and environmental datasets into a unified platform that can simulate urban growth, forecast energy demand, and approximate traffic flow patterns. The implemented system combines a FastAPI backend, a React single-page application (SPA), a reproducible Python data pipeline, and an optional PostgreSQL/PostGIS database. For the current phase of the work, Nairobi is used as a demonstration city due to richer open datasets and its similarity to Lusaka’s emerging mobility and settlement patterns. The system and pipelines are, however, parameterised so that they can be ported to Lusaka as data availability improves.

This chapter introduces the study, outlines the motivation and significance of the work, defines the research objectives and questions, presents the conceptual framework, and summarises how the rest of the report is organised.

## 1.1 Background

Urban planning in many African cities has historically been reactive. Infrastructure is upgraded only after congestion, informal settlements, and service backlogs have become entrenched (UN-Habitat, 2020). Research on smart cities and urban analytics demonstrates that integrating data from multiple domains—demographics, land use, transport, energy, and the environment—can support more proactive and evidence-based decision making (Albino et al., 2015; Batty, 2018; Zheng et al., 2014). In practice, however, African cities often lack integrated platforms and tools that can translate heterogeneous datasets into actionable insights for planners and policymakers (Lemmens et al., 2017).

In Zambia, national and local agencies collect census data, administrative records, and sectoral statistics, but these datasets are rarely fused into a single analytical environment. Transport planning is typically based on household surveys or manual traffic counts; energy planning relies on utility reports and high-level projections; settlement growth is monitored through periodic mapping exercises rather than continuous analytics. These fragmented approaches make it difficult to answer forward-looking questions such as: where will new population growth be concentrated, how will traffic volumes evolve across corridors, and what levels of energy demand should be expected under different growth scenarios?

At the same time, there has been rapid growth in openly available geospatial and mobility data. Examples include WorldPop gridded population datasets, OpenStreetMap road and points-of-interest layers, General Transit Feed Specification (GTFS) feeds, and global or regional environmental and climate datasets (Williams et al., 2015; Zheng et al., 2014). When combined with local census data and utility information, these sources can support predictive models of population distribution, trip-making, and energy use. SUSPS is designed to operationalise these ideas in a concrete, reproducible system targeting Lusaka as the primary use context and Nairobi as the demonstration and testing environment.

## 1.2 Significance of the Study

This study is significant at several levels (UN-Habitat, 2020; World Bank, 2021):

- **Policy support for planners and government agencies.** By integrating demographic, mobility, energy, and environmental data into a single platform, SUSPS provides structured outputs such as growth forecasts, energy demand profiles, and congestion patterns that can directly inform infrastructure investment decisions and urban development policies.
- **Sustainable urban development.** The ability to simulate alternative scenarios and forecast future demand helps planners anticipate where infrastructure and services are likely to be most needed. This supports more sustainable allocation of limited resources and aligns with national development agendas and global goals such as SDG 11 (Sustainable Cities and Communities).
- **Technical and academic contribution.** The project contributes to the relatively small but growing body of empirical work on smart cities and urban analytics in Sub-Saharan Africa. Methodologically, it demonstrates how open datasets and modern web technologies can be combined into a reproducible urban simulation platform tailored to an African context.
- **Practical benefits for communities.** In the longer term, better-informed planning decisions can translate into improved access to transport, more reliable energy supply, and better-managed urban growth, improving the daily lives of citizens.

## 1.3 Scope of the Study

The scope of this work is deliberately focused on urban-scale analysis rather than national-level planning or detailed economic modelling. Key scope elements are:

- Spatial focus on a single metropolitan area, with Lusaka as the intended deployment city and Nairobi used as the demonstration environment for the prototype.
- Thematically, the system concentrates on three interrelated domains: urban growth, energy demand, and traffic flow, complemented by environmental and hotspot analysis.
- Technically, the project delivers a working web-based prototype that includes a backend API, a frontend dashboard, and a reproducible data pipeline. The system is capable of running locally and on a cloud platform (Render) using free or free-tier services.

The study does not attempt to build full-scale operational control systems for utilities or transport agencies, nor does it develop detailed microsimulation models of individual vehicles or household behaviour. Instead, it focuses on lightweight but interpretable models and interfaces that can be extended in future work.

## 1.4 Problem Statement

Unplanned and rapidly expanding urban development in Zambia has led to challenges such as traffic congestion, unreliable energy supply, and inefficient land use. Existing planning methods are often reactive, fragmented across sectors, and based on outdated or isolated datasets. This makes it difficult for urban planners and policymakers to anticipate emerging problems, evaluate alternative scenarios, and design coordinated interventions. The core problem addressed in this project is the lack of an integrated, data-driven urban simulation platform that can combine demographic, mobility, energy, and environmental information into predictive insights to support sustainable planning in Lusaka and similar cities.

## 1.5 Objectives

### 1.5.1 General Objective

To design and implement a Smart Urban Simulation and Prediction System (SUSPS) that integrates demographic, mobility, and environmental data to predict urban growth, forecast energy demand, and approximate traffic flows for an urban area, with an intended deployment in Lusaka and a demonstration implementation using Nairobi data.

### 1.5.2 Specific Objectives

The specific objectives of the study are to:

1. Analyse demographic and population growth trends using census and geospatial data, and derive urban growth forecasts for the study area.
2. Forecast future energy demand based on population projections, settlement patterns, and processed energy features.
3. Model daily traffic flow profiles using transport and mobility datasets, including the identification of congestion-prone periods and corridors.
4. Design and implement a web-based prototype that exposes these predictions through a FastAPI backend and a React SPA, including simulation and advisory functionality.
5. Evaluate the system’s effectiveness in addressing key urban planning questions, particularly those related to growth hotspots, energy demand, and traffic management.

## 1.6 Research Questions

The study is guided by the following research questions:

1. How can demographic and census data be integrated with gridded and geospatial datasets to produce urban growth predictions suitable for planning in Lusaka and similar cities?
2. What are the likely energy demand profiles for an urban area under different growth and land-use scenarios, and how can these profiles be approximated from available datasets?
3. How can mobility and transport data be used to approximate traffic flow patterns and identify congestion hotspots in a way that is feasible for data-constrained African cities?
4. What system architecture and technology stack are most appropriate for implementing an AI-assisted urban simulation platform that remains maintainable on free or low-cost infrastructure?
5. How effective is the SUSPS prototype, as implemented, in providing insights that respond to the identified urban planning challenges and to the needs of stakeholders such as planners and policymakers?

## 1.7 Conceptual/Theoretical Framework

The conceptual foundation for this work draws primarily on systems theory and smart city frameworks. Systems theory views the city as a collection of interrelated subsystems—population, transport, energy, environment—where changes in one component can propagate to others (Skyttner, 2005). This perspective motivates the integration of diverse datasets into a single modelling and simulation pipeline rather than treating each domain in isolation.

Smart city frameworks emphasise the role of information and communication technologies, data analytics, and citizen engagement in promoting sustainable and resilient urban development (Albino et al., 2015; Hollands, 2008; Kitchin, 2014; Townsend, 2013). Within this study, SUSPS is positioned as a data and analytics layer within a broader smart city vision: it brings together demographic, mobility, energy, and environmental information to generate indicators, forecasts, and advisory text that can support evidence-based decision making.

Conceptually, SUSPS implements a loop that starts with data acquisition (ingest), proceeds through processing and feature engineering, generates predictions and simulations, and then exposes results to human decision-makers via dashboards and advisory content. Feedback from stakeholders and real-world outcomes can then be used to refine models and parameters, closing the loop.

## 1.8 Definition of Terms

For the purposes of this study, the following terms are defined as follows:

- **Smart city:** An urban area that uses digital technologies, data, and analytics to improve the efficiency of services, support sustainable development, and enhance quality of life.
- **Simulation:** The representation of real-world processes or systems over time using computational models, allowing “what-if” scenarios to be explored without intervening directly in the real system.
- **Prediction:** The use of statistical or machine learning models to estimate future conditions from historical and current data.
- **Geospatial data:** Data that include a geographic component such as coordinates, geometries, or raster cells, enabling spatial analysis and mapping.
- **Mobility data:** Information describing the movement of people or vehicles, including traffic counts, GPS traces, public transport routes, and timetables.
- **Hotspot:** In this context, a spatial unit or area exhibiting high combined risk or intensity (for example, high population density, high congestion, or high energy stress) relative to other units.
- **Advisory engine:** The component of SUSPS that translates quantitative outputs (time series, hotspots, forecasts) into structured narrative guidance for planners and policymakers using rule-based logic and, when configured, AI summarisation.

## 1.9 Organization of the Report

The remainder of this report is organised as follows:

- **Chapter Two** presents a review of literature on smart cities, urban simulation, traffic flow modelling, and energy demand forecasting, with emphasis on Sub-Saharan African and Zambian contexts. It also discusses related systems and identifies gaps that SUSPS aims to address.
- **Chapter Three** describes the methodology adopted in this study, including the research design, baseline study, data collection, and system design. It introduces the main architectural diagrams, class and data models used in SUSPS.
- **Chapter Four** presents the results of the baseline study, summarises testing activities and data analysis, and discusses the main findings produced by the implemented system.
- **Chapter Five** focuses on the implementation of SUSPS, detailing the backend, frontend, data pipeline, advisory engine, and deployment processes, and discussing how the system functions as a solution to the identified problem.
- **Chapter Six** concludes the study by summarising key findings, outlining implications for practice and policy, presenting recommendations, and proposing directions for future work.

---

# CHAPTER TWO: LITERATURE REVIEW

## 2.0 Overview

This chapter reviews existing research and practice relevant to the Smart Urban Simulation and Prediction System (SUSPS). It is organised into three main sections. Section 2.1 provides a thematic review of literature on smart cities, urban simulation and modelling, traffic flow prediction, and energy demand forecasting, with emphasis on methods and findings that inform this project. Section 2.2 discusses related systems and platforms that implement similar ideas in different contexts. Section 2.3 identifies gaps in the literature and practice, particularly in relation to Zambian and Sub-Saharan African cities, and highlights how SUSPS is designed to address these gaps.

## 2.1 Review of the Literature

### 2.1.1 Smart cities and urban growth

The smart city concept has gained prominence as cities seek to harness information and communication technologies (ICT) and data analytics to improve service delivery, sustainability, and citizen engagement (Albino et al., 2015; Batty, 2018). Studies emphasise that smart cities are not defined solely by technology, but by how technology is integrated with governance, planning, and social objectives (Hollands, 2008; Townsend, 2013). International examples such as Singapore, Barcelona, and Amsterdam illustrate how data-driven platforms can be used to optimise transport netwIn Sub-Saharan Africa, smart city initiatives are emerging but are often fragmented and limited in scope. Pilot projects may focus on traffic monitoring, smart meters, or digital land administration, but rarely integrate multiple domains into a coherent analytics framework (UN-Habitat, 2020; World Bank, 2021). Zambia, like many countries in the region, is still at an early stage in adopting such tools. This context underscores the relevance of SUSPS as a prototype that demonstrates how openly available data and modern software architectures can be combined to support urban planning.

### 2.1.2 Urban simulation and modelling

Urban simulation models have long been used in planning practice to explore how cities might evolve under different policy or development scenarios. Approaches include land-use transport interaction models, agent-based models, and cellular automata (Waddell, 2002; Silva and Clarke, 2002; Wegener, 2011; Batty, 2013). These frameworks aim to capture the interactions of population, economic activities, transport networks, and land-use change over time. In many high-income contexts, such models are supported by extensive datasets and institutional capacity.

In African cities, however, data limitations and resource constraints have often prevented the use of complex simulation platforms (Lemmens et al., 2017). Recent work has highlighted the potential of combining open geospatial datasets (such as WorldPop gridded population data and OpenStreetMap layers) with lighter-weight modelling approaches that are more appropriate for data-scarce settings. SUSPS follows this direction by applying simple but interpretable models for population growth and settlement expansion, supported by a reproducible pipeline that can be re-run as new data become available.

### 2.1.3 Traffic flow prediction and mobility analytics

Traffic congestion is a pervasive challenge in rapidly growing cities. Research has explored a spectrum of methods for predicting traffic conditions, ranging from classical time-series models to machine learning and deep learning techniques (Vlahogianni et al., 2014; Lv et al., 2015; Zheng et al., 2014). These methods use inputs such as historical traffic counts, GPS traces, public transport timetables, incident reports, and weather data to estimate flows, speeds, and congestion levels (Litman, 2021).

In practice, global platforms such as Google Maps and research initiatives like the Digital Matatus project in Nairobi have shown how GTFS feeds and crowdsourced mobility data can be transformed into usable information for planners and the public (Williams et al., 2015). For Lusaka and similar cities, detailed mobility datasets may not yet be available at the same scale, but simplified models and proxies—such as daily profiles derived from limited samples or analogous cities—can still provide useful insights. SUSPS adopts a pragmatic approach: it uses processed traffic features and, when configured, external APIs (e.g. TomTom) to build representative daily profiles and approximate congestion patterns rather than full microsimulation of vehicles.

### 2.1.4 Energy demand forecasting

Energy demand in urban areas is shaped by population, economic structure, housing characteristics, climate, and technology adoption. A large body of work has examined approaches for forecasting energy demand at various scales, from individual buildings through to national grids (International Energy Agency, 2019; Deb et al., 2017). Techniques include regression models, decomposition methods, time-series forecasting (e.g. ARIMA, exponential smoothing), and machine learning approaches such as neural networks and ensemble methods (Ghosh et al., 2018; Hyndman and Athanasopoulos, 2018). Best practice emphasises the use of explanatory variables such as temperature and humidity, and the evaluation of forecasting accuracy using robust error metrics.

In Zambia, frequent power shortages and load shedding highlight the need for better tools to anticipate demand and plan supply-side investments (International Energy Agency, 2019). However, detailed interval consumption data and advanced metering infrastructure are not yet universal. SUSPS therefore focuses on generating indicative daily and hourly profiles of energy demand based on processed energy features and demographic information, rather than attempting to model the full national grid. The time-series forecasting component of SUSPS is kept lightweight and interpretable, and can optionally be enhanced with free-tier AI models where connectivity and quotas permit.

### 2.1.5 Integrated urban analytics

Recent literature has argued for more integrated approaches that cut across traditional sectoral boundaries. Urban computing and urban analytics frameworks propose combining data from mobility, environment, land use, social media, and infrastructure systems to support holistic decision making (Zheng et al., 2014; Batty, 2013). These approaches often rely on cloud platforms, scalable data pipelines, and advanced analytics methods, which can pose challenges for resource-constrained cities.

SUSPS can be viewed as a step towards such an integrated analytics environment for Lusaka. It combines growth, energy, traffic, and environmental indicators in a single backend, and exposes them through a coherent user interface. While the models are deliberately kept simple, the system architecture is modular and extensible, providing a foundation for future integration of more advanced analytics.

## 2.2 Related Works

Several systems and projects provide useful reference points for SUSPS:

- **Digital Matatus (Nairobi).** This project demonstrated how informal public transport networks can be digitised using GTFS standards and mobile data. It provides a model for how mobility datasets can be created and used in contexts with informally organised transport services.
- **Urban simulation platforms such as UrbanSim.** These frameworks integrate land use, transport, and environmental models to explore long-term development scenarios. They illustrate the value of scenario-based planning and the importance of reproducible pipelines and model calibration.
- **Energy forecasting tools.** A range of academic and applied systems implement building-level and city-level energy demand forecasting using time-series and machine learning methods. These demonstrate the potential of combining historical consumption, weather data, and socio-economic variables to support energy planning.

While these systems have been influential, they are often developed for data-rich environments and may assume institutional and technical capacities that are not yet present in many African cities. SUSPS takes inspiration from their modular architectures and emphasis on reproducibility, but adapts the design to rely primarily on open datasets and simple, explainable models that can operate within free-tier resource constraints.

## 2.3 Gaps in the Literature

The literature and practice reviewed above suggest several gaps that this project seeks to address:

1. **Lack of integrated platforms for African cities.** Many existing initiatives focus on a single domain—transport, energy, or population—but do not provide a unified platform that links these domains together for integrated planning. SUSPS explicitly combines growth, energy, and traffic analyses, along with hotspots and advisory outputs, in one system.
2. **Data and capacity constraints.** Established urban modelling platforms typically assume extensive, high-quality datasets and significant institutional capacity. In contrast, Lusaka and similar cities often face sparse or inconsistent data, limited computational resources, and constraints on paid services. SUSPS is therefore designed around open datasets, lightweight models, and free or free-tier tools.
3. **Limited localisation of models.** Many smart city and urban analytics tools are developed in high-income contexts and transferred with minimal adaptation to African cities. This can lead to models that do not reflect local mobility patterns, settlement structures, or institutional realities. SUSPS emphasises configuration for the Lusaka context and uses Nairobi primarily as a data-rich stand-in for prototyping and evaluation.
4. **Bridging analytics and decision making.** A further gap lies in translating model outputs into forms that planners and policymakers can readily use. Technical dashboards and raw indicators may not be sufficient to guide decisions. By including an advisory engine that explains patterns and risks in narrative form, SUSPS takes a step towards bridging this gap and making analytics more accessible to non-technical stakeholders.

These gaps motivate the design choices made in SUSPS and provide criteria for evaluating how well the system contributes to improving urban planning practice in Lusaka and, by extension, similar cities in the region.

---

# CHAPTER THREE: METHODOLOGY

## 3.0 Overview

This chapter describes the methodological framework used to design, develop, and evaluate the Smart Urban Simulation and Prediction System (SUSPS). The work follows a design science approach focused on building and assessing an artefact that addresses a clearly defined practical problem (Pressman, 2010; Sommerville, 2011). Quantitative analysis of demographic, mobility, energy, and environmental datasets is combined with simulation modelling and iterative prototyping of a web-based system.

The chapter is organised as follows. Section 3.1 outlines the overall research design. Section 3.2 explains the baseline study, including data collection and the research approach taken to manage the use of Nairobi as a demonstration environment for a system intended for Lusaka. Section 3.3 presents the system design, including the main architectural views required by the Cavendish guidelines: context diagram, software architecture, modular design of system functions, class diagram, and data model design.

## 3.1 Research Design

The study adopts a design science research design, structured around the development and evaluation of a software artefact that supports urban planning decisions. The core elements of this design are:

- **Problem identification and motivation.** The initial stages of the work identified the limitations of existing planning processes in Lusaka and similar cities, drawing on reports and literature that highlight congestion, energy constraints, and unmanaged urban expansion (UN-Habitat, 2020; World Bank, 2021).
- **Definition of objectives for a solution.** Based on the problem statement and literature, objectives were defined around integrating heterogeneous datasets, providing interpretable forecasts of growth, energy demand, and traffic flows, and packaging these outputs in a form suitable for planners and policymakers.
- **Design and development of the artefact.** SUSPS was designed and implemented as a web-based system combining a FastAPI backend, a React single-page frontend, a Python data pipeline, and an optional PostgreSQL/PostGIS database.
- **Demonstration and evaluation.** The system was exercised on Nairobi data as a proxy for Lusaka, producing baseline outputs and simulation scenarios. Testing activities—both automated and manual—were used to verify correctness, performance, and usability.
- **Communication of results.** The outcomes and lessons learned are documented in this report and can be shared with technical and non-technical stakeholders.

The design is iterative rather than strictly sequential. Requirements were refined as the prototype evolved, with feedback from data availability, implementation constraints, and evaluation results informing subsequent design decisions (Pressman, 2010; Sommerville, 2011).

## 3.2 Baseline Study

The baseline study establishes the empirical context for SUSPS and provides the datasets used for model calibration, testing, and demonstration. Because comprehensive, high-resolution datasets for Lusaka are not yet available in all domains, Nairobi is used as the primary demonstration city in this phase. Nairobi offers richer open data, particularly for mobility and traffic (Williams et al., 2015), while sharing several structural similarities with Lusaka such as rapid growth, significant informal transport, and mixed land-use patterns.

The baseline study therefore has two complementary aims:

1. To assemble a coherent set of datasets covering demographics, mobility, energy, environment, and socio-economic conditions for Nairobi, processed into formats suitable for SUSPS.
2. To design the data pipeline, models, and interfaces so that they can be reparameterised for Lusaka once the required datasets become available.

### 3.2.1 Data Collection

Data collection for SUSPS builds on the sources identified in the proposal, complemented by specific open datasets and APIs assembled during implementation. The main categories of data are:

- **Demographics and population.** Gridded population datasets from WorldPop and GRID3 provide fine-scale estimates of population density and distribution, while city-level census and population time series (for example, Nairobi population statistics compiled by Macrotrends) supply historic totals and growth trends. These layers are ingested into the pipeline and aggregated by urban units (e.g., wards or analysis zones) to support growth modelling, hotspot identification, and validation of forecasts.
- **Mobility and transport.** Transport and traffic data are obtained from several complementary sources. Matatu route shapefiles from the Digital Matatus project describe informal public transport corridors, OpenStreetMap road network extracts downloaded as Geofabrik Kenya `.pbf` files provide a complete representation of the road network, and, where configured, TomTom Traffic API endpoints contribute speed and congestion indicators. These inputs, together with representative daily profiles stored in `traffic_flows`-style CSVs, are normalised into consistent hourly traffic profiles and corridor-level indicators.
- **Energy and infrastructure.** Energy access and usage data are primarily taken from the Africa Energy Portal and related open repositories, providing country and city-level statistics on electricity access, generation, and consumption. These statistics are combined with demographic information to derive typical daily and sectoral demand profiles, which are stored in processed artefacts such as energy feature tables and used as baselines for the energy forecasting module (International Energy Agency, 2019; Deb et al., 2017).
- **Environment, climate, and land cover.** Weather and climate variables (e.g., temperature and precipitation) are obtained from the OpenWeather API, while air-quality indicators such as PM2.5 and PM10 are sourced from OpenAQ and curated CSV datasets from initiatives such as AirQo. Land cover and urban change are characterised using land-cover rasters such as the ICPAC Kenya land-cover dataset, complemented by global settlement footprint layers from GRID3. These datasets support environmental feature construction and the analysis of exposure and risk.
- **Socio-economic, smart-city, and hotspot indicators.** Additional indicators of urban growth and infrastructure, including global settlement footprint layers and related GRID3 products, are used to characterise built-up areas, accessibility, and potential hotspots. These are combined with demographic and mobility features to produce hotspot areas and hotspot forecasts that rank local units by combined indicators such as population pressure, access to transport, and inferred service levels.

All datasets are ingested through the SUSPS pipeline, which performs extraction, transformation, and loading steps: raw files and API responses are normalised to standard CSV or GeoJSON formats, missing values are handled using simple imputation schemes, and derived variables (features) are computed for use in models (Lemmens et al., 2017). The pipeline is designed to be rerunnable so that updated raw data can be propagated through to new model runs.

### 3.2.2 Research Approach

The research approach is iterative and incremental, influenced by agile software engineering practices. Rather than treating data collection, modelling, and system development as isolated phases, the project cycles through the following activities:

1. **Dataset acquisition and profiling.** Candidate datasets are collected, profiled for quality and coverage, and integrated into the pipeline in a minimal form.
2. **Prototype modelling.** Simple baseline models for growth, energy demand, and traffic flows are implemented and exercised on the available data. For example, growth models may use linear trends over census years, while traffic models start from representative daily profiles (Wegener, 2011; Vlahogianni et al., 2014).
3. **System integration.** The models are exposed via the FastAPI backend and visualised in the React frontend, allowing stakeholders to see preliminary outputs and interactions between components.
4. **Evaluation and refinement.** Automated tests and exploratory analysis are used to validate the correctness and plausibility of outputs. Issues discovered at this stage may lead to changes in data cleaning rules, model parameters, or interface design.
5. **Documentation and consolidation.** Each iteration concludes with updates to documentation and configuration, ensuring that the system remains reproducible and that its behaviour is well understood.

This cyclical approach allows the system to evolve as data availability and understanding of the problem improve, while maintaining a clear audit trail of design decisions (Pressman, 2010; Sommerville, 2011).

## 3.3 System Design

The system design translates the methodological objectives into a concrete software architecture. It ensures that SUSPS can ingest and process heterogeneous datasets, run growth, energy, and traffic models, and expose outputs via a web interface that is usable by planners and policymakers. The subsections below correspond to the design views required in the thesis guidelines.

### 3.3.1 Context Diagram

The context diagram presents SUSPS as a single logical system interacting with external actors and data sources. Externally, SUSPS connects to:

- **Data providers:** open geospatial repositories (e.g., WorldPop, OpenStreetMap), weather and air-quality APIs, and mobility data providers in the demonstration environment.
- **Urban planners and policy analysts:** who access the system through the web-based dashboard to explore growth forecasts, energy demand profiles, traffic patterns, and hotspot maps.
- **Researchers:** who may export processed datasets and model outputs for further analysis in external tools.
- **System administrators:** who configure environment variables, manage data refreshes, and oversee deployment.

In the context diagram (Figure 3.1), these external entities appear as nodes connected to the central SUSPS system. Arrows indicate the flow of data into SUSPS (e.g., raw population and mobility data) and information out of SUSPS (e.g., forecasts, advisory narratives, and export files).

### 3.3.2 System Software Level Architectural Design

At the software architecture level, SUSPS is organised into several layers and components:

- **Presentation layer (frontend).** A React single-page application renders dashboards and maps for urban growth, energy, traffic, and hotspots. It communicates with the backend exclusively via RESTful API calls.
- **API layer (backend).** A FastAPI application defines endpoints for growth, energy, traffic, environment, hotspots, simulation, time-series forecasting, authentication, and advisory. It handles request validation, orchestration of domain logic, and formatting of responses.
- **Domain and service layer.** This layer contains the core business logic: growth prediction helpers, time-series forecasting utilities, simulation functions for growth/energy/traffic, and advisory-generation routines. It represents the central rules for how data are combined and transformed into outputs.
- **Data access and storage layer.** When database mode is enabled, SUSPS uses PostgreSQL with PostGIS to store urban areas, energy consumption, traffic flows, environment and air-quality series, hotspot scores, and user accounts. When database mode is disabled, the system reads from processed CSV artefacts. In both cases, the data access layer presents a consistent interface to the domain layer.
- **Data pipeline and batch layer.** Separate Python modules perform scheduled or ad-hoc ingest and preprocessing of raw datasets, writing derived artefacts into canonical `raw` and `processed` directories. These modules can be invoked locally or, in a cloud deployment, as part of a bootstrap process.

Figure 3.2 (software architecture diagram) illustrates these components and their interactions. Figure 3.3 extends this view to show how the components are deployed locally and on Render.

### 3.3.3 Modular Design of the System Functions

SUSPS is decomposed into functional modules to support maintainability, testability, and future extension. Key modules include:

- **Ingestion and ETL module.** Responsible for fetching raw data from files and APIs, validating formats, performing basic cleaning, and writing canonical raw artefacts.
- **Preprocessing and feature-engineering module.** Aggregates and transforms raw data into feature tables suitable for modelling, including traffic features, energy features, environmental and air-quality features, and hotspot indicators.
- **Prediction and simulation module.** Implements deterministic and, where configured, AI-assisted models for growth forecasts, energy demand profiles, and traffic flows. It also includes a SIMULATE engine that applies parameterised adjustments to baseline series for scenario analysis.
- **Advisory module.** Compiles model outputs and context into short narrative advisories for growth, energy, traffic, and overall dashboard views, optionally using free-tier AI models for text generation when an API key is configured.
- **API and authentication module.** Exposes a REST API over HTTP, manages CORS, and implements basic authentication and user management when database support is enabled.
- **User interface module.** The React SPA renders charts, tables, maps, and advisory text, and handles user interactions such as selecting areas, running simulations, and exporting reports.

Each module has a clearly defined responsibility and interacts with others through well-specified interfaces. This modular design makes it easier to swap out or extend individual models (for example, replacing a deterministic time-series forecaster with a more advanced one) without restructuring the entire system.

### 3.3.4 System Class Diagram

The system class diagram captures the main domain entities and their relationships. While the exact implementation details are defined in the database schema and model classes, the core conceptual entities include:

- **User.** Represents authenticated users of the system, with attributes such as identifier, email, name, role, and timestamps for account creation.
- **UrbanArea.** Represents spatial units such as wards or analysis zones, including an identifier, name, type, and geometry.
- **Demographics.** Represents population and demographic attributes for regions or areas, including population counts and age/gender distributions by census year.
- **EnergyConsumption.** Stores time-stamped energy demand values (predicted and, when available, actual) for each area.
- **TrafficFlow.** Stores time-stamped traffic volumes, and optionally congestion levels, for each area or corridor.
- **EnvironmentFeature and AirQualityDaily.** Capture environmental and air-quality indicators such as temperature, rainfall, and pollution metrics.
- **UrbanGrowthPrediction.** Stores forecasts of population and land-use change for each area and prediction date.
- **HotspotScore.** Stores combined hotspot indicators and scores for different areas and years.
- **SimulationRun.** Represents simulation scenarios executed through the `/simulate/run` endpoint, including parameters and summarised results.

In the class diagram, associations indicate how these entities relate—for example, an UrbanArea has many EnergyConsumption and TrafficFlow records; a User initiates many SimulationRun instances. These relationships are reflected in the underlying database through foreign keys and constraints.

### 3.3.5 System Data Model Design

The data model design specifies how the conceptual classes are mapped into relational tables and, where appropriate, spatial and JSON fields. Key aspects include:

- **Relational structure.** Tables for users, urban areas, demographics, energy consumption, traffic flows, environment features, air-quality series, hotspot scores, and simulation runs. Primary keys ensure uniqueness, and foreign keys link child tables to their parent entities (e.g., `area_id` in energy and traffic tables referring to the primary key of urban areas).
- **Spatial representation.** The geometry of urban areas is stored using PostGIS-compatible geometry types, enabling spatial queries such as intersection, buffering, and area calculations where database mode is enabled.
- **Temporal and series data.** Time-varying measurements use date, time, or timestamp fields, allowing time-series operations and filtering by period.
- **Flexible attributes.** JSON fields are used for attributes that vary in structure or are sparsely populated, such as route descriptions, simulation parameters, and simulation results.
- **Indexes and optimisation.** Appropriate B-tree and spatial indexes are defined on key columns (e.g., identifiers, timestamps, geometry fields) to support efficient queries from the API and pipeline.

Figure 4.1 (database entity–relationship diagram) visualises this data model, showing entities as tables with their main fields and the cardinalities of the relationships between them.

### 3.3.6 Database Schema

This subsection specifies the relational schema implemented in the current SUSPS system. Core tables include Users, Areas, Urban Areas (legacy), Processed Data, Simulation Inputs, Energy Consumption, Traffic Flow, Environment Features, Air Quality Daily, and Hotspot Scores. Time-series measures use timestamped fields, and JSONB fields capture flexible attributes such as parameters, results, and metadata. The baseline schema is defined using SQL DDL in `src/backend/db/susps_schema_dump.sql` and mapped to ORM models in `src/backend/db/tables.py`. Optional geometry columns may be added via separate migrations in deployments that enable PostGIS, but they are not created by default in the provided schema dump.

The layout below follows the structure of the original proposal but reflects the final implemented schema.

### 1. Users

Stores information about users interacting with the system.

| Column Name    | Data Type       | Constraints                 | Description                          |
| -------------- | --------------- | --------------------------- | ------------------------------------ |
| id             | BIGSERIAL       | PRIMARY KEY                 | Unique user identifier               |
| email          | VARCHAR(255)    | NOT NULL, UNIQUE            | User email address                   |
| full_name      | VARCHAR(255)    | NULL                        | Full name of the user                |
| hashed_password| VARCHAR(255)    | NULL                        | Hashed password (when auth enabled)  |
| created_at     | TIMESTAMPTZ     | NULL                        | Account creation timestamp           |
| updated_at     | TIMESTAMPTZ     | NULL                        | Last update timestamp                |

### 2. Areas

Represents logical analysis areas (city, ward, neighbourhood, corridor, etc.) used as anchors for processed data and simulations.

| Column Name  | Data Type    | Constraints              | Description                            |
| ------------ | ------------ | ------------------------ | -------------------------------------- |
| id           | BIGSERIAL    | PRIMARY KEY              | Unique area identifier                 |
| name         | VARCHAR(150) | NOT NULL                 | Area name                              |
| area_type    | VARCHAR(50)  | NOT NULL, DEFAULT 'city' | Area type (e.g., city, ward, corridor) |
| description  | TEXT         | NULL                     | Free-text description of the area      |
| boundary_hint| TEXT         | NULL                     | Textual or GeoJSON boundary hint       |
| created_at   | TIMESTAMPTZ  | NULL                     | Record creation timestamp              |
| updated_at   | TIMESTAMPTZ  | NULL                     | Last update timestamp                  |

### 3. Urban Areas (legacy)

Legacy table retained for backward compatibility with earlier prototypes and DB experiments.

| Column Name | Data Type    | Constraints | Description            |
| ----------- | ------------ | ----------- | ---------------------- |
| area_id     | BIGSERIAL    | PRIMARY KEY | Legacy area identifier |
| name        | VARCHAR(100) | NOT NULL    | Legacy area name       |
| area_type   | TEXT         | NOT NULL    | Legacy area type       |

### 4. Processed Data

Registers processed datasets (growth, energy, traffic, environment, etc.) associated with areas and modes (REAL/SIMULATE).

| Column Name  | Data Type    | Constraints                        | Description                                       |
| ------------ | ------------ | ---------------------------------- | ------------------------------------------------- |
| id           | BIGSERIAL    | PRIMARY KEY                        | Unique processed-data record                      |
| area_id      | BIGINT       | NOT NULL, FK -> areas(id)          | Area linked to this processed dataset             |
| mode         | VARCHAR(20)  | NOT NULL, DEFAULT 'REAL'           | Data mode (e.g., REAL, SIMULATE)                  |
| category     | VARCHAR(50)  | NOT NULL                           | Data category (e.g., growth, energy, traffic)     |
| version      | VARCHAR(50)  | NULL                               | Version or run identifier                         |
| storage_path | TEXT         | NULL                               | Path or key to stored artefact (CSV/GeoJSON/etc.) |
| meta         | JSONB        | NULL                               | JSON metadata (schema, stats, provenance)         |
| created_at   | TIMESTAMPTZ  | NULL                               | Registration timestamp                            |

### 5. Simulation Inputs

Captures user-defined simulation scenarios and parameter sets used by SIMULATE mode.

| Column Name | Data Type    | Constraints                        | Description                                      |
| ----------- | ------------ | ---------------------------------- | ------------------------------------------------ |
| id          | BIGSERIAL    | PRIMARY KEY                        | Unique simulation-input record                   |
| area_id     | BIGINT       | NOT NULL, FK -> areas(id)          | Area to which the simulation primarily relates   |
| user_id     | BIGINT       | NULL, FK -> users(id)              | User who created the scenario                    |
| name        | VARCHAR(150) | NOT NULL                           | Human-readable scenario name                     |
| parameters  | JSONB        | NULL                               | JSON payload of simulation parameters            |
| file_path   | TEXT         | NULL                               | Optional path to associated uploaded file        |
| created_at  | TIMESTAMPTZ  | NULL                               | Scenario creation timestamp                      |

### 6. Energy Consumption

Stores time-series energy demand values (predicted and, when available, actual) by urban area.

| Column Name       | Data Type    | Constraints                             | Description                                  |
| ----------------- | -----------  | --------------------------------------- | -------------------------------------------- |
| energy_id         | BIGSERIAL    | PRIMARY KEY                             | Unique energy record                         |
| area_id           | BIGINT       | FK -> urban_areas(area_id), NULLABLE    | Legacy area reference                        |
| ts                | TIMESTAMPTZ  | NOT NULL                                | Timestamp of record                          |
| predicted_demand  | DOUBLE PRECISION | NULL                                | Predicted energy demand (e.g., MWh)          |
| actual_demand     | DOUBLE PRECISION | NULL                                | Actual energy consumption (when available)    |

### 7. Traffic Flow

Stores time-series traffic volume values (predicted and, when available, actual) by urban area.

| Column Name       | Data Type       | Constraints                             | Description                                  |
| ----------------- | --------------- | --------------------------------------- | -------------------------------------------- |
| traffic_id        | BIGSERIAL       | PRIMARY KEY                             | Unique traffic record                        |
| area_id           | BIGINT          | FK -> urban_areas(area_id), NULLABLE    | Legacy area reference                        |
| ts                | TIMESTAMPTZ     | NOT NULL                                | Timestamp of record                          |
| predicted_volume  | INTEGER         | NULL                                     | Predicted traffic volume (vehicles/hour)     |
| actual_volume     | INTEGER         | NULL                                     | Actual measured volume (when available)      |
| congestion_level  | TEXT            | NULL                                     | Qualitative congestion label (e.g., low/high)|

### 8. Environment Features

Monthly environment and air-quality summary features used by analytics and advisory components.

| Column Name      | Data Type       | Constraints                        | Description                                  |
| ---------------- | --------------- | ---------------------------------- | -------------------------------------------- |
| id               | BIGSERIAL       | PRIMARY KEY                        | Unique environment-feature record            |
| area_id          | BIGINT          | NULL, FK -> areas(id)              | Area identifier (NULL for city-wide rows)    |
| month            | INTEGER         | NOT NULL                           | Month index (1–12)                           |
| temp_c           | DOUBLE PRECISION| NULL                               | Mean temperature (°C)                        |
| rain_mm          | DOUBLE PRECISION| NULL                               | Monthly rainfall (mm)                        |
| cooling_deg      | DOUBLE PRECISION| NULL                               | Cooling degree indicator                     |
| wet_month        | INTEGER         | NULL                               | Wet-month flag (1 = wet, 0 = dry)           |
| pm25             | DOUBLE PRECISION| NULL                               | Mean PM2.5 concentration                     |
| pm10             | DOUBLE PRECISION| NULL                               | Mean PM10 concentration                      |
| o3               | DOUBLE PRECISION| NULL                               | Mean O₃ concentration                        |
| pollution_index  | DOUBLE PRECISION| NULL                               | Normalised pollution index (0–1)            |

### 9. Air Quality Daily

Daily air-quality aggregates for key pollutants.

| Column Name | Data Type        | Constraints                        | Description                               |
| ----------- | ---------------- | ---------------------------------- | ----------------------------------------- |
| id          | BIGSERIAL        | PRIMARY KEY                        | Unique daily air-quality record           |
| area_id     | BIGINT           | NULL, FK -> areas(id)              | Area identifier (NULL for city-wide rows) |
| date        | DATE             | NOT NULL                           | Calendar date                             |
| pm25        | DOUBLE PRECISION | NULL                               | Daily mean PM2.5                          |
| pm10        | DOUBLE PRECISION | NULL                               | Daily mean PM10                           |
| o3          | DOUBLE PRECISION | NULL                               | Daily mean O₃                             |

### 10. Hotspot Scores

Area-level hotspot and optimal-zone indicators derived from processed pipeline outputs.

| Column Name      | Data Type        | Constraints                        | Description                                   |
| ---------------- | ---------------- | ---------------------------------- | --------------------------------------------- |
| id               | BIGSERIAL        | PRIMARY KEY                        | Unique hotspot-score record                   |
| area_id          | BIGINT           | NULL, FK -> areas(id)              | Area identifier (NULL for city-wide rows)     |
| admin_unit       | VARCHAR(150)     | NULL                               | Name of administrative or analysis unit       |
| year             | INTEGER          | NULL                               | Year of hotspot score                         |
| population       | DOUBLE PRECISION | NULL                               | Population in the unit                        |
| pop_share        | DOUBLE PRECISION | NULL                               | Share of total city population                |
| income_norm      | DOUBLE PRECISION | NULL                               | Normalised income indicator (0–1)             |
| employment_score | DOUBLE PRECISION | NULL                               | Employment-related score                      |
| hotspot_score    | DOUBLE PRECISION | NULL                               | Composite hotspot score (0–1, higher = worse) |

### 3.3.7 Use-Case Diagram

The SUSPS use-case view highlights the main actors—urban planners, policy analysts, researchers, and system administrators—and the core interactions they have with the system. Key use-cases include selecting an area, exploring dashboards, running simulations, generating and exporting reports, and managing access.

[Figure 3.4: SUSPS use-case diagram – to be inserted here, showing actors and primary use-cases such as "Ingest Data", "Run Simulations", "Explore Scenarios", "Generate Reports", "Export Datasets", and "Manage Access".]

### 3.3.8 Dependency Diagram

The dependency view shows how high-level components depend on one another, including the data pipeline (ingest and preprocess modules), the domain and prediction services, the FastAPI layer, the React frontend, the PostgreSQL/PostGIS database, and optional object storage used for raw and processed artefacts.

[Figure 3.5: SUSPS dependency diagram – to be inserted here, indicating build- and run-time dependencies between the pipeline, prediction services, API layer, frontend, database, and storage.]

### 3.3.9 General Flowchart

A general flowchart summarises the end-to-end processing logic from data ingestion through to stakeholder-facing outputs and feedback. It starts with ingesting and cleaning raw datasets, proceeds through feature engineering and model execution (forecasting and simulation), and concludes with visualisation, report generation, and an evaluation loop.

[Figure 3.6: General flowchart for SUSPS – to be inserted here, outlining steps such as "Ingest raw data", "Validate & clean", "Feature engineering", "Generate forecasts", "Visualise dashboards", "Export reports", and "Feedback & evaluation".]

### 3.3.10 Additional UML Diagrams

In addition to the context, architecture, class, and data-model views already described, two further UML-style diagrams are relevant for SUSPS.

**Activity diagram.** The activity view follows the main processing pipeline from ingest and preprocessing through model execution to UI rendering and export. It emphasises branching between training and inference modes and the role of evaluation-fed configuration updates.

[Figure 3.7: SUSPS activity diagram – to be inserted here, detailing ETL, modelling, UI/reporting, and governance activities.]

**Deployment diagram (Render).** The deployment view describes how SUSPS is hosted in practice: a Render web service for the FastAPI backend (running Gunicorn + Uvicorn workers), a Render static site for the built React frontend, an optional Render-managed PostgreSQL/PostGIS instance holding the schema described above, and object storage (such as S3) mirroring the `data/<CITY>/raw/` tree used by the pipeline.

[Figure 3.8: Deployment diagram for SUSPS on Render – to be inserted here, showing the React static site, FastAPI web service, optional background pipeline jobs, managed PostgreSQL/PostGIS, and S3-based raw-data storage.]

---

# CHAPTER FOUR: RESULTS

## 4.0 Overview

This chapter presents the empirical results produced by the Smart Urban Simulation and Prediction System (SUSPS). It reports on baseline outputs derived from the assembled datasets, discusses how these outputs relate to the objectives of the study, summarises testing activities, and interprets key patterns observed in the data. The focus is on demonstrating that the system behaves plausibly in light of the literature and provides information that could support urban planning decisions.

Section 4.1 describes the baseline results generated by the data pipeline and models for demographics, mobility, energy, environment, and hotspots. Section 4.2 discusses the results in relation to stakeholder needs and the broader literature, noting the absence of a formal survey in this phase. Section 4.3 outlines the test data, test plan, and test results used to verify and validate the system. Section 4.4 provides an integrated analysis of the quantitative findings.

## 4.1 Baseline Study Results

[Placeholder: insert baseline maps and charts here, including population density maps, growth hotspot maps, typical daily energy demand curves, traffic flow profiles, and air-quality time series from the SUSPS dashboards.]

Baseline results are obtained by running the SUSPS pipeline on the assembled Nairobi datasets and loading the derived artefacts into the backend. The outputs can be viewed through the web-based dashboards or exported for further analysis. The main categories of baseline results are summarised below.

- **Demographic and population patterns.** Baseline maps of population density highlight high-density areas around the urban core and selected peripheral settlements, while lower-density regions appear towards the outskirts. Population growth projections, based on historic time series and gridded estimates, indicate continued expansion along key transport corridors and into neighbouring peri-urban areas. These patterns are consistent with previous studies on urbanisation in African cities, which document both densification and outward sprawl.
- **Mobility and traffic flows.** Using Digital Matatus route shapefiles, OpenStreetMap road networks, and representative daily profiles informed by traffic data, SUSPS generates idealised hourly traffic profiles for major routes and areas. The resulting curves show clear morning and evening peaks associated with commuting, with reduced flows in the middle of the day and at night. In congested corridors, the baseline profiles suggest sustained higher volumes and longer peak periods, reflecting known congestion hotspots in rapidly growing cities.
- **Energy demand profiles.** Baseline energy demand results are presented as daily and hourly profiles for the demonstration city and, where data permit, for selected sectors or areas. Typical patterns show morning and evening peaks linked to residential and commercial activity, with lower demand overnight. When interpreted at a relative rather than absolute scale, these profiles are consistent with reported patterns in urban energy studies and with the limited summary statistics available from sources such as the Africa Energy Portal and the International Energy Agency.
- **Environmental and air-quality indicators.** Weather and climate series (e.g., temperature and rainfall) and air-quality indicators (e.g., PM2.5) are processed into time series that can be visualised alongside growth, energy, and traffic metrics. Baseline charts reveal seasonal variations in temperature and rainfall, and episodes of elevated particulate concentrations that are likely associated with traffic, fuel use, and meteorological conditions. While the current prototype does not undertake causal attribution, these results provide useful context for interpreting hotspots.
- **Hotspot maps and composite indicators.** By combining demographic, mobility, energy, and environmental features, SUSPS produces hotspot maps that rank areas by composite indicators of pressure and risk. Areas with high population density, strong growth, limited infrastructure, and relatively poor environmental conditions appear as higher-priority hotspots. These maps offer an initial, configurable view of where planners and policymakers might focus attention.

Overall, the baseline study demonstrates that SUSPS can ingest heterogeneous datasets and produce interpretable outputs that align qualitatively with expectations from the literature on urban growth, congestion, and energy demand.

## 4.2 Survey Results and Discussion

At this stage of the project, no formal questionnaire-based survey of stakeholders was conducted, primarily due to time and access constraints. Consequently, this section focuses on discussing the baseline results in relation to the project objectives and the challenges faced by key stakeholders such as citizens, urban planners, and policymakers.

For citizens, the baseline outputs highlight areas where rapid growth and limited infrastructure may translate into overcrowding, long travel times, and exposure to environmental risks. For urban planners, the combined growth, energy, traffic, and hotspot views illustrate how multiple pressures overlap spatially, emphasising the need for integrated planning rather than isolated interventions. For policymakers, the results provide indicative evidence of where infrastructure investments, public transport improvements, or energy access programmes could have the greatest impact.

The patterns observed in the baseline maps and profiles are broadly consistent with the literature reviewed in Chapter Two: rapid urbanisation along transport corridors, persistent congestion on key routes, and increasing energy demand driven by population growth and economic activity. However, the demonstration nature of the prototype—using Nairobi as a stand-in for Lusaka and relying heavily on open data—means that the quantitative values should be interpreted cautiously. In future work, structured engagement with stakeholders, using questionnaires or workshops, would allow for more systematic assessment of the usefulness and usability of SUSPS outputs.

## 4.3 Testing (Test data, test plan and test report)

Testing of SUSPS combines automated tests, manual functional checks, and scenario-based validation of results. The goal is to ensure that the system is technically robust, that outputs are internally consistent, and that key failure modes are handled gracefully.

- **Test data.** Test data include both synthetic and real datasets. Synthetic datasets with simple, controlled patterns (for example, constant or linearly increasing time series) are used to verify that forecasting and simulation routines behave as expected and that edge cases are handled correctly. Real datasets from the baseline study are used to check that the system can process full-sized inputs and that outputs remain plausible.
- **Test plan.** The test plan focuses on three main areas: (i) backend services, including API endpoints for growth, energy, traffic, environment, hotspots, simulation, and time-series forecasting; (ii) data pipeline steps, ensuring that raw inputs are correctly transformed into processed artefacts; and (iii) frontend behaviour, including dashboard rendering, navigation between pages, and interaction with the simulation and advisory components.
- **Automated tests.** Selected backend endpoints and utilities are covered by automated unit and integration tests. For example, tests for the time-series forecasting API verify that energy demand forecasts differ meaningfully from baseline values while preserving the overall shape of the series. Additional tests check input validation, error handling, and basic performance characteristics.
- **Manual and exploratory testing.** Manual testing involves exercising the dashboards and simulation tools using representative scenarios, such as inspecting growth hotspots for specific years, examining energy demand under different trends, and checking traffic profiles for key corridors. Exploratory testing is used to identify usability issues, unexpected interactions between components, and edge cases that may not be captured by automated tests.

Test execution reports indicate that the system behaves reliably for the main use cases envisaged in this phase. Issues encountered during testing—such as earlier versions of the energy forecast being too close to the baseline—have been addressed by refining the underlying algorithms and adding additional safeguards in the backend. Remaining limitations relate primarily to data quality and coverage rather than software defects.

## 4.4 Data Analysis

The data analysis in this project focuses on assessing whether SUSPS outputs are plausible, internally consistent, and informative for planning purposes, rather than on calibrating models to a specific set of ground-truth measurements. The key analytical themes are as follows:

- **Consistency with known patterns.** Population, mobility, energy, and environmental outputs are assessed qualitatively against known patterns from the literature and general knowledge of rapidly growing African cities. For instance, the presence of commuting peaks in traffic profiles and evening peaks in energy demand, and the concentration of hotspots along major transport corridors, are all consistent with expectations.
- **Internal coherence across modules.** The analysis examines whether modules produce outputs that align with one another. Areas with high projected population growth are expected to exhibit increased energy demand and potentially higher traffic volumes; the hotspot module is checked to ensure that it highlights areas where these pressures overlap rather than producing contradictory signals.
- **Sensitivity to inputs and parameters.** By varying selected inputs and parameters in the simulation engine—such as growth rates or adjustments to baseline energy demand—the analysis checks that outputs change in the expected direction and magnitude. This provides confidence that the system can be used to explore “what-if” scenarios in a meaningful way.
- **Identification of data and model gaps.** The analysis also highlights where limitations in data (for example, sparse traffic measurements or aggregated energy statistics) constrain the precision of results. These gaps are documented as priorities for future data collection and model enhancement.

Overall, the analysis suggests that SUSPS provides a coherent, extensible framework for integrating multi-domain urban data and generating indicative insights. While the results should not yet be treated as fully calibrated forecasts for Lusaka, they demonstrate the feasibility and potential value of the approach.

---

# CHAPTER FIVE: IMPLEMENTATION

## 5.0 Implementation

This chapter describes how the Smart Urban Simulation and Prediction System (SUSPS) has been implemented in practice. It moves from the conceptual and architectural views presented in earlier chapters to concrete technologies, modules, and configuration. The implementation centres on four main components: the FastAPI backend, the React single-page frontend, the Python data pipeline, and the optional PostgreSQL/PostGIS database. These components are complemented by an AI advisory engine, authentication, and deployment scripts for Render.

### 5.0.1 Backend implementation (FastAPI)

The backend is implemented as a unified FastAPI application under `src/backend/api.py`. It exposes RESTful endpoints for core domains, simulation, time-series forecasting, hotspots, advisory, and authentication. Key characteristics include:

- **Unified application.** A single FastAPI `app` instance defines routes such as `/health`, `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/simulate/run`, `/ts/forecast`, `/environment/features`, `/air_quality/daily`, `/hotspots/areas`, `/hotspots/areas/forecast`, `/hotspots/scores`, `/areas`, `/processed_data`, `/simulation_inputs`, `/advisory/{scope}`, `/advisory_batch`, `/auth/signup`, and `/auth/login`.
- **Domain services.** Supporting modules under `src/models/` and `src/backend` implement deterministic helpers and domain logic. For example, time-series forecasting utilities in `ts_forecast` provide both Hugging Face–backed and deterministic forecast functions for growth, energy, and traffic; simulation helpers implement the SIMULATE engine across these domains; and advisory helpers summarise recent series for the advisory endpoints.
- **DB vs file-based operation.** When `USE_DB` or `USE_LOCAL_DB` is enabled and a database URL is provided, service functions read recent series and summaries from PostgreSQL tables such as `energy_consumption`, `traffic_flow`, `environment_features`, `air_quality_daily`, and `hotspot_scores`. When DB mode is disabled or tables are empty, the same functions fall back to processed CSV artefacts under `data/<CITY>/processed/`, and, if necessary, to synthetic demo data.
- **Input validation and schemas.** Pydantic models are used to define request and response schemas for key endpoints, ensuring type-checked interactions between the frontend and backend. This includes simulation parameter payloads, advisory requests, and time-series forecast inputs.
- **Authentication.** The `/auth/signup` and `/auth/login` endpoints manage user registration and login, hashing passwords and persisting user records in the `users` table defined by the schema dump. Tokens are simplified for this project and stored client-side by the React app.

The backend is served locally via Uvicorn during development (`uvicorn src.backend.api:app --reload`) and in production via Gunicorn with Uvicorn workers, as configured in `render.yaml` and `scripts/render_start.sh`.

### 5.0.2 Frontend implementation (React SPA)

The user interface is implemented as a Vite + React + TypeScript + Tailwind CSS single-page application under `src/frontend`. The SPA communicates exclusively with the FastAPI backend via `VITE_API_BASE_URL`. Major elements are:

- **Routing and layout.** React Router is used to define routes for `/signin`, `/signup`, `/dashboard`, `/urban-growth`, `/energy`, and `/traffic`. A shared layout component provides the persistent sidebar, header, and main content area.
- **Area-driven sidebar.** A left-hand sidebar, populated from the `/areas` endpoint, allows users to select the current area. Until an area is chosen, domain pages display explanatory text and placeholder charts. Once selected, the chosen area is propagated through context so that each page can call the appropriate endpoints with the area context.
- **Domain pages.**
  - The **Dashboard** aggregates growth, energy, and traffic summaries using `/growth`, `/energy`, `/traffic`, `/energy/summary`, and `/traffic/summary` to render overview charts and tiles.
  - The **Urban Growth** page renders bar charts and tables for growth series, exposing SIMULATE and Predict/Optimize actions wired to `/simulate/run` and `/ts/forecast`.
  - The **Energy** page renders line charts and tables for daily energy demand profiles and summaries, with similar SIMULATE and Predict/Optimize controls.
  - The **Traffic** page renders histograms and tables for hourly traffic volumes, also supporting SIMULATE and Predict/Optimize.
- **Reusable chart components.** SVG-based `BarChart`, `LineChart`, and `Histogram` components provide consistent axes, gridlines, legends, and colour schemes across pages. Each chart supports multiple overlaid series for Real, Predicted, Simulated, and Optimal values.
- **Authentication UI.** Dedicated `/signin` and `/signup` pages implement the login and registration flow, backed by the FastAPI authentication endpoints. An `AuthProvider` context stores auth state (in memory and localStorage) and a `RequireAuth` wrapper guards the main routes, redirecting unauthenticated users to `/signin`.
- **Hotspot map.** A Leaflet-based map component calls `/hotspots/areas` and `/hotspots/areas/forecast` to render hotspot points as red regions and optional green "optimal zones" when Optimize is active. A corresponding list summarises the most critical and improving areas.
- **Advisory panel.** Each main page includes an "AI Analysis & Insights" panel that calls `/advisory/{scope}` with the selected area and, when applicable, scenario label. A `FormattedInsights` component applies light formatting to the response.

The frontend is run locally with `npm run dev` and built for production (`npm run build`) when deployed as a static site on Render.

### 5.0.3 Data pipeline implementation

The data pipeline is implemented as a set of Python modules under `src/pipeline/`. It produces canonical raw and processed artefacts under `data/<CITY>/raw/` and `data/<CITY>/processed/`. Key steps are:

- **Ingestion (`src/pipeline/ingest.py`).** This module fetches or reads input datasets for demographics, mobility, energy, environment, air quality, land cover, and socio-economic indicators. It writes standardised CSVs into domain-specific subfolders such as `Demographics_and_Population/worldpop_summary.csv`, `Energy_and_Infrastructure/energy_demand.csv`, `Mobility_and_Transport/traffic_flows.csv`, and `Environmental_and_Climate/environment_monthly.csv`, reflecting the data sources described in Chapter Three.
- **Preprocessing (`src/pipeline/preprocess.py`).** This module transforms raw inputs into feature tables and summaries used by the models and API. Outputs include `worldpop_features.csv`, `energy_features.csv`, `traffic_features.csv`, `traffic_enriched_features.csv`, `environment_features.csv`, `environment_aq_features.csv`, `air_quality_daily.csv`, socio-economic features, hotspot scores (`hotspots_areas.csv`, `hotspots_areas_forecast.csv`), and catalogue tables summarising raster and GIS datasets.
- **Synthetic data (`src/pipeline/synthetic.py`).** Optional routines generate synthetic datasets for testing when real data are not available, ensuring that the system can be demonstrated even in constrained environments.
- **Fairness and diagnostics (`src/pipeline/fairness.py`).** Optional scripts compute simple fairness and distribution diagnostics across demographic groups and areas.

The pipeline is designed to be invoked from the command line using `python -m src.pipeline.ingest` and `python -m src.pipeline.preprocess`. When database mode is enabled, an additional utility `python -m src.backend.db.seed_from_processed` loads processed artefacts into the Postgres tables.

### 5.0.4 Database schema and seeding

The database schema is defined in `src/backend/db/susps_schema_dump.sql`. It creates tables such as `users`, `urban_areas`, `energy_consumption`, `traffic_flow`, `environment_features`, `air_quality_daily`, and `hotspot_scores`. Key aspects include:

- **Spatial data.** The `urban_areas` table stores geometries using PostGIS types, enabling spatial queries and potential future choropleth maps or spatial joins.
- **Time-series measures.** Tables like `energy_consumption` and `traffic_flow` store time-stamped measurements of predicted and, when available, actual values.
- **Flexible attributes.** JSON fields store parameters and results for simulation runs, as well as flexible attributes such as route information.

Seeding scripts load processed artefacts into these tables to ensure that the database-backed API behaves consistently with the file-based mode. Both local and Render environments rely on the same schema and processed files, with S3 used to mirror `data/<CITY>/raw/` in the cloud.

### 5.0.5 AI advisory and time-series forecasting

Two cross-cutting features differentiate SUSPS from a purely deterministic dashboard: the AI advisory engine and advanced time-series forecasting.

- **Advisory engine.** The `/advisory/{scope}` and `/advisory_batch` endpoints summarise recent growth, energy, traffic, and hotspot data and construct prompts for a free-tier Hugging Face language model. Responses are cached and simplified to plain text before being rendered by the React SPA. When the AI service is unavailable or disabled, deterministic rule-based text is returned instead.
- **Time-series forecasting.** The `/ts/forecast` endpoint serves Predicted overlays for growth, energy, and traffic series. When configured, it calls Hugging Face time-series models; otherwise, it uses deterministic heuristics that respect baseline shapes (for example, scaled daily profiles for energy and traffic, and trend-based forecasts for growth). Additional safeguards for energy forecasting ensure that predicted series differ meaningfully from baselines while remaining realistic.

### 5.0.6 Deployment and environment parity

Deployment is designed to support both local development and cloud hosting on Render while keeping behaviour as similar as possible across environments.

- **Local stack.** Developers run the FastAPI backend with Uvicorn, the React SPA with Vite, and, optionally, a local PostgreSQL instance with the SUSPS schema applied. The pipeline modules populate `data/<CITY>/raw/` and `data/<CITY>/processed/` prior to seeding the database.
- **Render deployment.** A `render.yaml` blueprint and `Procfile` describe a web service for the backend (using Gunicorn with Uvicorn workers) and a static site for the built React frontend. Environment variables configure database URLs, S3 bucket details, and optional bootstrap behaviour (ingest → preprocess → seed on first deploy).
- **Environment parity.** A dedicated S3 sync utility ensures that raw datasets under `data/<CITY>/raw/` used locally are mirrored to the `susps-raw-data` bucket on Amazon Web Sevices (AWS) linked to the deployed Render application. This makes it possible to reproduce the same API responses in both environments for a given city and area.

## 5.1 Discussion

The implementation of SUSPS reflects several conscious trade-offs between ambition and practicality, guided by the constraints of a final-year project, free-tier infrastructure, and data availability.

First, the choice of **FastAPI plus a React SPA** in place of a more tightly coupled server-rendered dashboard stack (such as the Dash-based approach envisaged in the proposal) improves separation of concerns. The backend can focus on data access, models, and advisory, while the frontend focuses on user experience and visualisation. This separation also aligns with modern industry practice and simplifies deployment on Render, where the API and static frontend can be hosted as distinct services.

Second, the implementation intentionally relies on **lightweight, interpretable models** and deterministic heuristics rather than the full suite of advanced machine learning libraries listed in the proposal. While the proposal mentioned tools such as XGBoost, LightGBM, TensorFlow, and deep learning frameworks, incorporating and tuning these for all domains would require substantial additional time, data, and compute. Instead, SUSPS prioritises robustness and clarity: baseline growth models use straightforward trends, energy and traffic models rely on realistic daily profiles, and AI components are confined to advisory text and optional time-series enhancements via Hugging Face.

Third, the system is designed to work **file-first with optional database support**. The proposal emphasised a central PostgreSQL/PostGIS database and more extensive logging and audit features. The implemented system still uses PostgreSQL/PostGIS for spatially enabled tables and persistent storage when enabled, but keeps the file-based pipeline as the primary source of truth for processed artefacts. This approach simplifies setup for demonstration purposes—developers can run the full stack without a database—and reduces operational complexity on free cloud plans.

Fourth, the **area-driven UI and hotspot map** represent an evolution of the original interface concepts. Rather than using a generic demo/API toggle, the implemented React frontend gates all data visualisations and advisory content on the selected area, encouraging users to frame questions at the city-neighbourhood scale. The hotspot and optimal-zone visualisations are implemented with a pragmatic radial layout and point overlays, leaving more advanced choropleth mapping as future work.

Finally, the **environment parity tools** and S3-backed workflow were not spelled out in the original proposal but emerged as a practical solution to ensuring that local and Render deployments behave consistently. By formalising the data layout and providing tooling to sync raw datasets, SUSPS reduces the risk of configuration drift between environments.

## 5.2 Development of the System as a Solution

This section reflects on how the implemented SUSPS platform addresses the problem statement and objectives, and it highlights key differences from the initial proposal along with their justifications.

### 5.2.1 Alignment with problem statement and objectives

The problem statement identified the lack of an integrated, data-driven urban simulation platform for Lusaka and similar cities, along with constraints in data, capacity, and infrastructure. The implemented SUSPS addresses this by:

- **Integrating heterogeneous data.** The pipeline and backend combine demographic, mobility, energy, environmental, and socio-economic datasets into a coherent set of features, enabling multi-domain analysis and hotspot identification.
- **Providing interpretable forecasts and simulations.** Endpoints for growth, energy, and traffic supply baseline forecasts and scenario-based simulations that can be explored via the UI, allowing planners and policymakers to visualise how pressures evolve under different assumptions.
- **Supporting decision making through advisory content.** The AI advisory engine turns numerical outputs into concise narrative insights, lowering the barrier for non-technical stakeholders to understand trends and potential actions.
- **Maintaining portability to Lusaka.** Although Nairobi is used as the main demonstration city due to data richness, the pipeline, models, and UI are parameterised by `CITY` and designed to be reconfigured for Lusaka as suitable datasets become available.

These capabilities map directly onto the general and specific objectives set out in Chapter One, particularly those relating to growth forecasting, energy demand profiling, traffic analysis, and the provision of a web-based prototype.

### 5.2.2 Changes from the initial proposal

Several aspects of the implementation differ from the original proposal, which envisaged a broader set of technologies and more complex analytical capabilities. The most important changes are summarised below.

- **Technology stack simplification.**
  - *Proposal:* A wide range of Python frameworks and libraries, including Dash for the UI and multiple machine learning and simulation libraries (such as TensorFlow, PyTorch, XGBoost, LightGBM, and Prophet), with the expectation of training bespoke models for each domain.
  - *Implementation:* A focused stack built around FastAPI, React, and a small set of deterministic and AI-assisted utilities. Dash and many heavy ML libraries are not used in the final system.
  - *Justification:* Concentrating on a smaller, modern stack reduces complexity, improves maintainability, and ensures that the system can run reliably on free-tier infrastructure. It also aligns the project with industry-standard patterns for web APIs and SPAs.

- **Model scope and depth.**
  - *Proposal:* Ambitious modelling plans, including advanced forecasting techniques, agent-based or cellular-automata-style simulations, and detailed fairness and drift analysis.
  - *Implementation:* Lightweight but well-structured models that focus on baseline forecasts, daily profiles, and simple scenario simulations. Fairness and diagnostic scripts are included but not elevated into full production pipelines.
  - *Justification:* Given constraints on time, data, and compute, the implemented models strike a balance between realism and feasibility. They provide useful insights for planning while keeping the codebase understandable and extensible for future work.

- **Data management and background processing.**
  - *Proposal:* A more elaborate architecture with a background worker service, object storage abstractions, and extensive logging and audit trails.
  - *Implementation:* A simpler batch-oriented pipeline that can be run on demand, with logging handled by standard application logs and a straightforward data layout under `data/<CITY>/`.
  - *Justification:* The simplified approach still supports reproducible data preparation and analysis but avoids the operational overhead of managing background workers and complex logging infrastructure on a student project.

- **User interface and interaction patterns.**
  - *Proposal:* Dash-based dashboards embedded directly in the backend service.
  - *Implementation:* A decoupled React SPA with area-driven navigation, SIMULATE and Predict/Optimize toggles, a dedicated authentication flow, and refined advisory panels.
  - *Justification:* The React SPA offers more flexibility for UI design, better performance for complex interactions, and clearer separation between frontend and backend concerns. It also reflects widely used patterns in modern web development.

Overall, these changes lead to a system that is somewhat narrower in algorithmic ambition than originally proposed but significantly stronger in terms of robustness, clarity, and deployability. The implemented SUSPS provides a solid and extensible foundation for future enhancements—such as more sophisticated models, richer stakeholder evaluation, and deeper integration with Lusaka-specific datasets—while already delivering practical value as a prototype decision-support tool.

---

# CHAPTER SIX: CONCLUSIONS, IMPLICATIONS AND RECOMMENDATIONS

## Conclusion

The Smart Urban Simulation and Prediction System (SUSPS) was conceived to address a clear gap in urban planning practice for Lusaka and similar cities: the absence of an integrated, data-driven platform that combines demographic, mobility, energy, and environmental information into actionable insights. Guided by systems theory and smart-city frameworks, the study has designed and implemented a working prototype that integrates a FastAPI backend, a React single-page frontend, a reproducible Python data pipeline, and an optional PostgreSQL/PostGIS database. Nairobi has been used as a demonstration environment, while the architecture and configuration remain portable to Lusaka as local datasets mature.

Across the chapters, the thesis has shown how heterogeneous datasets can be assembled into canonical raw and processed artefacts, transformed into interpretable features, and exposed via web APIs and dashboards. The implemented system delivers baseline forecasts of urban growth, indicative daily energy demand profiles, and approximated traffic flow patterns, complemented by composite hotspot maps and an AI-assisted advisory engine. Automated tests, qualitative checks, and scenario-based analysis indicate that these outputs behave plausibly in light of the literature and domain knowledge for rapidly growing African cities.

The work has also demonstrated that a carefully scoped, lightweight modelling approach—emphasising deterministic baselines and transparent heuristics, with optional AI enhancements—can provide useful planning insights without requiring expensive infrastructure or extensive proprietary data. The pipeline and environment parity mechanisms ensure that results can be reproduced across local and cloud deployments, which is essential for transparency, teaching, and policy dialogue. Although the prototype does not yet incorporate all of the advanced analytical techniques and evaluation activities envisaged in the original proposal, it offers a robust and extensible foundation for future work.

At a broader level, the project contributes a concrete example of how open geospatial datasets, free-tier APIs, and modern web technologies can be combined into a decision-support tool tailored to the constraints faced by African cities. The conclusions of this study underscore that even under data and capacity limitations, it is possible to build integrated urban analytics platforms that move planning practice from reactive responses towards more anticipatory, evidence-informed decision making (UN-Habitat, 2020; World Bank, 2021).

## Implications

The findings from SUSPS carry several implications for urban planners, policymakers, technical practitioners, and researchers.

For **urban planners and government agencies**, SUSPS illustrates how integrated analytics can support more coherent decision making across traditionally siloed domains. By presenting growth forecasts, energy demand profiles, traffic patterns, environmental indicators, and hotspot rankings in a single interface, the system encourages planners to consider how pressures overlap spatially and temporally rather than treating each sector in isolation. Scenario-based simulations and forecast overlays make it easier to explore the consequences of alternative growth rates, demand-response policies, or transport interventions before committing to costly infrastructure investments.

For **policymakers and regulators**, the platform highlights the value of systematic data collection and stewardship. The quality and usefulness of SUSPS outputs are directly linked to the availability and reliability of underlying datasets. The work therefore reinforces policy arguments for strengthening national and municipal statistical systems, investing in geospatial and mobility data, and formalising data-sharing agreements between agencies. It also points towards the potential for more transparent and accountable planning processes, where evidence used in decision making can be inspected, reproduced, and debated.

For **citizens and civil society organisations**, tools like SUSPS can, over time, enable more informed engagement with urban development debates. While the current prototype is primarily targeted at planners and technical users, its dashboards and advisory narratives could be adapted for public-facing portals or participatory planning workshops. Visualisations of congestion hotspots, growth corridors, and areas with combined environmental and infrastructure stress can support more inclusive conversations about where to prioritise investment and how different neighbourhoods are affected by policy choices.

For the **technical and academic community**, the project offers a reusable blueprint for building urban analytics platforms in resource-constrained settings. The emphasis on open-source technologies, free-tier services, and reproducible pipelines aligns with good research practice and facilitates adaptation to other cities. The work also surfaces important methodological considerations—such as the trade-offs between model complexity and interpretability, and between data richness and portability—that can inform future research on smart cities and urban computing (Zheng et al., 2014; Batty, 2013).

## Recommendations

Based on the conclusions and implications above, several recommendations can be made for practice, policy, and further technical development.

1. **Institutionalise integrated urban analytics in planning processes.** Planning departments and related agencies should consider adopting platforms like SUSPS, or extending this prototype, as part of their routine workflows. This entails designating responsible units for maintaining the data pipeline, running periodic updates, and interpreting outputs in collaboration with sector specialists.

2. **Strengthen data governance and collaboration.** To maximise the value of SUSPS, ministries and agencies responsible for statistics, transport, energy, environment, and land use should establish clear data-sharing protocols and standards. Priority should be given to improving the temporal resolution and spatial coverage of key datasets (e.g., traffic counts, energy consumption, settlement growth) and to documenting metadata so that limitations are well understood.

3. **Pilot deployment in Lusaka with targeted use cases.** A practical next step is to configure SUSPS for Lusaka using the best available local data and to pilot it on a limited set of planning questions—for example, prioritising corridors for public transport investment, identifying growth hotspots for serviced land, or assessing energy demand implications of new housing areas. Lessons from such pilots can guide refinements to models, interfaces, and institutional arrangements.

4. **Invest in capacity building for planners and analysts.** Effective use of a platform like SUSPS requires basic data literacy, familiarity with geospatial analytics, and comfort with interpreting simulation outputs. Short training programmes, joint workshops between universities and planning agencies, and documentation tailored to non-technical users can help build this capacity.

5. **Maintain and extend the technical foundation.** From a software perspective, it is recommended that the SUSPS codebase continue to be maintained as an open, well-documented project. Over time, the pipeline can be extended to incorporate additional domains (such as housing quality or public health indicators), the database schema can be refined to support richer queries, and the frontend can be enhanced with more sophisticated visualisations such as choropleth maps and comparative dashboards.

6. **Embed evaluation and feedback mechanisms.** Future iterations of SUSPS deployments should include structured evaluation—such as user surveys, usability testing, and before–after studies—to assess how well the system supports decision making in practice. Feedback from these evaluations should be used to prioritise feature improvements and data collection efforts.

## Future Works

While the current prototype achieves its core objectives, there are several avenues for future work that can enhance the robustness, realism, and impact of SUSPS.

- **Local data integration for Lusaka.** A priority is to progressively replace proxy and demonstration datasets with Lusaka-specific data across all domains. This includes obtaining more detailed census and survey data, traffic counts or GPS traces, utility energy statistics, and local environmental measurements. As local data quality improves, models can be recalibrated and validated more rigorously.

- **Advanced modelling and calibration.** Future work could introduce more sophisticated forecasting and simulation techniques—such as ensemble time-series models, spatial interaction models, or agent-based simulations—where data volume and quality justify the additional complexity (Hyndman and Athanasopoulos, 2018; Vlahogianni et al., 2014). Systematic calibration against observed outcomes and the use of formal accuracy metrics would strengthen confidence in the quantitative outputs.

- **Enhanced spatial analytics and visualisation.** The current hotspot visualisations rely on point-based or radial layouts. Extending these to full ward or zone-based choropleth maps, integrating richer GIS layers, and supporting interactive spatial queries would make the system more intuitive for planners accustomed to map-centric workflows. Deeper use of PostGIS capabilities and geospatial libraries can support this evolution.

- **Stakeholder engagement and co-design.** Future phases should incorporate structured engagement with planners, policymakers, community representatives, and technical staff. Co-design workshops and participatory mapping exercises can help ensure that indicators, scenarios, and visualisations align with real decision needs and that the system interface is accessible to its intended users.

- **Operationalisation and sustainability.** Finally, research is needed on how to operationalise SUSPS within existing institutional and budgetary constraints. This includes exploring hosting models (e.g., national data centres or cloud providers), governance arrangements for long-term maintenance, role-based access control and auditing within the system, and integration with other digital platforms used by government.

Pursuing these future directions would move SUSPS from a demonstration prototype towards a mature, institutionalised decision-support platform capable of underpinning more sustainable and equitable urban development in Lusaka and similar cities.

---

# References

Africa Energy Portal (n.d.) *Africa Energy Portal Statistics and Data*. African Development Bank Group.

AirQo (n.d.) *AirQo Community Air Quality Data Platform*. AirQo.

Albino, V., Berardi, U. and Dangelico, R.M. (2015) ‘Smart cities: definitions, dimensions, performance, and initiatives’, *Journal of Urban Technology*.

Batty, M. (2013) *The New Science of Cities*. Cambridge, MA: MIT Press.

Batty, M. (2018) *Inventing Future Cities*. Cambridge, MA: MIT Press.

Deb, C., Zhang, F., Yang, J., Lee, S.E. and Shah, K.W. (2017) ‘A review of demand forecasting techniques for building energy consumption’, *Renewable and Sustainable Energy Reviews*.

Digital Matatus (n.d.) *Digital Matatus Project – Nairobi Transit Data*. University of Nairobi and partners.

Ghosh, S., Ghosh, A. and Sanyal, S. (2018) ‘Electricity consumption forecasting using time series and machine learning models’, *International Journal of Energy Economics and Policy*.

GRID3 (n.d.) *Geo-Referenced Infrastructure and Demographic Data for Development (GRID3) Datasets*. GRID3.

Hollands, R.G. (2008) ‘Will the real smart city please stand up? Intelligent, progressive or entrepreneurial?’, *City*.

Hyndman, R.J. and Athanasopoulos, G. (2018) *Forecasting: Principles and Practice*. 2nd edn. OTexts.

ICPAC (n.d.) *Land Cover Maps and Climate Datasets for Eastern Africa*. IGAD Climate Prediction and Applications Centre.

International Energy Agency (2019) *Africa Energy Outlook 2019*. Paris: IEA.

Kitchin, R. (2014) ‘The real-time city? Big data and smart urbanism’, *GeoJournal*.

Lemmens, R., et al. (2017) ‘Data integration and analytics for African cities: challenges and opportunities’, *International Journal of Geo-Information*.

Litman, T. (2021) ‘Congestion cost and congestion pricing evaluation’, *Victoria Transport Policy Institute Working Paper*.

Lv, Y., Duan, Y., Kang, W., Li, Z. and Wang, F.-Y. (2015) ‘Traffic flow prediction with big data: a deep learning approach’, *IEEE Transactions on Intelligent Transportation Systems*.

Macrotrends (n.d.) *Nairobi, Kenya Metro Area Population 1950–2025*. Macrotrends LLC.

OpenAQ (n.d.) *OpenAQ Open Air Quality Data Platform*. OpenAQ.

OpenStreetMap contributors (n.d.) *OpenStreetMap: Open Data for Streets and Transport Networks*. OpenStreetMap Foundation.

OpenWeather (n.d.) *OpenWeather API Documentation*. OpenWeather Ltd.

Pressman, R.S. (2010) *Software Engineering: A Practitioner’s Approach*. 7th edn. New York: McGraw-Hill.

Silva, E.A. and Clarke, K.C. (2002) ‘Calibration of the SLEUTH urban growth model for Lisbon and Porto, Portugal’, *Computers, Environment and Urban Systems*.

Skyttner, L. (2005) *General Systems Theory: Problems, Perspective, Practice*. 2nd edn. Singapore: World Scientific.

Sommerville, I. (2011) *Software Engineering*. 9th edn. Boston: Addison-Wesley.

TomTom (n.d.) *TomTom Traffic API Documentation*. TomTom International.

Townsend, A.M. (2013) *Smart Cities: Big Data, Civic Hackers, and the Quest for a New Utopia*. New York: W.W. Norton.

UN-Habitat (2020) *World Cities Report 2020: The Value of Sustainable Urbanization*. Nairobi: UN-Habitat.

United Nations (2019) *World Urbanization Prospects: The 2018 Revision*. New York: United Nations.

Vlahogianni, E.I., Karlaftis, M.G. and Golias, J.C. (2014) ‘Short-term traffic forecasting: Where we are and where we’re going’, *Transportation Research Part C: Emerging Technologies*.

Waddell, P. (2002) ‘UrbanSim: Modelling urban development for land use, transportation, and environmental planning’, *Journal of the American Planning Association*.

Wegener, M. (2011) ‘From macro to micro – changing models of land use and transport’, *Transport Reviews*.

Williams, S., White, A., Waiganjo, P., Orwa, D. and Klopp, J.M. (2015) ‘The Digital Matatus project: Using cell phones to create an open source data for Nairobi’s semi-formal bus system’, *Journal of Transport Geography*.

World Bank (2021) *Africa’s Cities: Challenges and Opportunities for Urban Development*. Washington, DC: World Bank.

WorldPop (n.d.) *WorldPop Global High-Resolution Population Datasets*. WorldPop Research Group.

Zheng, Y., Capra, L., Wolfson, O. and Yang, H. (2014) ‘Urban computing: Concepts, methodologies, and applications’, *ACM Transactions on Intelligent Systems and Technology*.

---

# Appendix

## Questionnaire

No formal questionnaire-based survey of stakeholders was conducted as part of this project, primarily due to time, access, and ethical clearance constraints. Consequently, the empirical evaluation reported in Chapter Four focuses on baseline quantitative outputs, automated tests, and qualitative interpretation rather than survey statistics.

If a structured survey is undertaken in future work, this appendix should be populated with the full questionnaire instrument and a brief description of its administration. A typical stakeholder questionnaire for SUSPS would contain sections such as:

- Background information (role, organisation, years of experience in urban planning or related fields).
- Perceptions of current urban challenges (e.g., traffic congestion, energy reliability, informal settlement growth).
- Experience with data-driven tools and dashboards in daily work.
- Evaluation of SUSPS outputs (clarity of dashboards, usefulness of forecasts and hotspots, relevance of advisory narratives).
- Perceived impact of SUSPS on planning decisions (e.g., whether it would change how priorities are identified or justified).
- Open-ended questions on desired features, concerns, and suggestions for improvement.

Providing the complete questionnaire and any supporting information (for example, consent forms or information sheets) in this appendix would ensure transparency and reproducibility of any future survey-based evaluation.

## System Functionalities

This appendix summarises the main user-facing functionalities of the Smart Urban Simulation and Prediction System (SUSPS) in a concise, implementation-aware manner. It complements the detailed descriptions in Chapters Three to Five.

### A. Backend and data pipeline functionalities

- **Data ingestion and preprocessing**
  - Ingests demographic, mobility, energy, environmental, air-quality, and socio-economic datasets from files and APIs.
  - Normalises inputs into canonical CSV and GeoJSON artefacts under `data/<CITY>/raw/`.
  - Produces processed feature tables under `data/<CITY>/processed/`, including traffic, energy, environment, air-quality, and hotspot features.

- **Core analytical endpoints**
  - `/growth` – serves precomputed and forecast population and growth series for the current city and area.
  - `/energy` and `/energy/summary` – provide hourly demand profiles and aggregate summaries.
  - `/traffic` and `/traffic/summary` – provide hourly traffic volume profiles and aggregate summaries.
  - `/environment/features` and `/air_quality/daily` – expose processed environmental and air-quality indicators.
  - `/hotspots/areas`, `/hotspots/areas/forecast`, and `/hotspots/scores` – expose static and forecast hotspot scores and metadata.

- **Simulation and forecasting services**
  - `/simulate/run` – applies parameterised adjustments (e.g., growth rates, demand scaling, peak shifting) to baseline series to generate scenario simulations for growth, energy, and traffic.
  - `/ts/forecast` – produces Predicted overlays for growth, energy, and traffic using either free-tier time-series models or deterministic heuristics.

- **Advisory and metadata services**
  - `/advisory/{scope}` and `/advisory_batch` – compile recent indicators into structured narrative guidance for specific scopes (dashboard, growth, energy, traffic), optionally using Hugging Face language models.
  - `/areas`, `/processed_data`, and `/simulation_inputs` – provide metadata used by the frontend for area selection, data provenance, and simulation parameter configuration.

- **Authentication and user management**
  - `/auth/signup` and `/auth/login` – support basic user creation and login, backed by a `users` table in PostgreSQL when database mode is enabled.

### B. Frontend functionalities

- **Authentication and access control**
  - Sign-in and sign-up pages allow users to create accounts and authenticate.
  - Protected routes ensure that only authenticated users can access core dashboards.

- **Area-driven dashboards**
  - A persistent sidebar exposes an `area-select` control backed by the `/areas` endpoint.
  - Until an area is selected, domain pages show descriptive content and placeholder charts.
  - Once an area is selected, domain pages call the relevant endpoints with area context and render real data.

- **Domain-specific pages**
  - **Dashboard** – summarises growth, energy, and traffic indicators using compact charts and tiles.
  - **Urban Growth** – displays growth series with Real, Predicted, Simulated, and Optimal overlays and a simulation-parameter panel.
  - **Energy** – displays daily energy demand profiles and summaries with analogous overlays and controls.
  - **Traffic** – displays hourly traffic profiles and summaries using histogram-style charts.

- **Hotspot map and optimal zones**
  - Leaflet-based map shows hotspot areas and forecasted changes, highlighting improving zones when Optimize mode is active.
  - A companion list ranks areas by hotspot scores and indicates potential optimal zones.

- **AI Analysis & Insights panels**
  - Each main page includes an advisory panel that displays narrative insights from `/advisory/{scope}`.
  - A formatting component emphasises key headings and recommended actions while hiding technical markup.

- **Exports and usability features**
  - Export functionality allows users to generate documents that include tables and chart renderings aligned with on-screen visuals.
  - Responsive design ensures usability on both desktop and mobile devices.

## Technical Report (Algorithm or selected source code)

This appendix provides high-level algorithmic descriptions and illustrative code excerpts to clarify how key SUSPS components operate. The goal is not to reproduce the entire codebase, but to document representative logic that underpins the main functionalities.

### A. Time-series forecasting (deterministic fallback)

When advanced time-series models are not configured, the `/ts/forecast` endpoint uses lightweight deterministic heuristics that preserve the overall shape of baseline series while generating plausible predictions.

For growth forecasts, the algorithm:

1. Extracts the historical series of population or growth indicators for the selected area.
2. Fits a simple trend (for example, an ordinary least-squares line) across all available years.
3. Projects this trend forward for the required forecast horizon.
4. Clips or smooths the results to avoid unrealistic negative values or explosive growth.

For energy and traffic forecasts, the algorithm:

1. Takes a representative 24-hour baseline profile for the selected area.
2. Computes a modest adjustment factor based on recent changes in demand or volumes.
3. Scales the baseline profile by this factor while preserving its diurnal shape (morning and evening peaks, lower night-time values).
4. Returns the resulting profile as the Predicted overlay used by the frontend charts.

These heuristics are implemented in the backend as simple numerical operations, making them easy to audit and extend.

A simplified excerpt from the deterministic fallback implementation is shown below:

```python path=C:\Users\david\OneDrive\Documents\SWE-Final-Year-Project--SUSPS\SWE-Project--SUSPS\src\backend\ts_forecast.py start=221
    def _forecast_deterministic(
        self, series: List[Dict[str, Any]], horizon: int
    ) -> List[Dict[str, Any]]:
        """Deterministic forecast when no HF model is used or available.

        Growth uses a simple trend-based extrapolation. Energy and traffic use
        uplifted copies of the existing series so the hourly/daily shape is
        preserved. For energy, higher values receive a slightly larger uplift,
        and a completely flat series is extended unchanged for tests and edge
        cases.
        """

        if not series or horizon <= 0:
            return []

        # For energy and traffic, scale the existing series while keeping the
        # overall shape. Energy uses a stronger, value-aware uplift.
        if self.target in {"energy", "traffic"}:
            values = [float(s.get("value", 0.0)) for s in series]
            v_min = min(values)
            v_max = max(values)
            rng = v_max - v_min

            # Energy: apply a stronger, peak-aware uplift.
            if self.target == "energy":
                # Preserve a perfectly flat series exactly so that tests expecting
                # a constant deterministic forecast (e.g. 10.0 -> 10.0) continue
                # to hold.
                if rng == 0.0:
                    last = series[-1]
                    last_t = float(last.get("t", len(series)))
                    last_v = float(last.get("value", 0.0))
                    return [
                        {
                            "step": i + 1,
                            "t": last_t + float(i + 1),
                            "value": last_v,
                            "source": "deterministic",
                        }
                        for i in range(horizon)
                    ]
```

### B. SIMULATE engine for scenario analysis

The `/simulate/run` endpoint provides a generic simulation engine that applies user-specified parameter changes to baseline series for growth, energy, and traffic. At a high level, the engine:

1. Receives a payload specifying the target module (growth, energy, or traffic), the selected area, and simulation parameters (e.g., scaling factors, rate adjustments, peak shifts).
2. Retrieves the relevant baseline series from the database or processed CSVs.
3. Applies transformations such as:
   - Multiplicative scaling (e.g., increasing all values by a given percentage).
   - Additive adjustments to specific time windows (e.g., peak hours only).
   - Temporal shifting of peaks to model behavioural or policy changes.
4. Computes basic summary statistics for the simulated series (e.g., total demand, peak values).
5. Returns both the modified series and summaries to the frontend for visualisation and comparison with Real and Predicted curves.

The transformations are designed to be simple and interpretable so that planners can understand how parameter changes affect outputs.

The following excerpt illustrates how hourly energy demand is adjusted for SIMULATE scenarios:

```python path=C:\Users\david\OneDrive\Documents\SWE-Final-Year-Project--SUSPS\SWE-Project--SUSPS\src\backend\simulation.py start=153
def simulate_energy(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply scenario adjustments to hourly energy demand.

    Supported parameters (all optional):
    - demand_scale: global multiplier for demand_mwh.
    - peak_hour_shift: integer hour shift for peak load (positive shifts peak
      later in the day, negative shifts earlier). This is applied with a simple
      rotation over the 24h profile.
    - peak_scale: additional multiplier applied to a fixed set of peak hours
      (07–08 and 17–18) after rotation.
    - offpeak_scale: multiplier applied to non-peak hours (default 1.0).
    - flatten_ratio: 0..1 factor that pulls values toward the daily average
      (0 = no change, 1 = fully flattened profile at the mean).
    - max_demand_mwh: optional cap on hourly demand (<=0 disables the cap).
    """

    if not base_items:
        return []

    params = params or {}
    demand_scale = _get_float(params, "demand_scale", 1.0)
    peak_hour_shift = _get_float(params, "peak_hour_shift", 0.0)
    peak_scale = _get_float(params, "peak_scale", 1.0)
```

### C. Data pipeline and hotspot scoring

The hotspot scoring routines in the pipeline combine multiple indicators into composite scores for each area:

1. Normalise selected indicators (e.g., population density, growth rate, traffic intensity, energy demand, environmental stress) to a common scale.
2. Apply configurable weights to reflect planning priorities.
3. Sum or aggregate weighted indicators into a single hotspot score per area.
4. Optionally compute forecasted hotspot scores using projected growth or demand.
5. Export results as CSVs (`hotspots_areas.csv`, `hotspots_areas_forecast.csv`) that are ingested by the backend and exposed through hotspot endpoints.

These steps ensure that hotspot maps and lists are traceable back to underlying indicators and can be reconfigured as planning priorities evolve.

The scoring logic is implemented in the preprocessing pipeline as shown in the excerpt below:

```python path=C:\Users\david\OneDrive\Documents\SWE-Final-Year-Project--SUSPS\SWE-Project--SUSPS\src\pipeline\preprocess.py start=619
def preprocess_hotspots() -> Path:
    """Compute simple area-level hotspots from processed features.

    This is a deterministic, resource-efficient hotspot score built from
    existing processed tables (worldpop_features and socioeconomic_features).
    It does not require any external APIs or ML models and is suitable for
    driving map overlays (by joining on admin_unit in a separate GeoJSON).
    """

    config.ensure_dirs()
    wp = config.PROCESSED_DIR / "worldpop_features.csv"
    se = config.PROCESSED_DIR / "socioeconomic_features.csv"
    if not wp.exists() or not se.exists():
        raise FileNotFoundError(
            "hotspot preprocessing requires worldpop_features.csv and "
            "socioeconomic_features.csv; run preprocess_worldpop and "
            "preprocess_socioeconomic first."
        )

    df_wp = pd.read_csv(wp)
    df_se = pd.read_csv(se)

    if "admin_unit" not in df_wp.columns:
        raise ValueError("worldpop_features.csv must contain admin_unit column")
```

### D. Database schema overview

The SUSPS database schema, detailed in `src/backend/db/susps_schema_dump.sql`, defines tables for users, urban areas, energy consumption, traffic flows, environment features, air-quality series, and hotspot scores, among others. Key design choices include:

- Using foreign keys from measurement tables (e.g., energy and traffic) to the `urban_areas` table to support area-based queries.
- Storing geometries in PostGIS-compatible columns to enable spatial operations.
- Including JSON fields for flexible attributes such as simulation parameters and results.

By combining relational structure with spatial support and flexible attributes, the schema provides a robust foundation for the analytics and visualisation features described in the main chapters.

A representative excerpt from the unified schema is shown below:

```sql path=C:\Users\david\OneDrive\Documents\SWE-Final-Year-Project--SUSPS\SWE-Project--SUSPS\src\backend\db\susps_schema_dump.sql start=101
-- Monthly environment + air-quality features (mirrors environment_aq_features.csv)
CREATE TABLE IF NOT EXISTS public.environment_features (
    id               BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.areas(id) ON DELETE SET NULL,
    month            INTEGER NOT NULL,
    temp_c           DOUBLE PRECISION,
    rain_mm          DOUBLE PRECISION,
    cooling_deg      DOUBLE PRECISION,
    wet_month        INTEGER,
    pm25             DOUBLE PRECISION,
    pm10             DOUBLE PRECISION,
    o3               DOUBLE PRECISION,
    pollution_index  DOUBLE PRECISION
);

-- Area-level hotspot / optimal-zone scores (mirrors hotspots_areas*.csv)
CREATE TABLE IF NOT EXISTS public.hotspot_scores (
    id               BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.areas(id) ON DELETE SET NULL,
    admin_unit       VARCHAR(150),
    year             INTEGER,
    population       DOUBLE PRECISION,
    pop_share        DOUBLE PRECISION,
    income_norm      DOUBLE PRECISION,
    employment_score DOUBLE PRECISION,
    hotspot_score    DOUBLE PRECISION
);
```
