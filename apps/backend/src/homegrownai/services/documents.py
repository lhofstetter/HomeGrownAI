from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from homegrownai.database.user import User
from homegrownai.exceptions import UploadError
from magic import from_buffer

upload_directory = Path("./uploads")

if not upload_directory.exists():
    upload_directory.mkdir()

maximum_file_size_limit_in_bytes = 10000000  # 10 MB


async def enforce_restrictions_and_determine_file_type(file: UploadFile) -> str:
    if file.filename == None:
        raise UploadError

    untrusted_upload_bytes = await file.read(2048)

    file_type: str = from_buffer(
        untrusted_upload_bytes, mime=True
    )  # technically, UploadFile has a content_type field with the MIME/media type... but probably best to verify for ourselves

    size = 0
    await file.seek(0)

    # basically copied from https://oneuptime.com/blog/post/2026-01-26-fastapi-file-uploads/view
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)

        if size > maximum_file_size_limit_in_bytes:
            raise HTTPException(
                status_code=400,
                detail="File size is too large! Files must be less than or equal to 10 MB!",
            )

    if len(str(file.filename)) > 255:
        raise HTTPException(
            status_code=400,
            detail="File name is too long! It needs to be less than or equal to 255 characters in length!",
        )

    if "\x00" in str(file.filename) or file.filename == None:
        raise HTTPException(status_code=400, detail="Invalid filename!")

    if not (
        "pdf" in file_type
        or "msword" in file_type
        or "vnd.openxmlformats-officedocument.wordprocessingml.document" in file_type
        or "html" in file_type
        or "markdown" in file_type
        or "javascript" in file_type
        or "plain" in file_type
        or "css" in file_type
    ):
        raise HTTPException(status_code=400, detail="File type is not allowed!")

    await file.seek(0)

    return file_type


async def save_file_path(user: User, file_type: str) -> tuple[Path, str]:
    user_directory = Path(upload_directory, Path(str(user.id)))

    if not user_directory.exists():
        user_directory.mkdir()
    file_directory_parameter = ""

    match file_type:
        case "application/pdf":
            file_directory_parameter = "pdfs"
            file_extension = ".pdf"
        case "application/msword":
            file_directory_parameter = "docs"
            file_extension = ".docx"
        case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            file_directory_parameter = "docs"
            file_extension = ".docx"
        case "text/html":
            file_directory_parameter = "webpages"
            file_extension = ".html"
        case "text/css":
            file_directory_parameter = "webpages"
            file_extension = ".css"
        case "text/javascript":
            file_directory_parameter = "webpages"
            file_extension = ".js"
        case "text/markdown":
            file_directory_parameter = "docs"
            file_extension = ".md"

    type_of_file_directory = Path(user_directory, Path(file_directory_parameter))

    file_id = str(uuid4())
    file_name = file_id + file_extension

    if not type_of_file_directory.exists():
        type_of_file_directory.mkdir()

    file_path = Path(type_of_file_directory, file_name)

    return (file_path, file_id)
