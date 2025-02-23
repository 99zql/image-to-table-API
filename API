from fastapi import FastAPI, HTTPException
import requests
from io import BytesIO
from PIL import Image

app = FastAPI()

@app.get("/imagetotable/imageurl")
def image_to_table(image_url: str):
    try:
        # Baixar a imagem
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGBA")
        
        # Processar pixels
        pixels = []
        width, height = image.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = image.getpixel((x, y))
                pixels.append({"x": x, "y": y, "color": (r, g, b), "transparency": a})
        
        return {"width": width, "height": height, "pixels": pixels}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erro ao baixar a imagem: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem: {str(e)}")

# Para rodar localmente: uvicorn nome_do_arquivo:app --reload
