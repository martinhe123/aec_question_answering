// Backend API URL.
// For local testing, this points to the local FastAPI server.
// Once deployed, replace this with your Render backend URL,
// e.g. "https://aec-chat-bot.onrender.com/chat"
const API_URL = "http://127.0.0.1:8000/chat";

const MAX_WORDS = 200;

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");
const sendButton = document.getElementById("send-button");

function addMessage(text, type) {
  const bubble = document.createElement("div");
  bubble.className = `message ${type}`;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function countWords(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

async function sendMessage(message) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        detail = errorData.detail;
      }
    } catch (_) {
      // response body wasn't valid JSON, keep default message
    }
    throw new Error(detail);
  }

  const data = await response.json();
  return data.response;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = chatInput.value.trim();

  // 1. Empty input
  if (!message) {
    addMessage("Please enter a message before sending.", "error");
    return;
  }

  // 2. Message longer than 200 words
  const wordCount = countWords(message);
  if (wordCount > MAX_WORDS) {
    addMessage(
      `Your message is too long (${wordCount} words). Please limit it to ${MAX_WORDS} words.`,
      "error"
    );
    return;
  }

  addMessage(message, "user");
  chatInput.value = "";
  sendButton.disabled = true;

  try {
    const reply = await sendMessage(message);
    addMessage(reply, "bot");
  } catch (err) {
    addMessage(err.message || "Unable to reach the server. Please try again later.", "error");
  } finally {
    sendButton.disabled = false;
    chatInput.focus();
  }
});
