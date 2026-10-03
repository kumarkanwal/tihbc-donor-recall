# WhatsApp Simulator Specification

The simulator is a donor's phone. It replaces the real WhatsApp app for the demo and must feel exactly
like WhatsApp. It is the only part of the UI styled like WhatsApp. Do not use the WhatsApp logo or
trademarked assets.

**Perspective:** the viewer is the donor. TIHBC messages are **incoming** (left, white bubbles).
Donor replies are **outgoing** (right, green bubbles, with ticks).

---

## 1. Panel
- Opened by the "Donor Phone" button (bottom-right) or any "View chat" link (opens directly on that donor).
- Slides in from the right, width about 400 px, full height, over the page (page stays usable).
- Contains a phone frame (rounded corners, status bar with demo-clock time and battery/signal icons).
- Close button outside the phone frame. Open/closed state and selected donor persist across page
  navigation (Zustand).

## 2. Screens Inside the Phone

### 2.1 Donor Picker (entry screen)
Each donor has their own phone, so the entry screen is a donor picker styled like a WhatsApp chat list:
- Header: "Select donor", search field, campaign filter.
- Rows: donor initials avatar, donor name, masked phone, preview of the latest message in their chat,
  time, unread count badge.
- Tapping a row opens that donor's conversation with TIHBC and calls `actions/open`.
- A back arrow in the conversation header returns to this picker.

### 2.2 Conversation
- **Header:** back arrow, TIHBC profile image (logo), name "Team Indus Health & Blood Center",
  subtitle "Business account", video/call/menu icons (non-functional).
- **Banner:** a "Viewing as: <donor name> (+92 300 *****67)" strip above the phone, outside the frame.
- **Wallpaper:** subtle beige pattern background.
- **Date separators:** "Today", "Yesterday", or date chips centered.
- **Business info chip** at top of a new chat: "This business uses a secure service..." style notice (generic wording).
- **Incoming bubble (TIHBC):** white, left, tail on first bubble of a group, timestamp bottom-right.
  - Media header: video thumbnail with play icon and duration, or image. Clicking plays/opens in a lightbox.
  - Body text with **bold**, _italic_ WhatsApp formatting rendered.
  - Quick-reply buttons rendered as separate full-width rows under the bubble, separated by thin lines,
    centered blue-green text. After the donor replies to that message, its buttons become disabled.
  - Slot options (reschedule) use the same button style (max 3 per message).
- **Outgoing bubble (donor):** light green, right, timestamp and ticks bottom-right.
  - Button replies show as a normal outgoing bubble with the button label.
- **Ticks:** single grey (sent), double grey (delivered), double blue (read). In the donor's view these
  apply to the donor's own messages; their state is driven by the system receiving the reply
  (sent → delivered immediately → read when processed).
- **Typing indicator:** "typing..." in the header subtitle and a three-dot bubble while
  `simulator.typing` is true.
- **Input bar:** emoji icon (non-functional), text field "Message", attach and camera icons
  (non-functional), send button (appears when text is entered). Enter sends.
- **Right-to-left:** Urdu messages render RTL with an Urdu font (`docs/brand.md`); mixed content
  uses `dir="auto"`.
- Auto-scroll to the newest message; "new messages" pill if scrolled up.

## 3. Behavior
- New messages arrive in real time via `message.created`; ticks update via `message.status_updated`.
- Opening a conversation marks TIHBC messages as read (only if the donor has read receipts on).
- Donors flagged unreachable show no incoming messages in their chat (the messages failed); the chat list
  shows them greyed with "Number not on WhatsApp" caption so the presenter can explain it.
- Sending a reply calls `POST /simulator/conversations/{donor_id}/replies`; the bubble appears
  optimistically and is reconciled with the server message.
- Automatic TIHBC responses (acknowledgements, slot offers) appear after a short typing indicator
  (1–2 seconds) for realism.

## 4. Visual Tokens (simulator only)

| Token | Value |
|---|---|
| Chat header background | `#008069` |
| Header text | `#FFFFFF` |
| Wallpaper | `#EFEAE2` |
| Incoming bubble | `#FFFFFF` |
| Outgoing bubble | `#D9FDD3` |
| Primary text | `#111B21` |
| Timestamp / secondary | `#667781` |
| Read ticks | `#53BDEB` |
| Button text | `#00A884` |
| Date chip | `#FFFFFF` with 90% opacity, text `#54656F` |
| Font | System UI stack (`-apple-system, Segoe UI, Roboto, Helvetica, Arial`), 14.2 px body |
| Bubble radius | 7.5 px, max width 80% |

## 5. Components (`frontend/components/simulator/`)
`SimulatorPanel`, `PhoneFrame`, `StatusBar`, `ChatList`, `ChatListItem`, `ChatHeader`, `MessageList`,
`DateSeparator`, `MessageBubble`, `MediaHeader`, `QuickReplyButtons`, `MessageTicks`, `TypingIndicator`,
`ChatInput`, `ViewingAsBanner`. Shared formatting helpers live in `frontend/lib/utils/whatsapp-format.ts`.
`PhonePreview` in the series editor reuses `MessageBubble`, `MediaHeader`, and `QuickReplyButtons`.
