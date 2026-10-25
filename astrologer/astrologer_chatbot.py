import getpass
import json
import os
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from google import genai
from google.genai.errors import APIError


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))
MAX_BODY_BYTES = 16_384
MAX_MESSAGE_CHARS = 2_000
MAX_HISTORY_MESSAGES = 12
STATIC_DIR = Path(__file__).parent / "static"

ASTROLOGER_INSTRUCTIONS = """You are a warm, thoughtful astrology chatbot.
Offer astrology readings as reflective guidance and entertainment, not as
scientific fact or guaranteed prediction. Be clear when a reading is general
because the user has not shared birth details. Never present astrology as a
substitute for professional medical, legal, financial, or mental-health advice.
Ask for only the birth date, approximate birth time, and birthplace when those
details are genuinely useful; make sharing them optional. Be respectful,
nonjudgmental, and concise."""


def create_handler(
    client: genai.Client | None,
) -> type[SimpleHTTPRequestHandler]:
    class ChatbotHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/api/status":
                self._send_json(200, {"configured": client is not None})
                return
            if path.startswith("/api/"):
                self._send_json(404, {"error": "Endpoint not found."})
                return
            super().do_GET()

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/chat":
                self._send_json(404, {"error": "Endpoint not found."})
                return

            content_length = self.headers.get("Content-Length")
            if content_length is None:
                self._send_json(411, {"error": "Content-Length is required."})
                return
            try:
                body_length = int(content_length)
            except ValueError:
                self._send_json(400, {"error": "Invalid Content-Length."})
                return
            if body_length < 0 or body_length > MAX_BODY_BYTES:
                self._send_json(413, {"error": "Request is too large."})
                return
            if self.headers.get_content_type() != "application/json":
                self._send_json(415, {"error": "Expected application/json."})
                return

            try:
                payload = json.loads(self.rfile.read(body_length))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"error": "Invalid JSON request."})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"error": "Request must be a JSON object."})
                return
            if client is None:
                self._send_json(
                    503,
                    {
                        "error": (
                            "The website is running, but Gemini isn't connected. "
                            "Set GEMINI_API_KEY in the server terminal and restart "
                            "the app to enable chat."
                        )
                    },
                )
                return

            message = payload.get("message")
            if not isinstance(message, str) or not message.strip():
                self._send_json(400, {"error": "Enter a message to continue."})
                return
            if len(message) > MAX_MESSAGE_CHARS:
                self._send_json(400, {"error": "Message is too long."})
                return

            history = payload.get("history", [])
            if not isinstance(history, list):
                self._send_json(400, {"error": "History must be a list."})
                return
            valid_history = []
            for item in history[-MAX_HISTORY_MESSAGES:]:
                role = item.get("role") if isinstance(item, dict) else None
                if (
                    isinstance(role, str)
                    and role in {"user", "assistant"}
                    and isinstance(item.get("content"), str)
                ):
                    valid_history.append(
                        f"{role.capitalize()}: "
                        f"{item['content'][:MAX_MESSAGE_CHARS]}"
                    )

            conversation = "\n".join(valid_history)
            history_prefix = (
                f"Conversation so far:\n{conversation}\n\n" if conversation else ""
            )
            prompt = (
                f"{ASTROLOGER_INSTRUCTIONS}\n\n"
                f"{history_prefix}"
                f"User: {message.strip()}\nAstrologer:"
            )

            try:
                interaction = client.interactions.create(model=MODEL, input=prompt)
            except APIError as exc:
                self._send_json(
                    502,
                    {"error": f"Gemini could not provide a response: {exc}"},
                )
                return

            answer = interaction.output_text
            if not answer:
                self._send_json(502, {"error": "Gemini returned an empty response."})
                return
            self._send_json(200, {"reply": answer})

        def _send_json(self, status: int, data: dict[str, str]) -> None:
            encoded = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            print(f"{self.address_string()} - {format % args}")

    return ChatbotHandler


def main() -> None:
    if not STATIC_DIR.is_dir():
        raise SystemExit(f"Frontend files were not found: {STATIC_DIR}")

    has_api_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if not has_api_key and sys.stdin.isatty():
        api_key = getpass.getpass(
            "Gemini API key (input hidden; press Enter for preview only): "
        ).strip()
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            has_api_key = True

    client = genai.Client() if has_api_key else None
    server = ThreadingHTTPServer((HOST, PORT), create_handler(client))
    browser_host = "127.0.0.1" if HOST in {"0.0.0.0", ""} else HOST
    app_url = f"http://{browser_host}:{PORT}"
    print(f"Astrologer chatbot is running at {app_url}")
    if not has_api_key:
        print(
            "Gemini is not connected. Set GEMINI_API_KEY (or GOOGLE_API_KEY) "
            "and restart to enable chat."
        )
    if sys.stdin.isatty():
        webbrowser.open(app_url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping astrologer chatbot.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
