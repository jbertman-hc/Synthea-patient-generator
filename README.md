# Synthea Patient Generator Web UI

A modern web interface for generating synthetic patient data using the Synthea patient generator (screenshot of UI: https://app.screencast.com/sfIhlt8Ucb2yW).

## Features

- **Comprehensive Output Format Support**:
  - FHIR R4 (Latest Version)
  - FHIR STU3
  - FHIR DSTU2
  - HL7 v2.4
  - C-CDA
  - CSV
  - JSON
  - CPCDS

- **Advanced FHIR Capabilities**:
  - Individual FHIR resource file download
  - Bulk FHIR directory download (as ZIP)
  - Support for multiple FHIR versions in parallel
  - Excludes practitioner and hospital information files from downloads

- **User-Friendly Interface**:
  - Simple form for patient generation parameters
  - Real-time progress updates
  - Organized output format selection with "Check All" option
  - Clear descriptions for each format
  - Modern, responsive design with mobile support

- **Flexible Configuration**:
  - Configurable number of patients
  - State selection for demographics
  - Optional numerical suffixes for patient names
  - Dynamic properties management
  - Customizable output formats

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jbertman-hc/Synthea-patient-generator.git
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

1. Access the web interface at `http://localhost:8000`
2. Configure your generation parameters:
   - Select one or more output formats
   - Enter the desired number of patients
   - Choose a US state for demographic data
   - Optionally disable numerical suffixes in patient names
3. Click "Generate Patients" to start the process
4. Monitor the generation progress in real-time
5. Once complete, access your files in the respective format directories

## Output Structure

Generated files are organized in the `output` directory with subdirectories for each format:
- `/output/fhir/` - FHIR resources (R4, STU3, or DSTU2)
- `/output/hl7/` - HL7 v2.4 messages
- `/output/ccda/` - C-CDA documents
- `/output/csv/` - CSV files
- `/output/json/` - JSON files
- `/output/cpcds/` - CPCDS format files

Each format is generated based on your selection in the web interface.

## Technical Details

- Built with FastAPI and Python
- Uses the official Synthea JAR for patient generation
- Real-time progress updates via Server-Sent Events (SSE)
- Docker containerization for easy deployment
- Dynamic properties file management for Synthea configuration
- Modern responsive UI with CSS Grid and Flexbox
- Error handling and validation for all API endpoints

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Synthea Project](https://github.com/synthetichealth/synthea) for the synthetic patient generator
- MITRE Corporation for developing and maintaining Synthea

## Coming Soon

- Enhanced error handling and validation
- Additional format customization options
- Improved file management and cleanup
- Support for custom Synthea modules
