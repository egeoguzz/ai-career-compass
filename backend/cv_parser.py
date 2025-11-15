import fitz  # PyMuPDF
import docx
import io
import logging
import os

# It's a best practice to configure logging at the application's entry point (e.g., main.py),
# but for module-level clarity, we can get the logger instance here.
logger = logging.getLogger(__name__)


class CVParserError(Exception):
    """Custom exception for errors encountered during CV parsing."""
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from the byte data of a PDF file.
    Hardened against corrupted or invalid files.
    """
    try:
        text = ""
        # Open PDF from in-memory bytes
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()

        if not text.strip():
            logger.warning("Extracted text from PDF is empty. The file might be image-based or blank.")
            raise CVParserError("Failed to extract text from PDF. The file may be empty or contain only images.")

        return text
    except Exception as e:
        logger.error(f"Failed to parse PDF file: {e}", exc_info=True)
        # 'from e' preserves the original exception's stack trace, which is crucial for debugging.
        raise CVParserError("Invalid or corrupted PDF file provided.") from e


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from the byte data of a DOCX file.
    Hardened against corrupted or invalid files.
    """
    try:
        # The 'docx' library expects a file-like object, so we use io.BytesIO to wrap the byte stream.
        document = docx.Document(io.BytesIO(file_bytes))
        full_text = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(full_text)

        if not text.strip():
            logger.warning("Extracted text from DOCX is empty. The file might be blank.")
            raise CVParserError("Failed to extract text from DOCX. The file may be empty.")

        return text
    except Exception as e:
        logger.error(f"Failed to parse DOCX file: {e}", exc_info=True)
        raise CVParserError("Invalid or corrupted DOCX file provided.") from e


# --- Dispatcher Function (Improved Design) ---

# A dictionary mapping file extensions to their respective parser functions.
# This makes the code more scalable and maintainable.
FILE_PARSERS = {
    ".pdf": extract_text_from_pdf,
    ".docx": extract_text_from_docx,
}


def parse_cv(filename: str, file_bytes: bytes) -> str:
    """
    Dispatches the CV parsing to the appropriate function based on the file extension.
    This acts as the single entry point for this module.
    """
    # Extract and normalize the file extension (e.g., '.PDF' -> '.pdf')
    _, extension = os.path.splitext(filename)
    extension = extension.lower()

    parser_function = FILE_PARSERS.get(extension)

    if not parser_function:
        logger.error(f"Unsupported file extension: '{extension}'")
        raise CVParserError(f"Unsupported file format '{extension}'. Please use PDF or DOCX.")

    return parser_function(file_bytes)