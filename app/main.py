from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import os
import json
from pathlib import Path
import logging
import shutil
from typing import List

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
async def root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_patients(
    num_patients: int = Form(...),
    years_of_history: int = Form(...),
    output_formats: List[str] = Form(...),
    state: str = Form("Massachusetts")  # Default to Massachusetts
):
    try:
        logger.info(f"Starting patient generation: {num_patients} patients, {years_of_history} years, formats: {output_formats}, state: {state}")
        
        # Clear previous output files but keep the directory
        for item in output_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                logger.error(f"Error clearing item {item}: {str(e)}")
        
        logger.info(f"Cleared contents of output directory: {output_dir}")

        # Base command
        cmd = [
            "java",
            "-jar",
            "/app/synthea-with-dependencies.jar",
            "-p", str(num_patients),
            "-a", "0-104",  # Set age range from birth to 104
            "--output-dir", str(output_dir)
        ]

        # Add export parameters based on selected formats
        for format in output_formats:
            if format == "FHIR_R4":
                cmd.extend(["--exporter.fhir.export", "true"])
                cmd.extend(["--exporter.fhir.use_r4", "true"])
            elif format == "FHIR_R4PLUS":
                cmd.extend(["--exporter.fhir.export", "true"])
                cmd.extend(["--exporter.fhir.use_r4", "true"])
                cmd.extend(["--exporter.fhir.use_us_core_ig", "true"])
            elif format == "FHIR_DSTU2":
                cmd.extend(["--exporter.fhir.export", "true"])
                cmd.extend(["--exporter.fhir.use_dstu2", "true"])
            elif format == "FHIR_STU3":
                cmd.extend(["--exporter.fhir.export", "true"])
                cmd.extend(["--exporter.fhir.use_stu3", "true"])
            elif format == "CSV":
                cmd.extend(["--exporter.csv.export", "true"])
            elif format == "CPCDS":
                cmd.extend(["--exporter.cpcds.export", "true"])
            elif format == "CCDA":
                cmd.extend(["--exporter.ccda.export", "true"])
            elif format == "TEXT":
                cmd.extend(["--exporter.text.export", "true"])
            elif format == "CDATEXT":
                cmd.extend(["--exporter.text.export.cdatext", "true"])
            elif format == "HTML":
                cmd.extend(["--exporter.html.export", "true"])
            elif format == "HL7":
                cmd.extend(["--exporter.hospital.fhir.export", "true"])
                cmd.extend(["--exporter.practitioner.fhir.export", "true"])
                cmd.extend(["--exporter.hospital.hl7v2.export", "true"])

        # Add state parameter
        cmd.append(state)

        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Output directory exists: {output_dir.exists()}")
        logger.info(f"Output directory permissions: {oct(output_dir.stat().st_mode)[-3:]}")

        # Run Synthea
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd="/app"  # Set working directory explicitly
        )
        stdout, stderr = process.communicate()
        
        logger.info(f"Synthea stdout: {stdout}")
        if stderr:
            logger.error(f"Synthea stderr: {stderr}")

        if process.returncode != 0:
            logger.error(f"Synthea failed with return code {process.returncode}")
            return {"status": "error", "message": stderr or "Unknown error occurred"}

        # Get list of generated files
        files = []
        for root, _, filenames in os.walk(output_dir):
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(output_dir)
                files.append(str(rel_path))
        
        logger.info(f"Found files in output directory: {files}")

        if not files:
            logger.warning("No files were generated")
            # List directory contents for debugging
            logger.info(f"Output directory contents: {list(output_dir.glob('**/*'))}")
            return {"status": "error", "message": "No files were generated"}

        return {
            "status": "success",
            "message": "Generated successfully",
            "files": files
        }
    except Exception as e:
        logger.error(f"Error generating patients: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/download/{filename:path}")
async def download_file(filename: str):
    try:
        file_path = output_dir / filename
        logger.info(f"Attempting to download file: {file_path}")
        logger.info(f"File exists: {file_path.exists()}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found"}
            
        return FileResponse(path=file_path, filename=file_path.name)
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
