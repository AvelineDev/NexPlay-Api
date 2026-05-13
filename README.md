---
title: NexPlay API
emoji: 🎌
colorFrom: purple
colorTo: cyan
sdk: docker
pinned: false
---

# NexPlay API
Backend API untuk NexPlay — Anichin scraper + MAL wrapper.

## Endpoints

### Anichin
- `GET /api/anime/anichin/home`
- `GET /api/anime/anichin/schedule`
- `GET /api/anime/anichin/search?q=query`
- `GET /api/anime/anichin/detail?url=/seri/slug`
- `GET /api/anime/anichin/stream?url=/slug`

### MAL
- `GET /api/anime/mal/popular?page=1`
- `GET /api/anime/mal/ongoing?page=1`
- `GET /api/anime/mal/genre?genreId=1`
- `GET /api/anime/mal/search?q=query`

### Health
- `GET /health`
