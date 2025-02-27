from dotenv import load_dotenv
import os 

load_dotenv()

PRIMARY_MODEL = {
    "provider": "OpenAI",
    "model_name": "gpt-4o-mini",
    "temperature": 0,
}

SECONDARY_MODEL = {
    "provider": "Claude",
    "model_name": "claude-3-haiku-20240307",
    "temperature": 0,
}

Images_MODEL = {
    "provider": "Claude",
    "model_name": "claude-3-5-sonnet-20241022",
    "temperature": 0.5,
}
