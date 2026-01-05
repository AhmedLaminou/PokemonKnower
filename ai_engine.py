"""
AI Engine for Pokémon Knower
Handles Vision-Language Model (VLM) tasks using LangChain and OpenRouter/OpenAI.
"""
import base64
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class PokemonIdentifier:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        base_url = "https://openrouter.ai/api/v1" if os.environ.get('OPENROUTER_API_KEY') else None
        
        # Use a vision-capable model that is efficient
        model_name = "google/gemini-flash-1.5-8b" if os.environ.get('OPENROUTER_API_KEY') else "gpt-4o-mini"
        # Force gpt-4o-mini for robust JSON output if using OpenRouter
        if os.environ.get('OPENROUTER_API_KEY'):
             model_name = "openai/gpt-4o-mini"

        if self.api_key:
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                base_url=base_url,
                temperature=0.0,
                max_tokens=500
            )
        else:
            print("Warning: No AI API Key found. VLM features disabled.")
            self.llm = None

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def identify_pokemon(self, image_path):
        """
        Identify a Pokémon from an image using VLM.
        Returns a dictionary with name, confidence, and metadata.
        """
        if not self.llm:
            return None

        try:
            base64_image = self._encode_image(image_path)
            
            prompt = """
            Look at this image. Identify if there is a Pokémon in it.
            
            Return the result valid JSON format ONLY, like this:
            {
                "name": "Pikachu",
                "confidence": 98.5,
                "is_pokemon": true,
                "is_shiny": false,
                "description": "A brief 1-sentence description of visual appearance."
            }
            
            If it is NOT a Pokémon (or just a generic animal/object), set "is_pokemon": false and "name": "Unknown".
            If the coloring matches the "Shiny" variation of the Pokémon, set "is_shiny": true.
            
            Do not include markdown formatting (```json). Just the raw JSON string.
            """
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            )
            
            response = self.llm.invoke([message])
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                print(f"VLM JSON Parse Error: {content}")
                return None
            
        except Exception as e:
            print(f"VLM Error: {e}")
            return None
