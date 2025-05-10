import os
import shutil
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException

def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Save an uploaded file to the specified destination.
    
    Args:
        upload_file: The uploaded file
        destination: The destination path
        
    Returns:
        str: The path to the saved file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Save the file
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        return destination
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    finally:
        upload_file.file.close()

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate that the file has an allowed extension.
    
    Args:
        filename: The name of the file
        allowed_extensions: List of allowed extensions (e.g., [".pdf", ".png"])
        
    Returns:
        bool: True if file type is allowed, False otherwise
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions

def get_file_extension(filename: str) -> str:
    """
    Get the file extension of a filename.
    
    Args:
        filename: The name of the file
        
    Returns:
        str: The file extension (e.g., ".pdf")
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()

def delete_file(file_path: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: The path to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False
