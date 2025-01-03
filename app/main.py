from fastapi import FastAPI, Request, Form, HTTPException
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
static_dir = Path("static")
if not static_dir.exists():
    logger.error(f"Static directory not found at {static_dir.absolute()}")
    static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Ensure output directory exists with absolute path
output_dir = Path("/app/output").absolute()
output_dir.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def process_output(process):
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        yield f"data: {line.decode().strip()}\n\n"

@app.post("/generate")
async def generate_patients(
    num_patients: int = Form(...),
    years_of_history: int = Form(...),
    output_formats: List[str] = Form(...),
    state: str = Form("Massachusetts"),
    no_numbers: bool = Form(True)
):
    try:
        # Clear output directory
        for item in output_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Base command with common parameters
        cmd = [
            "java", "-jar", "/app/synthea-with-dependencies.jar",
            state,  # State as first positional argument
            "-p", str(num_patients),
            "-s", str(datetime.now().microsecond),  # Random seed
            "--generate.timesteps", str(years_of_history * 12),  # Convert years to months
            "--exporter.baseDirectory", str(output_dir),
        ]

        # Add no-numbers option if selected
        if no_numbers:
            cmd.append("--generate.append_numbers_to_person_names=false")

        # Add export parameters based on selected formats
        for format in sorted(output_formats):  # Sort formats alphabetically
            if format == "FHIR_R4":
                cmd.append("--exporter.fhir.export=true")
                cmd.append("--exporter.fhir.use_r4=true")
            elif format == "FHIR_R4PLUS":
                cmd.append("--exporter.fhir.export=true")
                cmd.append("--exporter.fhir.use_r4=true")
                cmd.append("--exporter.fhir.use_us_core_ig=true")
            elif format == "FHIR_DSTU2":
                cmd.append("--exporter.fhir.export=true")
                cmd.append("--exporter.fhir.use_dstu2=true")
            elif format == "FHIR_STU3":
                cmd.append("--exporter.fhir.export=true")
                cmd.append("--exporter.fhir.use_stu3=true")
            elif format == "CSV":
                cmd.append("--exporter.csv.export=true")
            elif format == "CPCDS":
                cmd.append("--exporter.cpcds.export=true")
            elif format == "CCDA":
                cmd.append("--exporter.ccda.export=true")
            elif format == "TEXT":
                cmd.append("--exporter.text.export=true")
            elif format == "CDATEXT":
                cmd.append("--exporter.text.export.cdatext=true")
            elif format == "HTML":
                cmd.append("--exporter.html.export=true")
            elif format == "HL7":
                cmd.append("--exporter.hospital.fhir.export=true")
                cmd.append("--exporter.practitioner.fhir.export=true")
                cmd.append("--exporter.hospital.hl7v2.export=true")

        # Log the command being executed
        logger.info(f"Executing command: {' '.join(cmd)}")

        # Start process with pipe for output
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd="/app"  # Set working directory explicitly
        )

        return StreamingResponse(
            process_output(process),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error generating patients: {str(e)}")
        logger.error(f"Command was: {' '.join(cmd)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
