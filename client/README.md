# Saytrix AI Frontend

Vue.js frontend for the Saytrix AI financial assistant.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Open http://localhost:3000

## Features

- Real-time chat with AI assistant
- Markdown rendering for rich responses
- Quick action buttons for common tasks
- Responsive design with Tailwind CSS
- Error handling and loading states

## Backend Requirements

Ensure your Flask backend is running on http://localhost:5000 with the following endpoints:
- POST /chat
- POST /quick-action