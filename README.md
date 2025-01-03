# Synthea Patient Generator with Web Interface

A containerized web application for generating synthetic patient data using Synthea. This application provides a user-friendly interface to Synthea's synthetic patient generation capabilities, making it easy to create realistic healthcare data in various formats.

## About Synthea

Synthea™ is an open-source synthetic patient generator that models the medical history of artificial patients. This application uses Synthea v3.3.0, which includes support for:

- FHIR R4+ with US Core Implementation Guide
- Enhanced CSV exports
- Improved terminology bindings
- Better performance and stability

Using Synthea, you can generate realistic but completely synthetic patient records that include:

- Demographics
- Medical history
- Medications
- Allergies
- Lab results
- Vital signs
- Encounters/visits
- Social determinants of health
- Claims data

The generated data is:
- Completely synthetic (not derived from real patient data)
- Statistically realistic
- Free of cost and privacy restrictions
- Available in multiple formats (FHIR, C-CDA, CSV, etc.)

### How Synthea Works

Synthea uses a temporal model to simulate patient lives from birth to death through the modern health system. It generates:

1. **Population Data**: Creates demographically realistic population based on U.S. Census data
2. **Medical History**: Simulates medical conditions, treatments, and outcomes using clinical care protocols
3. **Healthcare Encounters**: Models interactions with healthcare providers
4. **Geographic Variation**: Accounts for regional differences in disease prevalence and care delivery

## Application Features

This web interface simplifies Synthea usage by providing:

### Core Features

- **Multi-format Export**: Generate data in multiple formats simultaneously:
  - FHIR (R4, DSTU2, STU3) - Modern healthcare interoperability standard
  - C-CDA - Clinical Document Architecture format
  - HL7 v2 - Traditional healthcare messaging standard
  - CSV - Tabular format for data analysis
  - CPCDS - Claims data format
  - Text/HTML - Human-readable formats

- **Customization Options**:
  - Patient Count: Generate any number of synthetic patients
  - Time Range: Specify years of history to generate
  - Geographic Location: Select U.S. state for population characteristics
  - Multiple Output Formats: Choose one or more output formats simultaneously

### Technical Features

- **Containerized Deployment**: Easy setup using Docker and Docker Compose
- **Modern Web Interface**: Built with FastAPI and Tailwind CSS
- **Persistent Storage**: Generated files saved to host machine
- **Real-time Processing**: Asynchronous generation with status updates
- **Download Management**: Easy access to generated files through web interface

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd fhir-synthea
   ```

2. Start the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Access the web interface at: http://localhost:3000

4. Generated files will be available in the `output` directory.

## Usage Guide

1. Open your web browser and navigate to http://localhost:3000

2. Configure your generation parameters:
   - **Number of Patients**: How many synthetic patients to create
   - **Years of History**: How many years of medical history to generate
   - **Output Formats**: Select one or more output formats
     - FHIR R4: Latest FHIR standard (recommended for modern systems)
     - FHIR DSTU2/STU3: Earlier FHIR versions for legacy systems
     - C-CDA: Clinical document format
     - HL7 v2: Traditional healthcare messaging
     - CSV: Tabular data for analysis
     - Others: Additional formats for specific needs
   - **State**: Select the U.S. state to use for population characteristics

3. Click "Generate Patients" and wait for processing to complete

4. Access your files:
   - Download directly from the web interface
   - Find in the local `output` directory
   - Files are organized by format type (fhir/, ccda/, csv/, etc.)

## Output Directory Structure

```
output/
├── fhir/           # FHIR format files (JSON)
├── ccda/           # C-CDA documents
├── csv/            # CSV files for different data types
├── html/           # Human-readable HTML records
└── hl7/            # HL7 v2 messages
```

## Development

To modify the application:

1. Stop the running containers:
   ```bash
   docker-compose down
   ```

2. Make your changes to the code

3. Rebuild and start the containers:
   ```bash
   docker-compose up --build
   ```

## Project Structure

```
.
├── app/
│   └── main.py          # FastAPI application
├── static/
│   └── index.html       # Web interface
├── output/              # Generated files directory
├── Dockerfile          # Container definition
├── docker-compose.yml  # Docker Compose configuration
└── requirements.txt    # Python dependencies
```

## Common Use Cases

1. **Healthcare Software Testing**: Generate realistic test data for healthcare applications
2. **Medical Research**: Create synthetic datasets for research and analysis
3. **Education**: Provide realistic patient cases for medical education
4. **Integration Testing**: Test healthcare system integrations with various data formats
5. **Machine Learning**: Generate training data for healthcare ML models

## License

[Add your license information here]

## Acknowledgments

- Synthea™ is an open-source project by The MITRE Corporation
- This application uses Synthea version 3.3.0
