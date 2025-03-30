import json
import os
from typing import List, Tuple

import loguru
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

logger = loguru.logger

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiTextGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-001"):
        """Initializes the GeminiTextGenerator with API key and model."""
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_text(
        self,
        system_instruction: str,
        user_input: str,
        temperature: float = 0.1,
        top_p: float = 0.95,
        top_k: int = 20,
        max_output_tokens: int = 1000,
        stop_sequences: list = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        seed: int = None,
    ) -> str:
        """Generates text using the Gemini API.

        Args:
            system_instruction (str): The system prompt or instruction.
            user_input (str): The user input text.
            temperature (float): Sampling temperature.
            top_p (float): Nucleus sampling probability.
            top_k (int): Top-k sampling.
            max_output_tokens (int): Maximum number of tokens in the output.
            stop_sequences (list): List of stop sequences.
            presence_penalty (float): Presence penalty for token generation.
            frequency_penalty (float): Frequency penalty for token generation.
            seed (int): Random seed for reproducibility.

        Returns:
            str: The generated text.
        """
        if stop_sequences is None:
            stop_sequences = []

        # TODO: Use a Pydantic model for the response schema
        # https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/controlled-generation/intro_controlled_generation.ipynb

        # class WeeklySchedule(BaseModel):
        #     Monday: List[Tuple[str, str]]
        #     Tuesday: List[Tuple[str, str]]
        #     Wednesday: List[Tuple[str, str]]
        #     Thursday: List[Tuple[str, str]]
        #     Friday: List[Tuple[str, str]]

        WeeklySchedule = {
            "type": "object",
            "properties": {
                "Monday": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": [
                            {
                                "type": "string",
                                "format": "time",
                                "description": "Start time, format hh:mm AM/PM",
                            },
                            {
                                "type": "string",
                                "format": "time",
                                "description": "End time, format hh:mm AM/PM",
                            },
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "Tuesday": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": [
                            {
                                "type": "string",
                                "format": "time",
                                "description": "Start time, format hh:mm AM/PM",
                            },
                            {
                                "type": "string",
                                "format": "time",
                                "description": "End time, format hh:mm AM/PM",
                            },
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "Wednesday": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": [
                            {
                                "type": "string",
                                "format": "time",
                                "description": "Start time, format hh:mm AM/PM",
                            },
                            {
                                "type": "string",
                                "format": "time",
                                "description": "End time, format hh:mm AM/PM",
                            },
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "Thursday": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": [
                            {
                                "type": "string",
                                "format": "time",
                                "description": "Start time, format hh:mm AM/PM",
                            },
                            {
                                "type": "string",
                                "format": "time",
                                "description": "End time, format hh:mm AM/PM",
                            },
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "Friday": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": [
                            {
                                "type": "string",
                                "format": "time",
                                "description": "Start time, format hh:mm AM/PM",
                            },
                            {
                                "type": "string",
                                "format": "time",
                                "description": "End time, format hh:mm AM/PM",
                            },
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
            },
            "required": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        }

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            candidate_count=1,
            seed=seed,
            max_output_tokens=max_output_tokens,
            stop_sequences=stop_sequences,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            response_mime_type="application/json",
            # response_schema=WeeklySchedule,
        )

        parts = [types.Part.from_text(text=f"<user_input>{user_input}</user_input>")]

        contents = types.Content(
            parts=parts,
            role="user",
        )

        response = self.client.models.generate_content(
            model=self.model,
            config=config,
            contents=contents,
        )

        return response.candidates[0].content.parts[0].text


def main():
    # Example usage of the GeminiTextGenerator
    generator = GeminiTextGenerator(api_key=GEMINI_API_KEY)

    system_prompt = """
    You are a helpful AI assistant that helps me organize my weekly schedule. You take in information about my week and then you give me a structured object that includes start and end times for each day. Each day can have multiple blocks of time that signify breaks in the day.

    The format I want you to use is as follows:
    - Return your response in 5 arrays; one for each day of the week.
    - Each array should contain arrays that represent the start and end times for each block of time in the day.
    - Each tuple should contain two strings: the start time and end time in the format "hh:mm AM/PM".
    - If there are no breaks in the day, return a single tuple with the default start and end times for the day.
    - If there are multiple blocks of time in the day, return multiple tuples in the array.
    """
    user_input = """
    I want my schedule to follow these rules:

    Every day has a default start time of 9:00 AM and end time of 5:00 PM unless stated otherwise. 
    Every day typically lasts about 8 hours.
    Consider the following exceptions when developing the schedule:

    These are the special exceptions that apply to my schedule:

    - On Tuesday, I want to start at 5AM and end at 2:00 PM.
    - On Tuesday, I have a dinner appointment from 5:30 PM to 7:00 PM.
    - On Friday, I want to see a movie at 7:00 PM.
    """

    try:
        response = generator.generate_text(
            system_instruction=system_prompt,
            user_input=user_input,
            temperature=1,
            max_output_tokens=1000,
        )
        schedule = {}
        for day, blocks in eval(response).items():
            schedule[day] = [tuple(block) for block in blocks]
        return schedule
    except ValueError as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
