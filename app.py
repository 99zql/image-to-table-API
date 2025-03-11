from fastapi import FastAPI, HTTPException, Query
import requests
from io import BytesIO
from PIL import Image, ImageSequence

app = FastAPI()

@app.get("/imageapi")
def image_to_table(imageurl: str, resolution: float = Query(1.0, gt=0, le=10.0)):
    try:
        response = requests.get(imageurl, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        frames = {}
        width, height = image.size

        for i, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")

            new_width = max(1, int(width * resolution))
            new_height = max(1, int(height * resolution))
            frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

            pixels = []
            for y in range(new_height):
                for x in range(new_width):
                    r, g, b, a = frame.getpixel((x, y))
                    alpha = round(1 - (a / 255), 2)
                    alpha = int(alpha) if alpha == 0 else alpha

                    if alpha < 1:
                        pixels.append(f"{x},{y},{r},{g},{b},{alpha}")

            if pixels:
                frames[f"Frame {i+1}"] = ",".join(pixels)

        if not frames:
            return {"message": "A imagem não possui pixels visíveis."}

        return {"width": new_width, "height": new_height, **frames}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {e}")
