import edge_tts #pip install edge-tts
from poolguy.utils import ColorLogger, asyncio
from typing import Optional
import xml.etree.ElementTree as ET

class EdgeTTSHandler:
    """
    A class to handle Text-to-Speech operations using Microsoft Edge TTS.
    
    Attributes:
        logger: ColorLogger instance for logging
        voice: Voice to use for TTS
        rate: Speech rate (percentage as string, e.g., "+50%" or "-50%")
        volume: Volume level (percentage as string, e.g., "+50%" or "-50%")
        pitch: Pitch adjustment (percentage as string, e.g., "+50%" or "-50%")
    """
    
    # Class variable to store available voices
    _available_voices = None
    
    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0%"
    ):
        self.logger = ColorLogger(__name__)
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        
    @staticmethod
    async def list_voices() -> list:
        """Get list of available voices."""
        if EdgeTTSHandler._available_voices is None:
            EdgeTTSHandler._available_voices = await edge_tts.list_voices()
        return EdgeTTSHandler._available_voices
    
    async def validate_voice(self) -> bool:
        """Validate if selected voice is available."""
        voices = await self.list_voices()
        return any(v["ShortName"] == self.voice for v in voices)
    
    def _create_ssml(self, text: str) -> str:
        """Create SSML markup for the text with current settings."""
        root = ET.Element("speak", version="1.0")
        root.set("xmlns", "http://www.w3.org/2001/10/synthesis")
        root.set("xmlns:mstts", "http://www.w3.org/2001/mstts")
        root.set("xml:lang", self.voice[:5])  # Extract language code (e.g., "en-US")
        
        voice = ET.SubElement(root, "voice")
        voice.set("name", self.voice)
        
        prosody = ET.SubElement(voice, "prosody")
        prosody.set("rate", self.rate)
        prosody.set("volume", self.volume)
        prosody.set("pitch", self.pitch)
        prosody.text = text
        
        return ET.tostring(root, encoding="unicode")
    
    async def text_to_speech(
        self,
        text: str,
        output_file: str,
        subtitle_file: Optional[str] = None
    ) -> None:
        """
        Convert text to speech and optionally generate subtitles.
        
        Args:
            text: Text to convert to speech
            output_file: Path to save the audio file
            subtitle_file: Optional path to save subtitles (None to skip)
        """
        try:
            # Validate voice before proceeding
            if not await self.validate_voice():
                raise ValueError(f"Voice '{self.voice}' is not available")
            
            # Create SSML with current settings
            ssml = self._create_ssml(text)
            
            # Initialize communicate object with SSML
            communicate = edge_tts.Communicate(ssml, self.voice)
            
            # Generate audio
            await communicate.save(output_file)
            self.logger.info(f"Audio saved to {output_file}")
            
            # Generate subtitles if requested
            if subtitle_file:
                async for sub in communicate.stream():
                    if sub[2] is not None:  # If we have subtitle data
                        with open(subtitle_file, "a", encoding="utf-8") as f:
                            start = self._format_time(sub[0])
                            end = self._format_time(sub[1])
                            f.write(f"{start} --> {end}\n{sub[2]}\n\n")
                self.logger.info(f"Subtitles saved to {subtitle_file}")
                
        except Exception as e:
            self.logger.error(f"Error during TTS conversion: {e}")
            raise
    
    @staticmethod
    def _format_time(ms: int) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
        seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def update_settings(
        self,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> None:
        """Update TTS settings."""
        if voice:
            self.voice = voice
        if rate:
            self.rate = rate
        if volume:
            self.volume = volume
        if pitch:
            self.pitch = pitch