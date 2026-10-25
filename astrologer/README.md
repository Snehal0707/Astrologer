# Starlight Astrology Chat

A responsive HTML, CSS, and JavaScript chat interface powered by the Google Gen
AI SDK. A small Python HTTP server serves the website and forwards chat requests
to Gemini so the API key stays on the server instead of being embedded in the
browser.

## Requirements

- Python 3.10 or newer
- A Gemini API key

## Run on Windows PowerShell

1. Install Python 3.10 or newer if it isn't already installed.
2. Install the Python dependency:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. (Optional) Set your API key for this PowerShell session:

   ```powershell
   $env:GEMINI_API_KEY = "your-api-key"
   ```

   If you skip this step, starting the app in a terminal prompts for the key
   with hidden input. Press Enter at that prompt to open the website in
   preview-only mode.

4. Start the web app:

   ```powershell
   python astrologer_chatbot.py
   ```

   Or double-click `start_chatbot.bat`, then enter your key at the hidden prompt.
   The app opens in your browser; keep the terminal window open while chatting.
   Press `Ctrl+C` in the terminal to stop the server.

5. If you configured an API key, chat is ready. Without a key, the website still
   opens but displays instructions to add one and restart before chatting.

The default model is `gemini-3.8-flash`. Set `GEMINI_MODEL` to use another model
available to your API key. The server binds to `127.0.0.1` by default; set
`HOST` or `PORT` to override the address and port.

## Deploy online with Render

The included `render.yaml` configures a Render web service, so the app can keep
running without VS Code or your computer being on:

1. Push this project to a GitHub repository.
2. In Render, choose **New** > **Blueprint**, connect the repository, and deploy
   the `render.yaml` blueprint.
3. In the new Render service's **Environment** settings, add
   `GEMINI_API_KEY` with your Gemini API key, then redeploy.
4. Open the `onrender.com` URL shown on the Render service page.

Keep the API key in Render's environment settings; do not add it to the project
or GitHub. Render's free service may sleep after a period without visits, so the
first visit after it sleeps can take a little while to load. Choose an always-on
paid service if the chat must respond immediately at all times.

## Troubleshooting

If chat says it cannot connect or shows `Failed to fetch`, the page is likely
being served by VS Code Live Server or opened directly from the `static` folder.
The chat API is provided by the Python app. Start it with `start_chatbot.bat`
or `python astrologer_chatbot.py` and keep its terminal running. The app opens
at `http://127.0.0.1:8765`; don't use the Live Server or file URL. If you see
the Gemini-not-connected message, set the API key in the terminal and restart.
Never paste API keys into chat or commit them to source files. Revoke any key
that has been shared and create a replacement.
