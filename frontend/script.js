// Backend API URL.
// For local testing, this points to the local FastAPI server.
// Once deployed, replace this with your Render backend URL,
// e.g. "https://aec-chat-bot.onrender.com/chat"
const API_URL = "https://aec-question-answering.onrender.com/chat";

const MAX_WORDS = 200;

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");
const sendButton = document.getElementById("send-button");
const newConversationButton = document.getElementById("new-conversation-button");

let conversationId = null;

const CATEGORY_LABELS = {
  codes: "Codes",
  safety: "Safety",
  architecture: "Architecture",
  structures: "Structures",
  energy: "Energy",
  building_systems: "Building systems",
  construction: "Construction",
  materials: "Materials",
  sustainability: "Sustainability",
  general_aec: "General AEC",
};

function addMessage(text, type) {
  const bubble = document.createElement("div");
  bubble.className = `message ${type}`;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
  return bubble;
}

function showThinkingIndicator() {
  const bubble = document.createElement("div");
  bubble.className = "message bot thinking";
  bubble.textContent = "Thinking…";
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
  return bubble;
}

function removeThinkingIndicator(bubble) {
  if (bubble && bubble.parentNode === chatLog) {
    chatLog.removeChild(bubble);
  }
}

function isSafeHttpsUrl(value) {
  try {
    return new URL(value).protocol === "https:";
  } catch (_) {
    return false;
  }
}

function addBotResponse(text, category, resources) {
  const responseGroup = document.createElement("div");
  responseGroup.className = "bot-response";

  const bubble = document.createElement("div");
  bubble.className = "message bot";
  bubble.textContent = text;
  responseGroup.appendChild(bubble);

  if (CATEGORY_LABELS[category]) {
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "category-label";
    categoryLabel.textContent = CATEGORY_LABELS[category];
    responseGroup.appendChild(categoryLabel);
  }

  const safeResources = Array.isArray(resources)
    ? resources.filter((resource) => resource && isSafeHttpsUrl(resource.url)).slice(0, 3)
    : [];

  if (safeResources.length > 0) {
    const resourcePanel = document.createElement("nav");
    resourcePanel.className = "resource-panel";
    resourcePanel.setAttribute("aria-label", "Related resources");

    const heading = document.createElement("p");
    heading.className = "resource-heading";
    heading.textContent = "Related resources";
    resourcePanel.appendChild(heading);

    safeResources.forEach((resource) => {
      const link = document.createElement("a");
      link.className = "resource-link";
      link.href = resource.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = resource.title || "AEC resource";
      resourcePanel.appendChild(link);
    });

    responseGroup.appendChild(resourcePanel);
  }

  chatLog.appendChild(responseGroup);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function countWords(text) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

async function sendMessage(message) {
  const requestBody = { message };
  if (conversationId) {
    requestBody.conversation_id = conversationId;
  }

  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
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
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

function startNewConversation() {
  conversationId = null;
  chatLog.replaceChildren();
  chatInput.focus();
}

newConversationButton.addEventListener("click", startNewConversation);

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
  chatInput.disabled = true;
  newConversationButton.disabled = true;

  const thinkingBubble = showThinkingIndicator();

  try {
    const result = await sendMessage(message);
    conversationId = result.conversation_id;
    removeThinkingIndicator(thinkingBubble);
    addBotResponse(result.response, result.category, result.resources);
  } catch (err) {
    removeThinkingIndicator(thinkingBubble);
    if (err.status === 404) {
      conversationId = null;
    }
    addMessage(err.message || "Unable to reach the server. Please try again later.", "error");
  } finally {
    sendButton.disabled = false;
    chatInput.disabled = false;
    newConversationButton.disabled = false;
    chatInput.focus();
  }
});
