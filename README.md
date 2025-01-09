# Synthea Patient Generator Web Interface

A web-based interface for generating synthetic patient data using the Synthea patient generator.

## Features

- Simple web interface for generating synthetic patient data
- Select number of patients and target state
- Choose from multiple output formats:
  - FHIR R4 (Latest standard)
  - FHIR STU3
  - FHIR DSTU2
  - CCDA
  - HL7 v2.4
  - CSV
  - JSON
  - CPCDS
- Option to remove numbers from patient names
- Real-time progress updates during generation
- Download all generated files as a ZIP archive
- Non-persistent storage (files are cleared between sessions)

## Requirements

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Synthea-patient-generator.git
   cd Synthea-patient-generator
   ```

2. Build and start the container:
   ```bash
   docker compose up
   ```

3. Access the web interface at:
   ```
   http://localhost:8000
   ```

## Usage

1. Select the number of patients to generate
2. Choose a state (defaults to Rhode Island)
3. Select desired output formats
4. Optionally check "No numbers in names" to remove numbers from generated names
5. Click "Generate" to start the process
6. Monitor progress in real-time
7. Download generated files using the "Download All Files" button
8. Files are automatically cleared when the container is restarted

## Notes

- Generated files are stored in a temporary filesystem and do not persist between container restarts
- The interface automatically refreshes the file list after generation
- Error messages and generation progress are displayed in real-time
- The download button is only enabled when files are available

## Development

To modify the application:
1. Edit files in the `app` directory for backend changes
2. Edit files in the `static` directory for frontend changes
3. The application will automatically reload when changes are detected

## License

[Insert your license information here]
