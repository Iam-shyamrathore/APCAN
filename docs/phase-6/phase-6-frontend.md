# Phase 6: Frontend Implementation — React 19 + TypeScript

## Overview

Phase 6 delivers the complete **web frontend** for APCAN Voice AI — a dark-themed healthcare portal built with React 19, TypeScript, Tailwind CSS v4, and Zustand. It connects to all backend APIs and provides real-time voice AI chat via WebSocket streaming.

| Metric            | Value                                                  |
| ----------------- | ------------------------------------------------------ |
| New source files  | 30                                                     |
| Framework         | React 19 + TypeScript + Vite 7                         |
| State management  | Zustand 5                                              |
| Styling           | Tailwind CSS v4 (dark healthcare theme)                |
| UI components     | CVA + Radix UI primitives (shadcn-style)               |
| Routing           | React Router v7 (protected + public routes)            |
| HTTP client       | Axios with JWT auto-refresh                            |
| Real-time         | WebSocket with auto-reconnect + streaming              |
| Pages             | 8 (Dashboard, Chat, Patients, Patient Detail, Appointments, Audit, Login, Signup) |

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                     Browser (SPA)                      │
│                                                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │  React     │  │  Zustand   │  │  Axios + JWT     │ │
│  │  Router v7 │  │  Stores    │  │  Auto-refresh    │ │
│  └─────┬──────┘  └─────┬──────┘  └────────┬─────────┘ │
│        │               │                  │            │
│  ┌─────┴───────────────┴──────────────────┘            │
│  │                                                     │
│  │  Pages: Dashboard │ Chat │ Patients │ Appointments  │
│  │         Audit │ Login │ Signup                      │
│  │                                                     │
│  │  ┌──────────────────────────────────────┐           │
│  │  │  WebSocket Hook (useWebSocket)       │           │
│  │  │  • 15 message types                  │           │
│  │  │  • Auto-reconnect (3s)               │           │
│  │  │  • Streaming chunks → chat store     │           │
│  │  └──────────────────────────────────────┘           │
│  │                                                     │
│  └─────────────────────────────────────────────────────┘
│        │  REST (/api/v1)          │  WS (/api/v1/voice/ws)
└────────┼──────────────────────────┼────────────────────┘
         ▼                          ▼
    ┌─────────────────────────────────────┐
    │         FastAPI Backend (:8000)      │
    │   Auth │ FHIR │ Voice │ Audit       │
    └─────────────────────────────────────┘
```

## Project Structure

```
frontend/
├── .env.example
├── index.html
├── package.json
├── vite.config.ts             # Vite + Tailwind plugin, /api proxy, @ alias
├── tsconfig.app.json          # Strict TS, path aliases
└── src/
    ├── main.tsx               # React 19 bootstrap
    ├── App.tsx                # BrowserRouter, route definitions
    ├── index.css              # Tailwind v4 @theme (dark palette)
    ├── lib/
    │   └── utils.ts           # cn(), formatDate(), formatTime(), relativeTime()
    ├── types/
    │   ├── api.ts             # TypeScript interfaces (User, Patient, Appointment, etc.)
    │   └── chat.ts            # WebSocket message types, AgentType, colors/labels
    ├── api/
    │   ├── client.ts          # Axios instance, JWT interceptors, auto-refresh
    │   ├── auth.ts            # login(), signup(), getMe()
    │   ├── patients.ts        # FHIR Patient CRUD
    │   ├── appointments.ts    # FHIR Appointment CRUD
    │   └── audit.ts           # getAuditLogs()
    ├── stores/
    │   ├── authStore.ts       # Zustand: user, tokens, login/signup/logout
    │   └── chatStore.ts       # Zustand: messages, streaming, tool calls
    ├── hooks/
    │   └── useWebSocket.ts    # WebSocket lifecycle, message routing, auto-reconnect
    ├── components/
    │   ├── ui/
    │   │   ├── button.tsx     # CVA button (6 variants, 4 sizes)
    │   │   ├── input.tsx      # Styled input with focus ring
    │   │   ├── card.tsx       # Card, CardHeader, CardTitle, CardContent
    │   │   ├── badge.tsx      # Badge (5 variants)
    │   │   └── spinner.tsx    # Animated loader
    │   ├── layout/
    │   │   ├── AppLayout.tsx  # Sidebar + Outlet layout
    │   │   └── ProtectedRoute.tsx  # Auth guard (redirects to /login)
    │   └── chat/
    │       ├── AgentBadge.tsx     # Color-coded agent indicator
    │       ├── ToolCallCard.tsx   # Tool execution status card
    │       ├── MessageBubble.tsx  # User/assistant chat bubbles
    │       └── ChatInput.tsx      # Auto-resize textarea
    └── pages/
        ├── DashboardPage.tsx      # Stats, quick actions, recent data
        ├── ChatPage.tsx           # Voice AI chat with WebSocket streaming
        ├── PatientsPage.tsx       # Patient list with search
        ├── PatientDetailPage.tsx  # Patient detail + contacts + appointments
        ├── AppointmentsPage.tsx   # Appointment grid with status badges
        ├── AuditPage.tsx          # Filterable audit log
        ├── LoginPage.tsx          # Email/password login
        └── SignupPage.tsx         # Registration form
```

## Tech Stack Details

### Dependencies

| Package              | Version | Purpose                    |
| -------------------- | ------- | -------------------------- |
| react                | 19.2.0  | UI framework               |
| react-router-dom     | 7.13.1  | Client-side routing        |
| zustand              | 5.0.11  | State management           |
| axios                | 1.13.6  | HTTP client                |
| tailwindcss          | 4.2.1   | Utility-first CSS          |
| @tailwindcss/vite    | 4.2.1   | Vite integration           |
| lucide-react         | 0.577.0 | Icons                      |
| class-variance-authority | 0.7.1 | Component variant pattern |
| clsx + tailwind-merge | —      | Class name composition     |
| react-hook-form      | 7.71.2  | Form state management      |
| zod                  | 4.3.6   | Schema validation          |
| date-fns             | 4.1.0   | Date utilities             |
| Radix UI (10 pkgs)   | —       | Accessible primitives      |

### Build Configuration

**Vite** (`vite.config.ts`):
- Plugins: `@vitejs/plugin-react`, `@tailwindcss/vite`
- Path alias: `@/` → `./src/`
- Dev server proxy: `/api` → `http://localhost:8000` (avoids CORS)

**TypeScript** (`tsconfig.app.json`):
- Target: ES2022, strict mode enabled
- Path alias: `@/*` → `./src/*`

## Feature Details

### 1. Design System — Dark Healthcare Theme

Tailwind CSS v4's `@theme` directive defines a cohesive dark palette:

| Token         | Value     | Usage                 |
| ------------- | --------- | --------------------- |
| `--background`| `#0f172a` | Page background       |
| `--foreground`| `#f8fafc` | Primary text          |
| `--card`      | `#1e293b` | Card surfaces         |
| `--primary`   | `#6366f1` | Actions, links        |
| `--accent`    | `#334155` | Hover states, borders |
| `--destructive`| `#ef4444`| Errors, delete        |
| `--success`   | `#22c55e` | Confirmations         |

Font: Inter with system sans-serif fallback. Border radius tokens from `sm` (0.375rem) to `xl` (1rem).

### 2. Authentication Flow

```
LoginPage                          Backend
   │                                  │
   │  POST /auth/login               │
   │  (form-urlencoded)              │
   ├─────────────────────────────────►│
   │                                  │
   │  { access_token, refresh_token } │
   │◄─────────────────────────────────┤
   │                                  │
   │  GET /auth/me                   │
   │  (Bearer access_token)          │
   ├─────────────────────────────────►│
   │                                  │
   │  { user }                       │
   │◄─────────────────────────────────┤
   │                                  │
   │  → Navigate to /                │
```

- **Zustand `authStore`** holds `user`, `accessToken`, `refreshToken`
- **Axios interceptor** attaches Bearer token to every request
- **401 interceptor** automatically refreshes expired tokens and retries the request
- **`ProtectedRoute`** wraps all authenticated routes — redirects to `/login` if no token

### 3. Voice AI Chat — Real-Time WebSocket

The chat page connects via WebSocket to stream AI responses in real-time:

```
ChatPage                  useWebSocket               Backend WS
   │                          │                          │
   │  connect()               │                          │
   │─────────────────────────►│  ws://host/api/v1/       │
   │                          │  voice/ws?token=JWT      │
   │                          │─────────────────────────►│
   │                          │                          │
   │                          │  session_created         │
   │                          │◄─────────────────────────┤
   │                          │                          │
   │  sendMessage("...")      │                          │
   │─────────────────────────►│  {type: text_input}      │
   │                          │─────────────────────────►│
   │                          │                          │
   │                          │  agent_switch            │
   │                          │◄─────────────────────────┤
   │  chatStore.setAgent()    │                          │
   │◄─────────────────────────┤                          │
   │                          │  stream_start            │
   │                          │◄─────────────────────────┤
   │  chatStore.startStream() │                          │
   │◄─────────────────────────┤                          │
   │                          │  stream_chunk (×N)       │
   │                          │◄─────────────────────────┤
   │  chatStore.appendChunk() │                          │
   │◄─────────────────────────┤                          │
   │                          │  tool_call               │
   │                          │◄─────────────────────────┤
   │  chatStore.addToolCall() │                          │
   │◄─────────────────────────┤                          │
   │                          │  tool_result             │
   │                          │◄─────────────────────────┤
   │  chatStore.updateTool()  │                          │
   │◄─────────────────────────┤                          │
   │                          │  stream_end              │
   │                          │◄─────────────────────────┤
   │  chatStore.endStream()   │                          │
   │◄─────────────────────────┤                          │
```

**WebSocket Message Types Handled (15):**

| Message Type     | Action                                        |
| ---------------- | --------------------------------------------- |
| `session_created`| Store session ID                              |
| `agent_switch`   | Update active agent badge                     |
| `stream_start`   | Create empty assistant message, start cursor  |
| `stream_chunk`   | Append text chunk to message                  |
| `stream_end`     | End streaming animation                       |
| `tool_call`      | Show tool call card with loading spinner      |
| `tool_result`    | Update tool card with success/failure         |
| `text_response`  | Display final response (non-streaming path)   |
| `agent_error`    | Show error from specific agent                |
| `rate_limited`   | Show rate limit warning                       |
| `error`          | Show generic error                            |
| `pong`           | Heartbeat acknowledgment (no-op)              |

**Auto-reconnect:** Socket reconnects after 3 seconds on unexpected close.

### 4. Chat Components

- **`AgentBadge`** — Color-coded pill showing which agent is active (intake=blue, scheduling=purple, care=emerald, admin=amber, general=gray)
- **`ToolCallCard`** — Compact card showing tool name + status (spinner → checkmark/failed)
- **`MessageBubble`** — User messages (right-aligned, primary bg) / assistant messages (left-aligned, card bg) with avatar icons, agent badges, embedded tool cards, streaming cursor animation, and timestamps
- **`ChatInput`** — Auto-resizing textarea, Enter to send, Shift+Enter for newline, disabled when disconnected

### 5. Patient Management

**Patients List (`/patients`):**
- Fetches up to 50 patients from FHIR Patient endpoint on mount
- Client-side search filter (name, MRN)  
- Grid of cards with initials avatar, name, MRN, DOB, gender badge
- Links to patient detail page

**Patient Detail (`/patients/:id`):**
- Loads individual patient record and recent appointments
- Contact information card (phone, email, address)
- Emergency contact card
- Recent appointments list with status

### 6. Appointment Management

Grid of appointment cards showing:
- Description or appointment ID
- Date and time (formatted)
- Provider name
- Status badge (proposed/pending/booked/arrived/fulfilled/cancelled/noshow)

### 7. Audit Log

- Fetches logs from `/audit/logs` endpoint
- Success/failure indicator (green/red dot)
- Displays: action, tool name, agent, user, session, timestamp
- Client-side filtering by action, tool, or agent

### 8. Dashboard

Overview page with:
- Personalized greeting using logged-in user's name
- Stats cards (patient count, appointment count, active agents)
- Quick action card linking to Voice AI Chat
- Two-column layout: Recent Patients + Upcoming Appointments

## Route Map

| Path               | Component          | Auth Required | Layout   |
| ------------------ | ------------------ | ------------- | -------- |
| `/login`           | LoginPage          | No            | None     |
| `/signup`          | SignupPage         | No            | None     |
| `/`                | DashboardPage      | Yes           | Sidebar  |
| `/chat`            | ChatPage           | Yes           | Sidebar  |
| `/patients`        | PatientsPage       | Yes           | Sidebar  |
| `/patients/:id`    | PatientDetailPage  | Yes           | Sidebar  |
| `/appointments`    | AppointmentsPage   | Yes           | Sidebar  |
| `/audit`           | AuditPage          | Yes           | Sidebar  |
| `*`                | → Redirect to `/`  | —             | —        |

## UI Component Library

All components follow the **shadcn/ui pattern** (CVA + Radix primitives), built manually since the shadcn CLI could not be used.

### Button

6 variants × 4 sizes. Uses `@radix-ui/react-slot` for polymorphic `asChild` rendering.

```tsx
<Button variant="destructive" size="sm">Delete</Button>
<Button asChild><Link to="/chat">Open Chat</Link></Button>
```

### Badge

5 variants: `default` (primary), `success`, `warning`, `destructive`, `outline`.

### Card

Composable: `Card > CardHeader > CardTitle + CardDescription` + `CardContent`.

### Input

Styled with dark background, focus ring, placeholder styling.

## Development Setup

```bash
# From project root
./dev.sh              # Starts DB, Redis, backend, and frontend

# Or manually:
cd frontend
npm install           # First time only
npm run dev           # Vite dev server on :5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`, so no CORS issues during development.

## State Management

### Auth Store (Zustand)

```
┌─────────────────────────────────┐
│ useAuthStore                    │
├─────────────────────────────────┤
│ user: User | null               │
│ accessToken: string | null      │
│ refreshToken: string | null     │
│ isLoading: boolean              │
│ error: string | null            │
├─────────────────────────────────┤
│ login(email, password)          │
│ signup(email, password, name)   │
│ fetchUser()                     │
│ logout()                        │
│ setTokens(access, refresh)      │
└─────────────────────────────────┘
```

### Chat Store (Zustand)

```
┌─────────────────────────────────┐
│ useChatStore                    │
├─────────────────────────────────┤
│ messages: ChatMessage[]         │
│ sessionId: string | null        │
│ activeAgent: string | null      │
│ isConnected: boolean            │
│ isStreaming: boolean            │
│ streamingMessageId: string      │
├─────────────────────────────────┤
│ addMessage(msg)                 │
│ startStreaming(id, agent?)      │
│ appendChunk(chunk)              │
│ endStreaming()                  │
│ addToolCall(tool)               │
│ updateToolResult(name, success) │
│ setActiveAgent(agent)           │
│ setConnected(bool)              │
│ setSessionId(id)                │
│ clearMessages()                 │
└─────────────────────────────────┘
```

## API Integration

All API calls go through a shared Axios instance (`src/api/client.ts`):

- **Base URL:** `/api/v1` (proxied by Vite to backend)
- **Request interceptor:** Attaches `Authorization: Bearer <token>` from auth store
- **Response interceptor:** On `401`, attempts token refresh via `/auth/refresh`, retries original request. On refresh failure, triggers logout.

### Endpoints Used

| Module        | Endpoint                    | Method | Purpose                 |
| ------------- | --------------------------- | ------ | ----------------------- |
| Auth          | `/auth/login`               | POST   | OAuth2 login            |
| Auth          | `/auth/signup`              | POST   | User registration       |
| Auth          | `/auth/me`                  | GET    | Current user profile    |
| Auth          | `/auth/refresh`             | POST   | Token refresh           |
| FHIR Patient  | `/fhir/Patient`             | GET    | Search patients         |
| FHIR Patient  | `/fhir/Patient/:id`         | GET    | Get patient             |
| FHIR Patient  | `/fhir/Patient`             | POST   | Create patient          |
| FHIR Appt     | `/fhir/Appointment`         | GET    | Search appointments     |
| FHIR Appt     | `/fhir/Appointment/:id`     | GET    | Get appointment         |
| FHIR Appt     | `/fhir/Appointment`         | POST   | Create appointment      |
| Audit         | `/audit/logs`               | GET    | Query audit logs        |
| Voice         | `/voice/ws` (WebSocket)     | WS     | Real-time AI chat       |
