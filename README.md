# Synthea Patient Generator Web UI

A modern web interface for generating synthetic patient data using the Synthea patient generator.

## Features

- **Multiple Output Formats**:
  - FHIR (R4, STU3, DSTU2)
  - HL7 v2.4
  - C-CDA
  - CSV
  - JSON
  - CPCDS

- **User-Friendly Interface**:
  - Simple form for patient generation parameters
  - Real-time progress updates
  - Organized output format selection
  - Clear descriptions for each format

- **Flexible Configuration**:
  - Configurable number of patients
  - State selection for demographics
  - Customizable output formats
  - Dynamic properties management

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Synthea-patient-generator.git
cd Synthea-patient-generator
```

2. Build and run with Docker Compose:
```bash
docker compose up --build -d
```

3. Access the web interface:
```
http://localhost:8000
```

## Usage

1. Select your desired output formats from the available options
2. Enter the number of patients to generate
3. Choose a US state for demographic data
4. Click "Generate Patients"
5. Monitor the progress in real-time
6. Access generated files in the output directory

## Output Structure

Generated files are organized in the `output` directory with subdirectories for each format:
- `/output/fhir/` - FHIR resources (R4, STU3, or DSTU2)
- `/output/hl7/` - HL7 v2.4 messages
- `/output/ccda/` - C-CDA documents
- `/output/csv/` - CSV files
- `/output/json/` - JSON files
- `/output/cpcds/` - CPCDS format files

## Technical Details

- Built with FastAPI and Python
- Uses the official Synthea JAR for patient generation
- Real-time progress updates via Server-Sent Events (SSE)
- Docker containerization for easy deployment
- Dynamic properties file management for Synthea configuration

## About Synthea

Synthea is an open-source synthetic patient generator that models the medical history of synthetic patients. The resulting data is free from cost, privacy, and security restrictions, making it ideal for:
- Healthcare software development
- Medical education
- EHR system testing
- Health IT standards development

For more information about Synthea, visit [SyntheticMass](https://syntheticmass.mitre.org/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- [Synthea Project](https://github.com/synthetichealth/synthea) for the synthetic patient generator
- MITRE Corporation for developing and maintaining Synthea

## Coming Soon

- Bulk download functionality for FHIR files
- Additional format customization options
- Enhanced error handling and validation
