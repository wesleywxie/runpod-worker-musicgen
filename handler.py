import base64
import json
import logging
import os
from pathlib import Path
from typing import Dict

import runpod

from predict import generate_melody
from utils import is_valid_url

logger = logging.getLogger(__name__)

REFRESH_WORKER = os.environ.get("REFRESH_WORKER", "false").lower() == "true"


def validate_input(job_input):
    """
    Validates the input for the handler function.

    Args:
        job_input (dict): The input data to validate.

    Returns:
        tuple: A tuple containing the validated data and an error message, if any.
               The structure is (validated_data, error_message).
    """
    # Validate if job_input is provided
    if job_input is None:
        return None, "Please provide input"

    # Check if input is a string and try to parse it as JSON
    if isinstance(job_input, str):
        try:
            job_input = json.loads(job_input)
        except json.JSONDecodeError:
            return None, "Invalid JSON format in input"

    # Validate 'prompt' in input
    prompt = job_input.get("prompt")
    if prompt is None:
        return None, "Missing 'prompt' parameter"

    # Validate 'duration' in input
    duration = job_input.get("duration")
    if duration is None:
        return None, "Missing 'duration' parameter"

    # Validate 'sample' in input, if provided
    sample = job_input.get("sample")
    if sample is not None:
        if not is_valid_url(sample):
            return (
                None,
                "'sample' must be a valid audio url",
            )

    # Return validated data and no error
    return {"prompt": prompt, "duration": duration, "sample": sample}, None


def process_output_mp3(mp3_filename: str) -> Dict[str, str]:
    """
    Reads an MP3 file from the given path, encodes its contents in base64,
    deletes the original file, and returns a JSON-compatible dictionary
    containing the encoded content.

    Args:
        mp3_filename (str): The path to the MP3 file.

    Returns:
        dict: A dictionary with keys:
              - "status": "success" or "error" (or "warning" if deletion fails)
              - "message": Base64-encoded MP3 content or an error message.
    """
    file_path = Path(mp3_filename)
    if not file_path.exists() or not file_path.is_file():
        logger.error(f"MP3 file does not exist: {mp3_filename}")
        return {
            "status": "error",
            "message": f"the mp3 does not exist in the specified output folder: {mp3_filename}"
        }

    try:
        mp3_bytes = file_path.read_bytes()
        encoded_content = base64.b64encode(mp3_bytes).decode("utf-8")
    except Exception as e:
        logger.exception(f"Error reading or encoding MP3 file {mp3_filename}: {e}")
        return {
            "status": "error",
            "message": f"Failed to read and encode MP3: {str(e)}"
        }

    try:
        file_path.unlink()  # delete the file
        logger.info("musicgen-worker - the mp3 was generated, converted to base64, and deleted")
    except Exception as e:
        logger.exception(f"Error deleting MP3 file {mp3_filename}: {e}")
        # Optionally, you might still return success with a warning, or treat this as an error.
        return {
            "status": "warning",
            "message": f"MP3 encoded successfully, but failed to delete the original file: {str(e)}"
        }

    return {
        "status": "success",
        "message": encoded_content,
    }


def handler(job):
    job_input = job['input']

    # Make sure that the input is valid
    validated_data, error_message = validate_input(job_input)
    if error_message:
        return {"error": error_message}

    prompt = validated_data.get('prompt')
    duration = validated_data.get('duration')
    sample = validated_data.get('sample')

    # Queue the workflow
    try:
        mp3_filename = generate_melody(prompt, duration, sample)
        logger.info(f"musicgen-worker - generated mp3 file - {mp3_filename}")
        mp3_result = process_output_mp3(mp3_filename)
    except Exception as e:
        return {"error": f"Error generating mp3: {str(e)}"}

    result = {**mp3_result, "refresh_worker": REFRESH_WORKER}
    return result


runpod.serverless.start({"handler": handler})
