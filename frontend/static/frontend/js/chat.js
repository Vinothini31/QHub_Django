document.addEventListener("DOMContentLoaded", () => {

    console.log("✅ chat.js loaded");

    const GEMINI_URL = "/api/chat/gemini/"; // ✅ Using Gemini API only

    const DOC_UPLOAD_URL = "/api/documents/upload/";

    const form = document.getElementById("chatForm");
    const input = document.getElementById("userInput");
    const messages = document.getElementById("chatMessages");
    const historyList = document.getElementById("historyList");

    // 🔹 New Chat Button
    const newChatBtn = document.getElementById("newChatBtn");

    // 🔹 Upload input
    const fileUpload = document.getElementById("fileUpload");

    // Safety check
    if (!form || !input || !messages || !historyList) {
        console.error("❌ Chat DOM elements not found");
        return;
    }

    // ---------------- CSRF ----------------
    function getCSRFToken() {
        const name = "csrftoken=";
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookies = decodedCookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return cookie.substring(name.length);
            }
        }
        return "";
    }

    // ---------------- HISTORY ----------------
    let chatHistory = JSON.parse(sessionStorage.getItem("chatHistory") || "[]");
    renderHistory();

    // ---------------- NEW CHAT (UI ONLY) ----------------
    if (newChatBtn) {
        newChatBtn.addEventListener("click", () => {
            messages.innerHTML = "";
            input.value = "";
            console.log("🆕 New chat started (UI only)");
        });
    }

    // ---------------- FILE UPLOAD (ACTUAL UPLOAD) ----------------
    let currentChatId = 1; // Default chat_id, will be updated after upload
    if (fileUpload) {
        fileUpload.addEventListener("change", async () => {
            if (fileUpload.files.length > 0) {
                const file = fileUpload.files[0];
                const formData = new FormData();
                formData.append("file", file);

                addMessage(`Uploading \"${file.name}\"...`, "bot");

                // Get JWT access token from localStorage
                const accessToken = localStorage.getItem("access");

                try {
                    const response = await fetch(DOC_UPLOAD_URL, {
                        method: "POST",
                        headers: accessToken ? { "Authorization": `Bearer ${accessToken}` } : undefined,
                        body: formData
                    });
                    if (!response.ok) throw new Error("Upload failed");
                    const data = await response.json();
                    addMessage(`📄 Document \"${file.name}\" uploaded successfully!`, "bot");
                    if (data.chat_id) {
                        currentChatId = data.chat_id;
                        sessionStorage.setItem("currentChatId", currentChatId);
                    }
                } catch (err) {
                    addMessage("❌ Document upload failed.", "bot");
                }
                // reset input so same file can be selected again
                fileUpload.value = "";
            }
        });
    }

    // ---------------- FORM SUBMIT ----------------
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const userText = input.value.trim();
        if (!userText) return;

        addMessage(userText, "user");
        input.value = "";

        chatHistory.push({ sender: "user", text: userText });
        saveHistory();
        renderHistory();

        addTyping();

        // Use chat_id from sessionStorage if available
        let chatIdToSend = currentChatId;
        const storedChatId = sessionStorage.getItem("currentChatId");
        if (storedChatId) chatIdToSend = storedChatId;

        try {
            const response = await fetch(GEMINI_URL, {  // ✅ Changed from OPENAI_URL to GEMINI_URL
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ message: userText, chat_id: chatIdToSend }),
            });

            if (!response.ok) throw new Error("Server error");

            const data = await response.json();
            removeTyping();

            const botReply = data.reply || "No response from AI";
            addMessage(botReply, "bot");

            chatHistory.push({ sender: "bot", text: botReply });
            saveHistory();
            renderHistory();

        } catch (error) {
            console.error("❌ Gemini Error:", error);
            removeTyping();
            if (error && error.message && error.message.includes("429")) {
                addMessage("API free quota exceeded. Please try again later or upgrade your plan.", "bot");
            } else {
                addMessage("Error connecting to AI", "bot");
            }
        }
    });

    // ---------------- UI HELPERS ----------------
    function addMessage(text, sender) {
        const msg = document.createElement("div");
        msg.className = `message ${sender}`;
        msg.innerText = text;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    function addTyping() {
        const typing = document.createElement("div");
        typing.id = "typing";
        typing.className = "message bot";
        typing.innerText = "Thinking...";
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById("typing");
        if (typing) typing.remove();
    }

    function saveHistory() {
        sessionStorage.setItem("chatHistory", JSON.stringify(chatHistory));
    }

    function renderHistory() {
        historyList.innerHTML = "";
        chatHistory.forEach((item, index) => {
            if (item.sender === "user") {
                const li = document.createElement("li");
                li.className = "history-item";
                li.innerText = item.text;
                li.dataset.index = index;
                historyList.appendChild(li);
            }
        });

        document.querySelectorAll(".history-item").forEach(li => {
            li.addEventListener("click", () => {
                const idx = parseInt(li.dataset.index);
                if (isNaN(idx)) return;

                messages.innerHTML = "";
                for (let i = 0; i <= idx; i++) {
                    addMessage(chatHistory[i].text, chatHistory[i].sender);
                }
            });
        });
    }

});
