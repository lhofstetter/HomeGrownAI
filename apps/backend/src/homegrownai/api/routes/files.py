from pathlib import Path
from typing import Annotated
from uuid import UUID

from anyio import open_file
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import and_

from homegrownai.ai.engine import InferenceEngine
from homegrownai.database.db import DBSession
from homegrownai.database.dependencies import get_db_session
from homegrownai.database.document import Document
from homegrownai.database.document_chunk import DocumentChunk
from homegrownai.database.user import User
from homegrownai.security.security import get_current_user
from homegrownai.services.documents import (
    enforce_restrictions_and_determine_file_type,
    save_file_path,
)

files_router = APIRouter(
    prefix="/files",
    tags=["files"],
)

upload_directory = Path("./uploads")

if not upload_directory.exists():
    upload_directory.mkdir()

maximum_file_size_limit_in_bytes = 10000000  # 10 MB


@files_router.get("/files")
async def get_files(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[DBSession, Depends(get_db_session)],
):
    with session as db:
        user: User | None = db.query(User).filter(User.id == current_user.id).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token! Please log in again.",
                headers={"WWW-Authenticate": "Bearer token error!"},
            )

        for doc in user.documents:
            m = {
                "id": doc.id,
                "original_file_name": doc.original_file_name,
                "title": doc.title,
            }

            yield m


@files_router.get("/file/{file_id}")
async def get_file(
    file_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[DBSession, Depends(get_db_session)],
):

    with session as db:
        document: Document | None = (
            db.query(Document)
            .filter(and_(Document.id == file_id, Document.user_id == current_user.id))
            .first()
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource is not found on the server!",
            )
        else:
            async with await open_file(document.file_path, "rb") as f:
                content = f.read()

            m = {"document_id": document.id, "content": content}

            return m


@files_router.post("/upload")
async def upload_file(
    file: UploadFile,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[DBSession, Depends(get_db_session)],
):
    file_type = await enforce_restrictions_and_determine_file_type(file)
    file_path, file_id = await save_file_path(current_user, file_type)

    # basically copied from https://oneuptime.com/blog/post/2026-01-26-fastapi-file-uploads/view
    uploaded_file = await file.read()

    async with await open_file(file_path, "wb") as f:
        await f.write(uploaded_file)

    e: InferenceEngine = request.app.state.inference_engine

    with session as db:
        d = Document(
            id=file_id,
            title=file_path.stem,
            original_file_name=str(file.filename),
            user=current_user,
            file_path=file_path,
            embedding_model_id=e.embedding_engine.model_config.model,
        )
        index = 0

        async for (
            original_content,
            embedding_gen,
            positions,
            is_last,
        ) in e.generate_embeddings(file_path):
            async for output in embedding_gen:
                dc = DocumentChunk(
                    document_id=file_id,
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


@files_router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[DBSession, Depends(get_db_session)],
):
    if len(file_id) > 36:
        raise HTTPException(
            status_code=400,
            detail="File ID is too long! It needs to be less than or equal to 36 characters in length!",
        )

    with session as db:
        d: Document | None = (
            db.query(Document)
            .filter(and_(Document.id == file_id, User.id == current_user.id))
            .first()
        )

        if d == None:
            raise HTTPException(
                status_code=400,
                detail="An error occurred when attempting to delete the file.",
            )
        else:
            db.delete(d)
            db.commit()

    return {
        "result": "File deletion success!",
    }
