import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.voice_adapter import voice_adapter, VoiceInputPayload

client = TestClient(app)

class TestVoiceFeature(unittest.TestCase):
    def test_01_voice_adapter_processing_web_speech(self):
        """1. Test voice adapter normalizing Web Speech API input."""
        payload = VoiceInputPayload(
            source="web_speech",
            transcript="  Remember that I studied Operating Systems paging today.  ",
            device_id="browser_mic"
        )
        res = voice_adapter.process_incoming_voice(payload)
        self.assertEqual(res["source"], "web_speech")
        self.assertEqual(res["transcript"], "Remember that I studied Operating Systems paging today.")
        self.assertEqual(res["device_id"], "browser_mic")
        self.assertEqual(res["word_count"], 8)
        self.assertFalse(res["omi_authenticated"])

    def test_02_voice_adapter_processing_text_fallback(self):
        """2. Test voice adapter processing typed text fallback input."""
        payload = VoiceInputPayload(
            source="text_fallback",
            transcript="What did I study about TCP flow control?",
            device_id="keyboard"
        )
        res = voice_adapter.process_incoming_voice(payload)
        self.assertEqual(res["source"], "text_fallback")
        self.assertEqual(res["transcript"], "What did I study about TCP flow control?")
        self.assertEqual(res["word_count"], 8)

    def test_03_adapter_status(self):
        """3. Test retrieving adapter status and supported sources."""
        status = voice_adapter.get_adapter_status()
        self.assertTrue(status["fallback_active"])
        self.assertIn("web_speech_api", status["supported_sources"])
        self.assertIn("text_fallback", status["supported_sources"])

    def test_04_study_api_with_web_speech_source(self):
        """4. Test Study API endpoint processing Web Speech voice transcript."""
        res = client.post("/api/study", json={
            "transcript": "Explain what I studied about 2PL protocol.",
            "source": "web_speech",
            "device_id": "browser_mic",
            "uid": "test_voice_user"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("voice_meta", data)
        self.assertEqual(data["voice_meta"]["source"], "web_speech")
        self.assertEqual(data["voice_meta"]["device_id"], "browser_mic")

    def test_05_empty_voice_transcript_validation(self):
        """5. Test empty voice input is rejected with 400 Bad Request."""
        res = client.post("/api/study", json={
            "transcript": "",
            "source": "web_speech"
        })
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["detail"], "Voice or text input transcript cannot be empty.")

if __name__ == "__main__":
    unittest.main()