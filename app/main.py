from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import os
import json
from pathlib import Path
import logging
import shutil
from typing import List
import asyncio
from datetime import datetime
import random
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import HTTPException
import time
import zipfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
static_dir = Path("/app/static")
if not static_dir.exists():
    logger.error(f"Static directory not found at {static_dir.absolute()}")
    static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/output", StaticFiles(directory="/app/output"), name="output")
templates = Jinja2Templates(directory="/app/static")

# Ensure output directory exists with absolute path
output_dir = Path("/app/output").absolute()

def ensure_output_directories():
    """Create output directory if it doesn't exist."""
    output_dir = Path("/app/output")
    output_dir.mkdir(exist_ok=True)
    # Directories are created in Dockerfile

jar_path = "/app/synthea-with-dependencies.jar"
properties_file = "/app/synthea.properties"

async def create_default_properties():
    default_properties = """
exporter.baseDirectory = ./output/
exporter.metadata.export = false
exporter.fhir.export = false
exporter.fhir_stu3.export = false
exporter.fhir_dstu2.export = false
exporter.ccda.export = false
exporter.json.export = false
exporter.csv.export = false
exporter.cpcds.export = false
exporter.hl7.export = false
exporter.hl7.version = 2.4
exporter.html.export = false
exporter.text.export = false
exporter.text.per_encounter_export = false
exporter.clinical_note.export = false
exporter.hospital.fhir.export = false
exporter.practitioner.fhir.export = false
exporter.years_of_history = 0
exporter.split_records = false
""".strip()

    with open(properties_file, 'w') as f:
        f.write(default_properties)

@app.on_event("startup")
async def startup_event():
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Create initial properties file
    await create_default_properties()

class GenerateRequest(BaseModel):
    num_patients: int
    state: str
    no_numbers: bool = False
    output_formats: List[str]

async def update_properties_file(formats):
    # Create default properties if file doesn't exist
    if not os.path.exists(properties_file):
        await create_default_properties()

    with open(properties_file, 'r') as f:
        properties = f.read()

    # Create a dictionary of properties
    props = {}
    for line in properties.splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            props[key.strip()] = value.strip()

    # Reset all exporters to false
    for key in props:
        if key.endswith('.export'):
            props[key] = 'false'

    # Enable selected formats
    enabled_exporters = set()
    for fmt in formats:
        if fmt == "FHIR_R4" and "fhir" not in enabled_exporters:
            props['exporter.fhir.export'] = 'true'
            props['exporter.fhir.use_r4'] = 'true'
            enabled_exporters.add("fhir")
        elif fmt == "FHIR_STU3" and "fhir" not in enabled_exporters:
            props['exporter.fhir.export'] = 'true'
            props['exporter.fhir.use_stu3'] = 'true'
            enabled_exporters.add("fhir")
        elif fmt == "FHIR_DSTU2" and "fhir" not in enabled_exporters:
            props['exporter.fhir.export'] = 'true'
            props['exporter.fhir.use_dstu2'] = 'true'
            enabled_exporters.add("fhir")
        elif fmt == "CCDA":
            props['exporter.ccda.export'] = 'true'
        elif fmt == "CSV":
            props['exporter.csv.export'] = 'true'
        elif fmt == "JSON":
            props['exporter.json.export'] = 'true'
        elif fmt == "CPCDS":
            props['exporter.cpcds.export'] = 'true'
        elif fmt == "HL7":
            props['exporter.hl7.export'] = 'true'
            props['exporter.hl7.version'] = '2.4'

    # Write back to file
    with open(properties_file, 'w') as f:
        for key, value in props.items():
            f.write(f"{key} = {value}\n")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "output_dir": str(output_dir)
        }
    )

@app.post("/generate")
async def generate_patients(request: GenerateRequest):
    async def stream_output():
        try:
            # Verify Synthea JAR exists
            if not os.path.exists(jar_path):
                yield "data: Error: Synthea JAR file not found\n\n"
                return

            # Ensure output directories exist
            ensure_output_directories()

            # Create directories for selected formats
            format_directories = {
                'FHIR_R4': 'fhir',
                'FHIR_STU3': 'fhir',
                'FHIR_DSTU2': 'fhir',
                'CCDA': 'ccda',
                'CSV': 'csv',
                'JSON': 'json',
                'CPCDS': 'cpcds',
                'HL7': 'hl7'
            }
            
            for fmt in request.output_formats:
                if fmt in format_directories:
                    os.makedirs(os.path.join(output_dir, format_directories[fmt]), exist_ok=True)

            # Update properties file with selected formats
            await update_properties_file(request.output_formats)

            # Set up the command with properties file
            cmd = [
                "java", "-jar", jar_path,
                "-p", str(request.num_patients),
                "-s", "0",  # Default seed
                "-c", properties_file  # Use our properties file
            ]

            if request.state:
                cmd.append(request.state)

            if request.no_numbers:
                cmd.append("--generate.append_numbers_to_person_names=false")

            # Send the command to the frontend for display
            yield f"data: command: {' '.join(cmd)}\n\n"

            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                yield f"data: {line.decode()}\n\n"

            await process.wait()
            yield "data: Generation complete\n\n"

        except Exception as e:
            logging.error(f"Error generating patients: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return EventSourceResponse(stream_output())

@app.get("/fhir-files")
async def list_fhir_files():
    try:
        ensure_output_directories()
        fhir_dir = output_dir / "fhir"
        if not fhir_dir.exists():
            return {"files": []}
            
        files = []
        for file in fhir_dir.glob("*.json"):
            if file.name.startswith("practitionerInformation") or file.name.startswith("hospitalInformation"):
                continue
            stat = file.stat()
            files.append({
                "name": file.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing FHIR files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing FHIR files: {str(e)}")

@app.get("/download/{filename}")
async def download_fhir_file(filename: str):
    try:
        ensure_output_directories()
        file_path = output_dir / "fhir" / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path=file_path, filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.get("/download-all")
async def download_fhir_directory():
    try:
        ensure_output_directories()
        # Create a temporary zip file
        zip_filename = f"fhir_files_{int(time.time())}.zip"
        zip_path = output_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            fhir_dir = output_dir / "fhir"
            if fhir_dir.exists():
                for file in fhir_dir.glob("*.json"):
                    if not (file.name.startswith("practitionerInformation") or 
                           file.name.startswith("hospitalInformation")):
                        zipf.write(file, arcname=file.name)

        # Return the zip file
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            background=BackgroundTasks([lambda: zip_path.unlink(missing_ok=True)])
        )
    except Exception as e:
        logger.error(f"Error creating zip file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating zip file: {str(e)}")
