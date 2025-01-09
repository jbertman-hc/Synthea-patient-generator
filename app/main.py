from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
import asyncio
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import shutil
import subprocess
import json
import random
from datetime import datetime
import time
import zipfile

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/output", StaticFiles(directory="/app/output"), name="output")
templates = Jinja2Templates(directory="/app/static")

# Constants
output_dir = "/app/output"
jar_path = "/app/synthea-with-dependencies.jar"
properties_file = "/app/synthea.properties"

# Global message queue for SSE
message_queue = []

class GenerateRequest(BaseModel):
    num_patients: int
    state: Optional[str] = None
    no_numbers: bool = False
    output_formats: List[str]

def ensure_output_directories():
    """Create output directory if it doesn't exist."""
    try:
        # Create main output directory
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created/verified output directory: {output_dir}")
        
        # Create subdirectories for each format
        subdirs = ['fhir', 'ccda', 'csv', 'json', 'cpcds', 'hl7']
        for subdir in subdirs:
            dir_path = os.path.join(output_dir, subdir)
            os.makedirs(dir_path, exist_ok=True)
            logging.info(f"Created/verified subdirectory: {dir_path}")
            
        # Set permissions
        for root, dirs, files in os.walk(output_dir):
            try:
                os.chmod(root, 0o777)
                logging.info(f"Set permissions for directory: {root}")
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o777)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o666)
            except Exception as e:
                logging.error(f"Error setting permissions: {e}")
                
    except Exception as e:
        logging.error(f"Error creating directories: {e}")
        raise

async def create_default_properties():
    default_properties = f"""
exporter.baseDirectory = {output_dir}/
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

async def update_properties_file(formats):
    """Update properties file with selected output formats."""
    # Map of format names to their property keys
    format_properties = {
        'fhir_r4': 'exporter.fhir.export',
        'fhir_stu3': 'exporter.fhir_stu3.export',
        'fhir_dstu2': 'exporter.fhir_dstu2.export',
        'ccda': 'exporter.ccda.export',
        'csv': 'exporter.csv.export',
        'json': 'exporter.json.export',
        'cpcds': 'exporter.cpcds.export',
        'hl7': 'exporter.hl7.export'
    }

    # Start with all properties disabled
    properties = {
        'exporter.baseDirectory': f'{output_dir}/',
        'exporter.years_of_history': '0',
        'exporter.split_records': 'false',
        'exporter.metadata.export': 'false',
        'exporter.html.export': 'false',
        'exporter.text.export': 'false',
        'exporter.text.per_encounter_export': 'false',
        'exporter.clinical_note.export': 'false',
        'exporter.hospital.fhir.export': 'false',
        'exporter.practitioner.fhir.export': 'false',
        'exporter.fhir.export': 'false',
        'exporter.fhir_stu3.export': 'false',
        'exporter.fhir_dstu2.export': 'false',
        'exporter.ccda.export': 'false',
        'exporter.csv.export': 'false',
        'exporter.json.export': 'false',
        'exporter.cpcds.export': 'false',
        'exporter.hl7.export': 'false',
        'exporter.hl7.version': '2.4'
    }
    
    # Enable only selected formats
    for fmt in formats:
        if fmt in format_properties:
            properties[format_properties[fmt]] = 'true'
            logging.info(f"Enabling format: {fmt}")

    # Write to file
    content = '\n'.join(f'{key} = {value}' for key, value in properties.items())
    logging.info(f"Writing properties:\n{content}")
    
    with open(properties_file, 'w') as f:
        f.write(content)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "output_dir": str(output_dir)
        }
    )

@app.get("/stream")
async def stream_output():
    """Stream output from the command execution."""
    async def event_generator():
        while True:
            if len(message_queue) > 0:
                message = message_queue.pop(0)
                if message == "CLOSE":
                    break
                yield {"data": message}
            await asyncio.sleep(0.01)  # Reduced sleep time
    
    return EventSourceResponse(event_generator())

@app.post("/generate")
async def generate_patients(request: GenerateRequest):
    """Generate synthetic patient data."""
    try:
        # Clear message queue
        message_queue.clear()
        
        # Create properties file
        await update_properties_file(request.output_formats)

        # Set up the command with properties file
        java_opts = os.getenv("JAVA_OPTS", "").split()
        cmd = [
            "java",
            *java_opts,
            "-cp", os.getenv("CLASSPATH", jar_path),
            "App",
        ]

        if request.no_numbers:
            cmd.append("--generate.append_numbers_to_person_names=false")
        cmd.extend(["-p", str(request.num_patients)])
        cmd.extend(["-c", properties_file])
        if request.state:
            cmd.append(request.state)

        # Send command to frontend
        message_queue.append(f"Running command: {' '.join(cmd)}")

        try:
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(output_dir)
            )

            # Stream stdout in real-time
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode().strip()
                if decoded_line:  # Only send non-empty lines
                    message_queue.append(decoded_line)

            # Get stderr output
            stderr_data = await process.stderr.read()
            if stderr_data:
                error_lines = stderr_data.decode().strip().split('\n')
                for line in error_lines:
                    if line.strip() and not line.startswith("SLF4J:"):  # Skip SLF4J messages
                        message_queue.append(f"Error: {line}")

            await process.wait()
            
            if process.returncode == 0:
                # Get list of generated files
                files = []
                for root, _, filenames in os.walk(output_dir):
                    for filename in filenames:
                        if filename.endswith(('.json', '.xml', '.csv', '.txt')):
                            rel_path = os.path.relpath(os.path.join(root, filename), output_dir)
                            files.append(rel_path)
                
                if files:
                    message_queue.append("Generated files:")
                    for file in files:
                        message_queue.append(f"- {file}")
                    message_queue.append("Generation complete")
                    message_queue.append("REFRESH_FILES")
                else:
                    message_queue.append("Warning: No files were generated")
            else:
                message_queue.append(f"Error: Process failed with exit code {process.returncode}")

            return {"status": "success"}

        except Exception as e:
            message_queue.append(f"Error: Failed to run Synthea - {str(e)}")
            return {"status": "error", "message": str(e)}

    except Exception as e:
        logging.error(f"Error in generate: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/cleanup")
async def cleanup_files():
    """Remove all generated files from the output directory."""
    try:
        if not os.path.exists(output_dir):
            logging.warning(f"Output directory does not exist: {output_dir}")
            return {"status": "success"}

        # Walk through output directory and remove all files
        for root, dirs, files in os.walk(output_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                    logging.info(f"Removed file: {name}")
                except Exception as e:
                    logging.error(f"Error removing file {name}: {e}")
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                    logging.info(f"Removed directory: {name}")
                except Exception as e:
                    logging.error(f"Error removing directory {name}: {e}")
        
        # Recreate necessary directories
        ensure_output_directories()
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error cleaning up files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_files")
async def list_fhir_files():
    """List all files in the output directory."""
    try:
        logging.info(f"Scanning directory: {output_dir}")
        if not os.path.exists(output_dir):
            logging.warning(f"Output directory does not exist: {output_dir}")
            return []

        files = []
        for root, _, filenames in os.walk(output_dir):
            for filename in filenames:
                if filename.endswith(('.json', '.xml', '.csv', '.txt', '.zip')):
                    try:
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, output_dir)
                        stat = os.stat(file_path)
                        
                        # Log file details for debugging
                        logging.info(f"Found file: {rel_path} ({stat.st_size} bytes)")
                        
                        files.append({
                            "name": rel_path,
                            "size": stat.st_size,
                            "modified": int(stat.st_mtime)
                        })
                    except Exception as e:
                        logging.error(f"Error processing file {filename}: {e}")
                        continue

        # Sort files by modification time (newest first)
        sorted_files = sorted(files, key=lambda x: x["modified"], reverse=True)
        logging.info(f"Found {len(sorted_files)} files")
        return sorted_files

    except Exception as e:
        logging.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename:path}")
async def download_fhir_file(filename: str):
    """Download a specific file from the output directory."""
    try:
        file_path = os.path.join(output_dir, filename)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(file_path, filename=os.path.basename(filename))
    except Exception as e:
        logging.error(f"Error downloading file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_all")
async def download_fhir_directory():
    """Download all files as a zip archive."""
    try:
        # Check if there are any files to download
        files = []
        for root, _, filenames in os.walk(output_dir):
            for filename in filenames:
                if filename.endswith(('.json', '.xml', '.csv', '.txt')):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, output_dir)
                    files.append((file_path, rel_path))
        
        if not files:
            raise HTTPException(status_code=404, detail="No files to download")

        # Create a temporary zip file
        zip_path = os.path.join(output_dir, "synthea_output.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, rel_path in files:
                zipf.write(file_path, rel_path)

        return FileResponse(
            zip_path,
            filename="synthea_output.zip",
            media_type='application/zip',
            background=BackgroundTasks()
        )
    except Exception as e:
        logging.error(f"Error creating zip archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))
