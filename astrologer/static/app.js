const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const sendButton = document.querySelector("#send-button");
const serviceStatus = document.querySelector(".guide-status div > span");
const history = [];
const MAX_HISTORY_MESSAGES = 12;

async function updateServiceStatus() {
  const dot = serviceStatus.querySelector(".online-dot");
  const label = dot.nextSibling;
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Status unavailable");
    const status = await response.json();
    if (status.configured) {
      dot.classList.remove("offline-dot");
      label.textContent = " Gemini connected";
    } else {
      dot.classList.add("offline-dot");
      label.textContent = " API key needed";
    }
  } catch {
    dot.classList.add("offline-dot");
    label.textContent = " Chat server offline";
  }
}

function addMessage(role, content, { error = false, typing = false } = {}) {
  const message = document.createElement("article");
  message.className = `message ${role}`;
  if (typing) message.setAttribute("aria-label", "Astrologer is thinking");

  const icon = document.createElement("span");
  icon.className = "message-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = role === "assistant" ? "✦" : "✧";

  const bubble = document.createElement("div");
  bubble.className = `message-bubble${error ? " error" : ""}${typing ? " typing" : ""}`;
  if (typing) {
    for (let i = 0; i < 3; i += 1) {
      bubble.append(document.createElement("span"));
    }
  } else {
    bubble.textContent = content;
  }

  message.append(icon, bubble);
  messages.append(message);
  message.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return message;
}

async function sendMessage(message) {
  const normalizedMessage = message.trim();
  if (!normalizedMessage || sendButton.disabled) return;

  welcome.hidden = true;
  addMessage("user", normalizedMessage);
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  input.disabled = true;
  const loadingMessage = addMessage("assistant", "", { typing: true });

  try {
    let response;
    try {
      response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: normalizedMessage,
          history: history.slice(-MAX_HISTORY_MESSAGES),
        }),
      });
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error(
          "Can't reach the chat server. In a VS Code terminal, set GEMINI_API_KEY, run `python astrologer_chatbot.py`, then open http://127.0.0.1:8765. Keep that terminal running; don't use Live Server or open the HTML file directly.",
        );
      }
      throw error;
    }

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(
        "This page isn't connected to the chatbot API. Start `python astrologer_chatbot.py` and open http://127.0.0.1:8765 instead of using Live Server.",
      );
    }
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    if (typeof data.reply !== "string" || !data.reply.trim()) {
      throw new Error("The astrologer returned an empty reply. Please try again.");
    }

    loadingMessage.remove();
    addMessage("assistant", data.reply);
    history.push(
      { role: "user", content: normalizedMessage },
      { role: "assistant", content: data.reply },
    );
    history.splice(0, Math.max(0, history.length - MAX_HISTORY_MESSAGES));
  } catch (error) {
    loadingMessage.remove();
    addMessage(
      "assistant",
      error instanceof Error ? error.message : "Unable to reach the astrologer. Please try again.",
      { error: true },
    );
  } finally {
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt || ""));
});

document.querySelector("#new-chat").addEventListener("click", () => {
  history.length = 0;
  messages.replaceChildren();
  welcome.hidden = false;
  input.value = "";
  input.focus();
});

const aboutDialog = document.querySelector("#about-dialog");
document.querySelector("#about-button").addEventListener("click", () => aboutDialog.showModal());
document.querySelector("#dialog-close").addEventListener("click", () => aboutDialog.close());
aboutDialog.addEventListener("click", (event) => {
  if (event.target === aboutDialog) aboutDialog.close();
});

updateServiceStatus();
