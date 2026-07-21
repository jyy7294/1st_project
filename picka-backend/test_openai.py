import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model=os.getenv("OPENAI_MODEL"),
    input="안녕! 한 줄로 자기소개해."
)

print(response.output_text)