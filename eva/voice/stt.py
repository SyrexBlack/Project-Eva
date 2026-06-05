"""
Eva's STT Module (Speech-to-Text)

Распознавание голоса через Whisper.
Ева сможет слушать Гришу, а не только читать текст.

Поддержка:
- OpenAI Whisper (base/small/medium/large)
- Faster Whisper (быстрее, требует GPU)
- Push-to-talk режим
"""

import os
import wave
import struct
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Default settings
DEFAULT_MODEL = "base"
RECORDING_DIR = "./data/recordings"


@dataclass
class STTConfig:
    """Конфигурация STT."""
    model: str = "base"           # whisper model size
    language: str = "ru"          # распознаваемый язык
    energy_threshold: int = 300    # порог громкости для активации
    recording_timeout: int = 30    # максимальная длина записи (сек)
    silence_threshold: float = 2.0 # секунд тишины для завершения


class EvaSTT:
    """
    Eva's ears — слушает и распознаёт речь.
    
    Использование:
        stt = EvaSTT()
        
        # Push-to-talk (рекомендуется)
        text = stt.listen_push_to_talk()
        
        # Автоматическое распознавание
        text = stt.listen_once()
        
        # Callback режим (слушает постоянно)
        stt.listen_callback(lambda text: print(f"Grisha said: {text}"))
    """
    
    def __init__(self, config: Optional[STTConfig] = None):
        """
        Initialize STT.
        
        Args:
            config: STT configuration
        """
        self.config = config or STTConfig()
        self._whisper = None
        self._pyaudio = None
        
        # Создаём папку для записей
        os.makedirs(RECORDING_DIR, exist_ok=True)
    
    def _load_whisper(self):
        """Lazy load Whisper model."""
        if self._whisper is None:
            try:
                import whisper
                self._whisper = whisper.load_model(self.config.model)
                print(f"✅ Whisper {self.config.model} loaded")
            except ImportError:
                try:
                    from faster_whisper import WhisperModel
                    self._whisper = WhisperModel(
                        self.config.model,
                        device="cpu",
                        compute_type="int8"
                    )
                    print(f"✅ Faster-Whisper {self.config.model} loaded")
                except ImportError:
                    raise RuntimeError(
                        "Install whisper: pip install openai-whisper\n"
                        "Or faster-whisper: pip install faster-whisper"
                    )
    
    def _load_pyaudio(self):
        """Lazy load PyAudio."""
        if self._pyaudio is None:
            try:
                import pyaudio
                self._pyaudio = pyaudio.PyAudio()
            except ImportError:
                raise RuntimeError(
                    "Install pyaudio: pip install pyaudio\n"
                    "For Linux: sudo apt install portaudio19-dev && pip install pyaudio"
                )
    
    def _record_audio(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024
    ) -> Optional[bytes]:
        """
        Запись аудио с микрофона.
        
        Args:
            sample_rate: Частота дискретизации
            chunk_size: Размер чанка
            
        Returns:
            WAV данные или None
        """
        self._load_pyaudio()
        
        import pyaudio
        
        stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        frames = []
        silent_chunks = 0
        max_chunks = int(self.config.recording_timeout * sample_rate / chunk_size)
        
        try:
            for i in range(max_chunks):
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Простой VAD (voice activity detection)
                audio_data = struct.unpack(f"{chunk_size}h", data)
                energy = sum(abs(x) for x in audio_data) / chunk_size
                
                if energy < self.config.energy_threshold:
                    silent_chunks += 1
                    # Останавливаем после 2 сек тишины
                    if silent_chunks > (self.config.silence_threshold * sample_rate / chunk_size):
                        break
                else:
                    silent_chunks = 0
            
        finally:
            stream.stop_stream()
            stream.close()
        
        if len(frames) < 10:  # Слишком короткая запись
            return None
        
        # Конвертируем в WAV
        return self._make_wav(b"".join(frames), sample_rate)
    
    def _make_wav(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Конвертировать raw audio в WAV формат."""
        import io
        
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        
        return buffer.getvalue()
    
    def _transcribe(self, audio_data: bytes) -> str:
        """
        Транскрибировать аудио через Whisper.
        
        Args:
            audio_data: WAV данные
            
        Returns:
            Распознанный текст
        """
        self._load_whisper()
        
        # Сохраняем во временный файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"{RECORDING_DIR}/temp_{timestamp}.wav"
        
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        try:
            if hasattr(self._whisper, "transcribe"):
                # OpenAI Whisper
                result = self._whisper.transcribe(
                    temp_path,
                    language=self.config.language,
                    fp16=False
                )
                return result["text"].strip()
            else:
                # Faster Whisper
                segments, _ = self._whisper.transcribe(
                    temp_path,
                    language=self.config.language
                )
                return " ".join(segment.text for segment in segments).strip()
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def listen_once(
        self,
        timeout: int = 5,
        record_while: bool = True
    ) -> Optional[str]:
        """
        Слушать один раз (до начала речи или таймаута).
        
        Args:
            timeout: Максимальное время ожидания речи (сек)
            record_while: Записывать ли аудио во время ожидания
            
        Returns:
            Распознанный текст или None
        """
        self._load_pyaudio()
        
        import pyaudio
        
        stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        silent_count = 0
        speaking = False
        max_silent = 50  # ~3 секунды тишины для завершения
        
        try:
            for _ in range(int(timeout * 16000 / 1024)):
                data = stream.read(1024, exception_on_overflow=False)
                
                # VAD
                audio_data = struct.unpack("1024h", data)
                energy = sum(abs(x) for x in audio_data) / 1024
                
                if energy > self.config.energy_threshold:
                    speaking = True
                    silent_count = 0
                    if record_while:
                        frames.append(data)
                elif speaking:
                    silent_count += 1
                    if record_while:
                        frames.append(data)
                    
                    if silent_count > max_silent:
                        break
        
        finally:
            stream.stop_stream()
            stream.close()
        
        if not frames:
            return None
        
        audio_bytes = self._make_wav(b"".join(frames), 16000)
        return self._transcribe(audio_bytes)
    
    def listen_push_to_talk(self, key: str = "space") -> Optional[str]:
        """
        Push-to-talk режим.
        
        Нажми и держи пробел — говори, отпусти — распознаём.
        
        Args:
            key: Клавиша для активации (по умолчанию space)
            
        Returns:
            Распознанный текст
        """
        try:
            from pynput import keyboard
        except ImportError:
            return "[pynput not installed: pip install pynput]"
        
        import threading
        
        is_recording = threading.Event()
        is_recording.clear()
        frames = []
        
        def on_press(key_press):
            """Handle key press - start recording."""
            try:
                if key == "space":
                    if key_press == keyboard.Key.space:
                        is_recording.set()
                else:
                    if hasattr(key_press, 'char') and key_press.char == key:
                        is_recording.set()
            except AttributeError:
                pass
        
        def on_release(key_release):
            """Handle key release - stop recording."""
            try:
                if key == "space":
                    if key_release == keyboard.Key.space:
                        is_recording.clear()
                else:
                    if hasattr(key_release, 'char') and key_release.char == key:
                        is_recording.clear()
            except AttributeError:
                pass
        
        # Start keyboard listener
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        print(f"🎤 Push-to-talk: Hold '{key}' to record, release to transcribe")
        print("Press Ctrl+C to cancel...")
        
        # Recording
        self._load_pyaudio()
        import pyaudio
        
        stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        was_recording = False
        try:
            while True:
                data = stream.read(1024, exception_on_overflow=False)
                
                if is_recording.is_set():
                    was_recording = True
                    frames.append(data)
                    
                    # Max 30 seconds
                    if len(frames) > 30 * 16:
                        break
                elif was_recording:
                    break
        
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            listener.stop()
        
        if not frames:
            return None
        
        # Transcribe
        audio_bytes = self._make_wav(b"".join(frames), 16000)
        return self._transcribe(audio_bytes)
    
    def listen_callback(
        self,
        callback: Callable[[str], None],
        check_interval: float = 0.5
    ):
        """
        Постоянное прослушивание с callback.
        
        Args:
            callback: Функция для обработки распознанного текста
            check_interval: Интервал проверки голоса (сек)
        """
        import threading
        
        def listening_loop():
            while True:
                text = self.listen_once(timeout=3, record_while=True)
                if text and len(text) > 2:
                    callback(text)
        
        thread = threading.Thread(target=listening_loop, daemon=True)
        thread.start()


# =============================================================================
# Simple version without PyAudio (using subprocess)
# =============================================================================

class SimpleSTT:
    """
    Упрощённый STT через системные утилиты.
    
    Использует ffmpeg или arecord для записи.
    Работает без Python зависимостей для записи.
    """
    
    def __init__(self, model: str = "base"):
        self.model = model
        self._whisper = None
    
    def _load_whisper(self):
        """Lazy load Whisper model."""
        if self._whisper is None:
            try:
                import whisper
                self._whisper = whisper.load_model(self.model)
            except ImportError:
                try:
                    from faster_whisper import WhisperModel
                    self._whisper = WhisperModel(
                        self.model,
                        device="cpu",
                        compute_type="int8"
                    )
                except ImportError:
                    raise RuntimeError(
                        "Install whisper: pip install openai-whisper"
                    )
    
    def _record_with_ffmpeg(self, duration: int = 5) -> Optional[bytes]:
        """Запись через ffmpeg."""
        import subprocess
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{RECORDING_DIR}/temp_{timestamp}.wav"
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "alsa", "-i", "default",
                "-t", str(duration), "-ar", "16000", "-ac", "1",
                output_path
            ], capture_output=True, timeout=duration + 5)
            
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    return f.read()
        except Exception as e:
            print(f"FFmpeg recording failed: {e}")
        
        return None
    
    def _record_with_arecord(self, duration: int = 5) -> Optional[bytes]:
        """Запись через arecord."""
        import subprocess
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{RECORDING_DIR}/temp_{timestamp}.wav"
        
        try:
            subprocess.run([
                "arecord", "-d", str(duration), "-f", "S16_LE", "-r", "16000",
                "-c", "1", output_path
            ], capture_output=True, timeout=duration + 5)
            
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    return f.read()
        except Exception as e:
            print(f"arecord recording failed: {e}")
        
        return None
    
    def listen(self, duration: int = 5) -> Optional[str]:
        """
        Записать и распознать.
        
        Args:
            duration: Длина записи (сек)
            
        Returns:
            Распознанный текст
        """
        # Пробуем arecord (Linux)
        audio_data = self._record_with_arecord(duration)
        
        if not audio_data:
            return None
        
        # Сохраняем для Whisper
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = f"{RECORDING_DIR}/temp_{timestamp}.wav"
        
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        try:
            self._load_whisper()
            
            if hasattr(self._whisper, "transcribe"):
                result = self._whisper.transcribe(
                    temp_path,
                    language="ru",
                    fp16=False
                )
                return result["text"].strip()
            else:
                segments, _ = self._whisper.transcribe(
                    temp_path,
                    language="ru"
                )
                return " ".join(segment.text for segment in segments).strip()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# =============================================================================
# Global instance
# =============================================================================

_stt: Optional[EvaSTT] = None


def get_stt(config: Optional[STTConfig] = None) -> EvaSTT:
    """Get or create global STT instance."""
    global _stt
    if _stt is None:
        _stt = EvaSTT(config)
    return _stt


# Тест
if __name__ == "__main__":
    print("=== Eva STT Test ===\n")
    
    # Проверяем зависимости
    try:
        import whisper
        print("✅ Whisper available")
    except ImportError:
        print("❌ Whisper not installed: pip install openai-whisper")
    
    try:
        import pyaudio
        print("✅ PyAudio available")
    except ImportError:
        print("❌ PyAudio not installed: pip install pyaudio")
    
    print("\n📝 Usage:")
    print("  stt = EvaSTT()")
    print("  text = stt.listen_once()  # Listen once")
    print("  stt.listen_callback(lambda t: print(t))  # Continuous")