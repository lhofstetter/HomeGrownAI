from pathlib import Path
from typing import Annotated
from uuid import uuid4

from anyio import open_file
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from magic import from_buffer

from homegrownai.ai.engine import InferenceEngine
from homegrownai.database.db import DBSession
from homegrownai.database.dependencies import get_db_session
from homegrownai.database.document import Document
from homegrownai.database.document_chunk import DocumentChunk
from homegrownai.database.user import User
from homegrownai.exceptions import UploadError
from homegrownai.security.security import get_current_user

files_router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_directory = Path("./uploads")

if not upload_directory.exists():
    upload_directory.mkdir()


maximum_file_size_limit_in_bytes = 10000000  # 10 MB


@files_router.post("/upload")
async def upload_file(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile,
    session: Annotated[DBSession, Depends(get_db_session)],
):
    if file.filename == None:
        raise UploadError

    untrusted_upload_bytes = await file.read(2048)

    file_type: str = from_buffer(
        untrusted_upload_bytes, mime=True
    )  # technically, UploadFile has a content_type field with the MIME/media type... but probably best to verify for ourselves

    user_directory = Path(upload_directory, Path(str(current_user.id)))

    if not user_directory.exists():
        user_directory.mkdir()

    file_path = Path()

    # basically copied from https://oneuptime.com/blog/post/2026-01-26-fastapi-file-uploads/view
    size = 0
    await file.seek(0)

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

    await file.seek(0)

    if (
        "pdf" in file_type
        or "msword" in file_type
        or "vnd.openxmlformats-officedocument.wordprocessingml.document" in file_type
        or "html" in file_type
        or "markdown" in file_type
        or "javascript" in file_type
        or "plain" in file_type
        or "css" in file_type
    ):
        await file.seek(0)

        uploaded_file = await file.read()

        if file_type == "application/pdf":
            file_input_parameter = "pdf"

            pdf_directory = Path(user_directory, Path("pdfs"))

            if not pdf_directory.exists():
                pdf_directory.mkdir()

            file_id = str(uuid4())
            file_name = file_id + ".pdf"

            file_path = Path(pdf_directory, file_name)

            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        elif (
            file_type == "application/msword"
            or file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            file_input_parameter = "word_document"

            document_directory = Path(user_directory, Path("docs"))

            if not document_directory.exists():
                document_directory.mkdir()

            file_id = str(uuid4())
            file_name = file_id

            if file_type == "application/msword":
                file_name += ".doc"
            else:
                file_name += ".docx"

            file_path = Path(document_directory, file_name)
            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        elif (
            file_type == "text/html"
            or file_type == "text/css"
            or file_type == "text/javascript"
        ):
            if file_type == "text/html":
                file_input_parameter = "webpage"
            else:
                file_input_parameter = "plaintext"

            webpage_directory = Path(user_directory, Path("webpages"))

            if not webpage_directory.exists():
                webpage_directory.mkdir()

            file_id = str(uuid4())

            if file_type == "text/html":
                file_name = file_id + ".html"
            elif file_type == "text/css":
                file_name = file_id + ".css"
            else:
                file_name = file_id + ".js"

            file_path = Path(webpage_directory, file_name)

            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        elif file_type == "text/markdown":
            file_input_parameter = "plaintext"

            markdown_directory = Path(user_directory, Path("markdown"))

            if not markdown_directory.exists():
                markdown_directory.mkdir()

            file_id = str(uuid4())
            file_name = file_id + ".md"

            file_path = Path(markdown_directory, file_name)
            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        else:
            file_input_parameter = "plaintext"

            plaintext_or_source_directory = Path(
                user_directory, Path("plaintext_or_source_directory")
            )

            if not plaintext_or_source_directory.exists():
                plaintext_or_source_directory.mkdir()

            file_id = str(uuid4())
            file_extension = ""

            if "." not in str(file.filename):  # there's no file extension!
                file_extension += ".txt"
            else:
                file_extension += str(file.filename).split(".")[-1]
            file_name = file_id + file_extension

            file_path = Path(plaintext_or_source_directory, file_name)

            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)

        e: InferenceEngine = request.app.state.inference_engine

        with session as db:
            d = Document(
                title=file_name,
                original_file_name=str(file.filename),
                user=current_user,
                embedding_model_id=e.embedding_engine.model_config.model,
            )
            index = 0

            async for (
                original_content,
                embedding_gen,
                positions,
                is_last,
            ) in e.generate_embeddings(file_path, file_input_parameter):
                async for output in embedding_gen:
                    dc = DocumentChunk(
                        content=original_content,
                        embedding=output.outputs.embedding,
                        column=positions["start"]["column"],
                        line=positions["start"]["line"],
                        offset=positions["start"]["offset"],
                        index=index,
                    )
                    index += 1

                    d.embeddings.append(dc)

                if is_last:
                    db.add(d)
                    db.commit()

        return {
            "result": "File upload success!",
        }
    else:
        raise HTTPException(status_code=415, detail="File type is not allowed!")


@files_router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[DBSession, Depends(get_db_session)],
):

    pass
