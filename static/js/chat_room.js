document.addEventListener("DOMContentLoaded", () => {
    // Stop early if the chat page bootstrap data or DOM hooks are missing.
    if (typeof chatBootstrap === "undefined") {
        return;
    }

    const bookingId = chatBootstrap.bookingId;
    const userId = chatBootstrap.userId;
    const messagesContainer = document.getElementById("messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatStatus = document.getElementById("chat-status");
    const chatError = document.getElementById("chat-error");
    const chatSend = document.getElementById("chat-send");
    const chatImageInput = document.getElementById("chat-image-input");
    const chatImageButton = document.getElementById("chat-image-button");
    const chatImagePreview = document.getElementById("chat-image-preview");
    const chatImageName = document.getElementById("chat-image-name");
    const chatImageClear = document.getElementById("chat-image-clear");
    const csrfTokenInput = chatForm ? chatForm.querySelector("input[name='csrfmiddlewaretoken']") : null;
    const uploadUrl = chatBootstrap.uploadUrl;

    if (
        !messagesContainer ||
        !chatForm ||
        !chatInput ||
        !chatStatus ||
        !chatError ||
        !chatSend ||
        !chatImageInput ||
        !chatImageButton ||
        !chatImagePreview ||
        !chatImageName ||
        !chatImageClear ||
        !csrfTokenInput ||
        !uploadUrl
    ) {
        return;
    }

    // Use the matching websocket scheme so chat works on both HTTP and HTTPS.
    const websocketScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const chatSocket = new WebSocket(
        `${websocketScheme}://${window.location.host}/ws/chat/${bookingId}/`
    );

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function setStatus(message, tone) {
        chatStatus.textContent = message;
        chatStatus.dataset.tone = tone || "neutral";
    }

    function selectedImageFile() {
        return chatImageInput.files && chatImageInput.files[0] ? chatImageInput.files[0] : null;
    }

    function updateSendAvailability(enabled) {
        const composerEnabled = typeof enabled === "boolean" ? enabled : !chatInput.disabled;
        chatSend.disabled = !composerEnabled || (!chatInput.value.trim() && !selectedImageFile());
    }

    function setComposerEnabled(enabled) {
        chatInput.disabled = !enabled;
        chatImageButton.disabled = !enabled;
        updateSendAvailability(enabled);
    }

    function showError(message) {
        if (!message) {
            chatError.hidden = true;
            chatError.textContent = "";
            return;
        }

        chatError.hidden = false;
        chatError.textContent = message;
    }

    function removeEmptyState() {
        const emptyState = document.getElementById("chat-empty-state");
        if (emptyState) {
            emptyState.remove();
        }
    }

    function updateImagePreview() {
        const imageFile = selectedImageFile();
        if (!imageFile) {
            chatImagePreview.hidden = true;
            chatImageName.textContent = "";
            updateSendAvailability();
            return;
        }

        chatImagePreview.hidden = false;
        chatImageName.textContent = imageFile.name;
        updateSendAvailability();
    }

    function clearSelectedImage() {
        chatImageInput.value = "";
        updateImagePreview();
    }

    function buildMessageElement(data) {
        const existingMessage = data.id
            ? messagesContainer.querySelector(`[data-message-id="${data.id}"]`)
            : null;
        if (existingMessage) {
            return null;
        }

        const messageArticle = document.createElement("article");
        messageArticle.classList.add("message");
        if (data.id) {
            messageArticle.dataset.messageId = data.id;
        }

        const isCurrentUser = Number(data.sender_id) === Number(userId);
        messageArticle.classList.add(isCurrentUser ? "you" : "other");

        if (!isCurrentUser) {
            const avatar = document.createElement("div");
            avatar.className = "message-avatar";
            avatar.textContent = (data.sender_username || "?").charAt(0).toUpperCase();
            messageArticle.appendChild(avatar);
        }

        const stack = document.createElement("div");
        stack.className = "message-stack";

        const author = document.createElement("div");
        author.className = "message-author";
        author.textContent = isCurrentUser ? "You" : data.sender_username || "Guest";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        if (data.image_url) {
            const imageLink = document.createElement("a");
            imageLink.className = "message-image-link";
            imageLink.href = data.image_url;
            imageLink.target = "_blank";
            imageLink.rel = "noopener noreferrer";

            const image = document.createElement("img");
            image.className = "message-image";
            image.src = data.image_url;
            image.alt = data.image_name || "Shared chat image";
            imageLink.appendChild(image);
            bubble.appendChild(imageLink);
        }

        if (data.content) {
            const messageText = document.createElement("div");
            messageText.className = "message-text";
            messageText.textContent = data.content;
            bubble.appendChild(messageText);
        }

        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = data.timestamp_label || data.timestamp || "";

        stack.appendChild(author);
        stack.appendChild(bubble);
        stack.appendChild(meta);
        messageArticle.appendChild(stack);

        return messageArticle;
    }

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.error) {
            showError(data.error);
            return;
        }

        removeEmptyState();
        const messageElement = buildMessageElement(data);
        if (!messageElement) {
            return;
        }

        messagesContainer.appendChild(messageElement);
        showError("");
        scrollToBottom();
    };

    chatSocket.onopen = function() {
        setStatus("Active now", "connected");
        setComposerEnabled(true);
        showError("");
        chatInput.focus();
    };

    chatSocket.onclose = function() {
        setStatus("Connection lost", "disconnected");
        setComposerEnabled(false);
        showError("Chat disconnected. Refresh the page or restart the ASGI server.");
    };

    setStatus("Connecting...", "neutral");
    setComposerEnabled(false);
    scrollToBottom();

    chatInput.addEventListener("input", () => {
        updateSendAvailability();
    });

    chatImageButton.addEventListener("click", () => {
        if (!chatImageButton.disabled) {
            chatImageInput.click();
        }
    });

    chatImageInput.addEventListener("change", () => {
        updateImagePreview();
        showError("");
    });

    chatImageClear.addEventListener("click", () => {
        clearSelectedImage();
        chatInput.focus();
    });

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        const imageFile = selectedImageFile();
        if (message === "" && !imageFile) return;
        if (chatSocket.readyState !== WebSocket.OPEN) {
            showError("Chat is still connecting. Please wait a moment and try again.");
            return;
        }

        if (imageFile) {
            const payload = new FormData();
            payload.append("content", message);
            payload.append("image", imageFile);

            chatSend.disabled = true;
            fetch(uploadUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfTokenInput.value,
                },
                body: payload,
            })
                .then(async (response) => {
                    const rawBody = await response.text();
                    let data = {};
                    try {
                        data = rawBody ? JSON.parse(rawBody) : {};
                    } catch (error) {
                        data = {};
                    }

                    if (!response.ok) {
                        throw new Error(data.error || "Unable to upload image.");
                    }
                    return data;
                })
                .then((data) => {
                    removeEmptyState();
                    const messageElement = buildMessageElement(data);
                    if (messageElement) {
                        messagesContainer.appendChild(messageElement);
                        scrollToBottom();
                    }
                    chatInput.value = "";
                    clearSelectedImage();
                    showError("");
                    chatInput.focus();
                })
                .catch((error) => {
                    showError(error.message || "Unable to upload image.");
                })
                .finally(() => {
                    updateSendAvailability();
                });
            return;
        }

        chatSocket.send(JSON.stringify({
            "content": message
        }));
        chatInput.value = "";
        showError("");
        updateSendAvailability();
        chatInput.focus();
    });
});
