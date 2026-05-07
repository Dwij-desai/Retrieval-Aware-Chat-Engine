# Frontend Design Plan: Zed-Inspired AI Chatbot

## Objective
Build a clean, ultra-minimalist web frontend for the RAG chatbot. The design is heavily inspired by Zed's design philosophy—high performance, industrial aesthetic, and developer-first experience—but radically simplified to focus solely on the chat interface.

## Tech Stack
- **Framework:** React with TypeScript (via Vite for speed).
- **Styling:** Vanilla CSS. This provides the strict control necessary to achieve a pure, minimalist "editor-like" aesthetic without the overhead of utility classes.
- **Backend Integration:** Standard Fetch API communicating with the existing FastAPI backend (`http://localhost:8000/ask`).

## 1. Visual Style (Simpler, Industrial)
*   **Theme:** Strict Dark Mode. Backgrounds will use deep grays/blacks (e.g., `#1e1e20`), and text will be crisp off-white (`#f1f1f1`).
*   **Typography:** 
    *   UI Elements (buttons, sidebar): System sans-serif (Inter, San Francisco).
    *   Chat Content & Inputs: System monospaced fonts (Menlo, Monaco, JetBrains Mono) to mimic a code editor environment.
*   **Aesthetic:** High contrast with sharp edges (no rounded corners, `border-radius: 0`). Dividers and layout boundaries will use thin, subtle borders (`1px solid #333`). No shadows, no gradients. Pure function.

## 2. Navigation Structure (Simpler, Two-Column)
*   **Left Sidebar (Narrow, e.g., 220px):**
    *   **Action:** A stark, bordered "New Chat" button at the top.
    *   **List:** A simple vertical list of recent sessions (managed locally or via session storage).
*   **Main Content Area:**
    *   **Header:** Minimal title showing the current `chat_id`.
    *   **Chat Log:** A scrollable pane. Instead of traditional "chat bubbles", messages will span the width of the container. 
        *   User messages: Indented slightly or styled with a subtle left border.
        *   Assistant messages: Styled like standard editor output/markdown.
    *   **Input Dock:** Fixed at the bottom. A borderless (or minimally bordered) monospaced textarea that auto-expands slightly, resembling a command palette or terminal prompt.

## 3. User Experience (UX) (Keyboard-Centric)
*   **Keyboard First:**
    *   Press `Enter` to send the message (without needing Shift).
    *   Input field auto-focuses on page load and after every sent message.
*   **Editor-Like Flow:**
    *   While waiting for the backend response, a simple visual indicator (like a blinking block cursor `█`) will denote activity.
    *   Assistant responses are optimized for reading technical content, focusing on clear text block spacing rather than enclosed bubbles.
*   **State Management:**
    *   The React app will maintain the active `chat_id` and append messages locally while the backend request processes, ensuring the UI feels instantly responsive.