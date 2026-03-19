const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const documentsEl = document.getElementById("documents");
const chatForm = document.getElementById("chat-form");
const questionInput = document.getElementById("question-input");
const chatStatus = document.getElementById("chat-status");
const messagesEl = document.getElementById("messages");

let sessionId = "";

function addMessage(role, text, sources = []) {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const title = document.createElement("h3");
  title.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("p");
  body.textContent = text;

  wrapper.appendChild(title);
  wrapper.appendChild(body);

  if (sources.length) {
    const sourceTitle = document.createElement("strong");
    sourceTitle.textContent = "Sources";
    wrapper.appendChild(sourceTitle);

    sources.forEach((source, index) => {
      const sourceItem = document.createElement("div");
      const page = source.page === null ? "N/A" : source.page;
      sourceItem.className = "source";
      sourceItem.textContent = `${index + 1}. ${source.document} | page ${page} | chunk ${source.chunk_index}`;
      wrapper.appendChild(sourceItem);
    });
  }

  messagesEl.prepend(wrapper);
}

async function refreshDocuments() {
  const response = await fetch("/api/documents");
  const documents = await response.json();
  documentsEl.innerHTML = "";

  if (!documents.length) {
    documentsEl.textContent = "No documents indexed yet.";
    return;
  }

  documents.forEach((doc) => {
    const item = document.createElement("div");
    item.className = "document-card";
    item.textContent = `${doc.filename} • ${doc.chunk_count} chunks`;
    documentsEl.appendChild(item);
  });
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) {
    return;
  }

  uploadStatus.textContent = "Uploading...";
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    uploadStatus.textContent = payload.detail || "Upload failed";
    return;
  }

  uploadStatus.textContent = `Indexed ${payload.chunks_indexed} chunks`;
  fileInput.value = "";
  await refreshDocuments();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) {
    return;
  }

  addMessage("user", question);
  questionInput.value = "";
  chatStatus.textContent = "Thinking...";

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId || null }),
  });

  const payload = await response.json();
  if (!response.ok) {
    chatStatus.textContent = payload.detail || "Request failed";
    return;
  }

  sessionId = payload.session_id;
  addMessage("assistant", payload.answer, payload.sources);
  chatStatus.textContent = "Answered";
});

refreshDocuments();
