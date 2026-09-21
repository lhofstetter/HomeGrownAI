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

    user_directory = Path(upload_directory, Path(current_user.username))

    if not user_directory.exists():
        user_directory.mkdir()

    file_path = Path()

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
        # read image with multimodal model
        await file.seek(0)

        uploaded_file = await file.read()

        if file_type == "application/pdf":
            file_input_parameter = "pdf"

            pdf_directory = Path(user_directory, Path("pdfs"))

            if not pdf_directory.exists():
                pdf_directory.mkdir()

            file_id = str(uuid4())
            file_name = file_id + "_" + str(file.filename).split(".")[0] + ".pdf"

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
            file_name = file_id + "_" + str(file.filename).split(".")[0]

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
                file_name = file_id + "_" + str(file.filename).split(".")[0] + ".html"
            elif file_type == "text/css":
                file_name = file_id + "_" + str(file.filename).split(".")[0] + ".css"
            else:
                file_name = file_id + "_" + str(file.filename).split(".")[0] + ".js"

            file_path = Path(webpage_directory, file_name)

            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        elif file_type == "text/markdown":
            file_input_parameter = "plaintext"

            markdown_directory = Path(user_directory, Path("markdown"))

            if not markdown_directory.exists():
                markdown_directory.mkdir()

            file_id = str(uuid4())
            file_name = file_id + "_" + str(file.filename).split(".")[0] + ".md"

            file_path = Path(markdown_directory, file_name)
            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)
        else:
            plaintext_or_source_directory = Path(
                user_directory, Path("plaintext_or_source_directory")
            )

            if not plaintext_or_source_directory.exists():
                plaintext_or_source_directory.mkdir()

            file_id = str(uuid4())
            file_name = (
                file_id
                + "_"
                + str(file.filename).split(".")[0]
                + str(file.filename).split(".")[-1]
            )

            file_path = Path(plaintext_or_source_directory, file_name)

            async with await open_file(file_path, "wb") as f:
                await f.write(uploaded_file)

        e: InferenceEngine = request.app.state.engine

        with session as db:
            d = Document(
                title=file_name,
                user=current_user,
                embedding_model_id=e.embedding_engine.model_config.model,
            )
            index = 0

            async for embedding_gen, positions, is_last in e.generate_embeddings(
                file_path, file_input_parameter
            ):
                async for output in embedding_gen:
                    dc = DocumentChunk(
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
        return HTTPException(status_code=415, detail="File type is not allowed!")
