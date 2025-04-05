import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno desde el .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no está definido en el archivo .env")

# Crear cliente OpenAI
client = OpenAI(api_key=api_key)

# Llamada al modelo gpt-4o
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Eres un asistente de mantenimiento industrial."},
        {"role": "user", "content": "Genera un procedimiento para hacer mantenimiento a una UPS trifásica."}
    ]
)

# Mostrar la respuesta
print(response.choices[0].message.content)

