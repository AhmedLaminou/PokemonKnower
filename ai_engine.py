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

class PokemonStoryteller:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        base_url = "https://openrouter.ai/api/v1" if os.environ.get('OPENROUTER_API_KEY') else None
        
        # Use a text-optimized model
        model_name = "google/gemini-flash-1.5" if os.environ.get('OPENROUTER_API_KEY') else "gpt-4o-mini"
        if os.environ.get('OPENROUTER_API_KEY'):
             # Prefer a cheaper but capable model for stories, or user defined
             model_name = "openai/gpt-4o-mini" # Consistently reliable

        if self.api_key:
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                base_url=base_url,
                temperature=0.7, # Higher creativity for stories
                max_tokens=1000
            )
        else:
            self.llm = None

    def generate_story(self, pokemon_name, genre="Adventure", theme="Friendship"):
        """
        Generate a creative Pokémon story.
        """
        if not self.llm:
            return {
                "title": "API Key Missing",
                "content": "Please configure your OpenAI or OpenRouter API key to generate stories."
            }

        try:
            prompt = f"""
            Write a short, engaging Pokémon story about {pokemon_name}.
            
            Genre: {genre}
            Theme: {theme}
            Target Audience: Pokémon fans (All ages)
            Length: Approximately 300-500 words.
            
            Return the result in valid JSON format ONLY:
            {{
                "title": "A catchy title for the story",
                "content": "The full story content here...",
                "summary": "A 1-sentence summary"
            }}
            
            Do not include markdown formatting. Just the raw JSON.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                # Fallback if specific JSON fails, just return raw content as story
                return {
                    "title": f"A Tale of {pokemon_name}",
                    "content": content,
                    "summary": "An AI generated story."
                }
                
        except Exception as e:
            print(f"Story Gen Error: {e}")
            return {
                "title": "Error generating story",
                "content": "Something went wrong with the AI story engine. Please try again."
            }

class PokemonQuizMaster:
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
        base_url = "https://openrouter.ai/api/v1" if os.environ.get('OPENROUTER_API_KEY') else None
        
        # Use a consistent model
        model_name = "openai/gpt-4o-mini"
        
        if self.api_key:
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                base_url=base_url,
                temperature=0.7 
            )
        else:
            self.llm = None

    def generate_question(self, difficulty="medium"):
        """
        Generate a random Pokémon trivia question appropriate for the difficulty.
        """
        if not self.llm:
            return None

        try:
            prompt = f"""
            Generate a unqiue, random Pokémon multiple-choice trivia question.
            Difficulty: {difficulty}
            
            Topics can include:
            - Anime lore (e.g., "Who was the first Pokémon Ash caught?")
            - Game mechanics (e.g., "Which type is immune to Ground moves?")
            - Pokémon biology/dex entries (e.g., "Which Pokémon is known as the Mouse Pokémon?")
            
            Return ONLY valid JSON like this:
            {{
                "question": "The question text here?",
                "options": [
                    {{"id": 1, "text": "Option A"}},
                    {{"id": 2, "text": "Option B"}},
                    {{"id": 3, "text": "Option C"}},
                    {{"id": 4, "text": "Option D"}}
                ],
                "correct_option_id": 2,
                "explanation": "Brief explanation of why it is correct."
            }}
            
            Ensure the wrong answers are plausible. Do not use Markdown.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.replace('```json', '').replace('```', '').strip()
            
            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                print(f"Quiz JSON Error: {content}")
                return None
                
        except Exception as e:
            print(f"Quiz Gen Error: {e}")
            return None
