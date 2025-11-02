# GenAIAlchemist - Folder Structure & Technologies

## Project Overview
A full-stack travel booking application with AI-powered travel concierge using Google Gemini, featuring an Easemytrip UI replica frontend and Flask backend.

---

## 📁 Root Directory Structure

```
GenAIAlchemist/
├── backend/                          # Python Flask Backend
├── frontend/                          # React + TypeScript Frontend
├── README.md                          # Main project documentation
├── .gitignore                         # Git ignore rules
└── FOLDER_STRUCTURE.md                # This file
```

---

## 🔧 Backend Structure (Python/Flask)

### Technologies Used:
- **Flask** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Google ADK** - Gemini AI integration
- **Amadeus API** - Flight and hotel booking services
- **Python-dotenv** - Environment variable management
- **Requests** - HTTP library

```
backend/
├── __pycache__/                       # Python bytecode cache
├── app.py                             # Flask application entry point
├── agent_runner.py                    # Agent execution runner
├── config.env                         # Environment variables (API keys, secrets)
├── requirements.txt                   # Python dependencies
│
├── agents/                            # AI Agent System
│   ├── __init__.py
│   ├── agent.py                       # Base agent class
│   ├── prompt.py                      # Agent prompts
│   │
│   ├── orchestrators/                 # High-level orchestration agents
│   │   ├── planning_agent/            # Travel planning agent
│   │   │   ├── agent.py
│   │   │   └── prompt.py
│   │   ├── inspiration_agent/        # Travel inspiration agent
│   │   │   └── agent.py
│   │   └── booking_agent/            # Booking handling agent
│   │       └── agent.py
│   │
│   ├── tool_agents/                   # Specialized tool agents
│   │   └── transportation/
│   │       └── train_search_agent/    # Train search agent
│   │           └── agent.py
│   │
│   ├── parallel_agents/               # Parallel processing agents
│   │   └── ...
│   │
│   ├── loop_agents/                   # Loop-based agents
│   │   └── ...
│   │
│   ├── transactional_agents/          # Transaction handling agents
│   │   └── ...
│   │
│   └── travel_concierge/              # Travel concierge agent
│       └── agent.py
│
├── tools/                             # Backend Tools & Services
│   ├── __init__.py
│   ├── amadeus_flights.py            # Amadeus flight search service
│   ├── amadeus_hotels.py             # Amadeus hotel search service
│   ├── indian_railways.py            # Indian Railways integration
│   ├── map_tools.py                  # Google Maps integration
│   ├── memory.py                     # Memory management
│   ├── places.py                     # Places/POI search
│   ├── search.py                     # Search functionality
│   │
│   ├── apis/                         # External API integrations
│   │   └── ...
│   │
│   ├── helpers/                      # Utility helpers
│   │   └── ...
│   │
│   └── validators/                   # Data validators
│       └── ...
│
├── shared_libraries/                 # Shared utility libraries
│   └── ...
│
├── utils/                            # Utility functions
│   └── ...
│
└── profiles/                         # User profiles and configurations
    └── ...
```

---

## 🎨 Frontend Structure (React/TypeScript)

### Technologies Used:
- **React 18.3.1** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite 4.5.0** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
- **React Hook Form** - Form state management
- **Recharts** - Chart library
- **Lucide React** - Icon library
- **React Day Picker** - Date picker
- **Sonner** - Toast notifications
- **Vaul** - Drawer component
- **Embla Carousel** - Carousel component
- **Next Themes** - Theme management
- **Date-fns** - Date utility library

```
frontend/
└── Easemytrip UI/                    # Frontend application
    ├── node_modules/                  # NPM dependencies
    ├── package.json                  # Dependencies and scripts
    ├── package-lock.json             # Dependency lock file
    ├── vite.config.ts                # Vite configuration
    ├── index.html                    # HTML entry point
    ├── README.md                     # Frontend documentation
    │
    └── src/                          # Source code
        ├── main.tsx                  # React application entry point
        ├── App.tsx                   # Main App component
        ├── index.css                 # Global styles
        ├── README.md                 # Source documentation
        ├── Attributions.md           # Attribution credits
        │
        ├── components/               # React components
        │   ├── ui/                   # Reusable UI components (Radix UI)
        │   │   ├── accordion.tsx
        │   │   ├── alert-dialog.tsx
        │   │   ├── avatar.tsx
        │   │   ├── button.tsx
        │   │   ├── card.tsx
        │   │   ├── checkbox.tsx
        │   │   ├── dialog.tsx
        │   │   ├── dropdown-menu.tsx
        │   │   ├── input.tsx
        │   │   ├── label.tsx
        │   │   ├── select.tsx
        │   │   ├── slider.tsx
        │   │   ├── tabs.tsx
        │   │   ├── toast.tsx
        │   │   └── ...
        │   │
        │   ├── features/             # Feature-specific components
        │   │   ├── flights/          # Flight booking components
        │   │   ├── hotels/           # Hotel booking components
        │   │   ├── trains/           # Train booking components
        │   │   └── itinerary/        # Itinerary components
        │   │
        │   ├── layout/               # Layout components
        │   │   ├── Header.tsx
        │   │   ├── Footer.tsx
        │   │   ├── Sidebar.tsx
        │   │   └── Navigation.tsx
        │   │
        │   └── common/               # Common/shared components
        │       ├── Loading.tsx
        │       ├── ErrorBoundary.tsx
        │       └── ...
        │
        ├── pages/                    # Page components (if using routing)
        │   ├── Home.tsx
        │   ├── Flights.tsx
        │   ├── Hotels.tsx
        │   └── ...
        │
        ├── hooks/                    # Custom React hooks
        │   ├── useAuth.ts
        │   ├── useApi.ts
        │   └── ...
        │
        ├── services/                 # API service layer
        │   ├── api.ts               # API client configuration
        │   ├── flights.service.ts
        │   ├── hotels.service.ts
        │   └── chat.service.ts      # Chat/Agent service
        │
        ├── store/                    # State management (if using Redux/Zustand)
        │   ├── slices/
        │   └── store.ts
        │
        ├── utils/                    # Utility functions
        │   ├── formatters.ts
        │   ├── validators.ts
        │   └── constants.ts
        │
        ├── types/                    # TypeScript type definitions
        │   ├── api.types.ts
        │   ├── flight.types.ts
        │   ├── hotel.types.ts
        │   └── index.ts
        │
        ├── styles/                   # Additional styles
        │   ├── globals.css
        │   └── themes.css
        │
        └── assets/                   # Static assets
            ├── images/
            ├── icons/
            └── fonts/
```

---

## 🔌 API Endpoints

### Backend API Routes (Flask):
```
POST   /chat           # Non-streaming chat endpoint
POST   /chatStream     # Streaming chat endpoint (SSE)
POST   /getSession     # Initialize chat session
```

---

## 🌐 External Integrations

### APIs & Services:
- **Google Gemini API** - AI conversation and planning
- **Amadeus Travel API** - Flight and hotel search/booking
- **Google Maps API** - Location services and maps
- **RapidAPI (IRCTC)** - Indian Railways integration
- **Places API** - Points of interest search

---

## 📦 Key Dependencies Summary

### Backend (Python):
```txt
flask                    # Web framework
flask-cors              # CORS handling
google-adk              # Google Gemini AI
amadeus                 # Travel API
requests                # HTTP client
python-dotenv           # Environment variables
```

### Frontend (Node.js):
```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "@radix-ui/*": "^1.x",    // UI primitives
  "vite": "^4.5.0",
  "tailwindcss": "*",
  "react-hook-form": "^7.55.0",
  "recharts": "^2.15.2",
  "lucide-react": "^0.487.0"
}
```

---

## 🚀 Development Scripts

### Backend:
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
# or
flask run
```

### Frontend:
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build
```

---

## 🔒 Environment Variables

### Backend (`config.env`):
```env
GEMINI_API_KEY=...
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
AMADEUS_CLIENT_ID=...
AMADEUS_CLIENT_SECRET=...
GOOGLE_MAPS_KEY=...
RAPID_API_KEY=...
INDIAN_RAPID_HOST=...
```

### Frontend:
Create `.env` file for frontend environment variables:
```env
VITE_API_URL=http://localhost:5000
VITE_GOOGLE_MAPS_KEY=...
```

---

## 📝 Notes

- The backend uses an agent-based architecture with multiple specialized agents
- The frontend is a single-page application built with React and Vite
- All API keys and secrets should be stored in environment variables
- The application supports streaming responses for real-time chat interactions
- The UI is a replica of Easemytrip's design (Figma reference available)

---

## 🏗️ Architecture Pattern

**Backend:** Agent-based architecture with:
- Orchestrator agents (planning, inspiration, booking)
- Tool agents (transportation, search)
- Parallel processing capabilities
- Memory management for session persistence

**Frontend:** Component-based architecture with:
- Reusable UI components (Radix UI)
- Feature-based organization
- Service layer for API communication
- Type-safe TypeScript implementation

