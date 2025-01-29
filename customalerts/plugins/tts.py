import edge_tts
from pathlib import Path
from poolguy.utils import ColorLogger, asyncio

logger = ColorLogger(__name__)

VOICES = {
    "Jenny": {
        "local": "United States",
        "sex": "female",
        "voice": "en-US-JennyNeural"
    },
    "Steffan": {
        "local": "United States",
        "sex": "male",
        "voice": "en-US-SteffanNeural"
    },
    "Ryan": {
        "local": "United Kingdom",
        "sex": "male",
        "voice": "en-GB-RyanNeural"
    },
    "Sonia": {
        "local": "United Kingdom",
        "sex": "female",
        "voice": "en-GB-SoniaNeural"
    },
    "Natasha": {
        "local": "Australia",
        "sex": "female",
        "voice": "en-AU-NatashaNeural"
    },
    "William": {
        "local": "Australia",
        "sex": "male",
        "voice": "en-AU-WilliamNeural"
    },
    "Clara": {
        "local": "Canada",
        "sex": "female",
        "voice": "en-CA-ClaraNeural"
    },
    "Liam": {
        "local": "Canada",
        "sex": "male",
        "voice": "en-CA-LiamNeural"
    }
}

async def generate_speech(text, output_file, voice="Ryan", rate=0, volume=0, pitch=-15):
    """
    Generate speech from text using Microsoft Edge TTS and save as MP3.
    
    Args:
        text (str): The text to convert to speech
        output_file (str): The path/filename for the output MP3 file
        voice (str): The voice to use (default: "Eric") - can be shortname or full voice name
        rate (int): Speaking rate adjustment (-100 to 100)
        volume (int): Volume adjustment (-100 to 100)
        pitch (int): Pitch adjustment in Hz (-100 to 100)
    
    Returns:
        str: Path to the generated MP3 file
    
    Raises:
        ValueError: If rate, volume, or pitch are outside valid ranges
        Exception: If there's an error during speech generation
    """
    try:
        # Validate integer ranges
        for param, name in [(rate, 'rate'), (volume, 'volume'), (pitch, 'pitch')]:
            if not -100 <= param <= 100:
                raise ValueError(f"{name} must be between -100 and 100")
        
        # Convert integers to formatted strings
        rate_str = f"{rate:+d}%" if rate != 0 else "+0%"
        volume_str = f"{volume:+d}%" if volume != 0 else "+0%"
        pitch_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
        
        # Handle voice name
        if voice in VOICES:
            voice = VOICES[voice]["voice"]
        # If not in VOICES dict, assume it's a full voice name

        # Create communicate instance
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=rate_str,
            volume=volume_str,
            pitch=pitch_str
        )
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate audio
        await communicate.save(str(output_path))
        return str(output_path.absolute())
        
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)} text={text} voice={voice} rate={rate} volume={volume} pitch={pitch}")
        return None

async def main():
    for v in VOICES:
        try:
            file_path = await generate_speech(
                f"Hello, my name is {v} and this is a test!",
                f"{v}_pitch+20.mp3",
                voice=v,
                pitch=20
            )
            print(f"Generated file at: {file_path}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())