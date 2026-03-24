## MindPulse Backend — Configuration

### Required/Optional API keys
- `API_KEY` (optional but recommended): When set, all API routes (except `/`, `/health`, `/docs`, `/openapi.json`, `/redoc`) require the `X-API-Key` header to match this value. Leave unset to disable API-key auth.
- `ALLOWED_ORIGINS`: Comma-separated CORS origins (e.g., `http://localhost:3000`).

See `.env.example` for a starter environment file.
