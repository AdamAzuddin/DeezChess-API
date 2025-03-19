# app/routes/pgn_upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.post("/pgn_upload")
async def upload_pgn(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        pgn_text = contents.decode("utf-8")

        # Optional: Save to file
        with open("uploaded_game.pgn", "w", encoding="utf-8") as f:
            f.write(pgn_text)

        return PlainTextResponse("success", status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
