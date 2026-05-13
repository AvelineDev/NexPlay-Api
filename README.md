# NexPlay API 🎌

Backend API untuk NexPlay — scraper Anichin + MAL wrapper.

## Deploy ke Railway

1. Push repo ini ke GitHub
2. Buka [railway.app](https://railway.app) → Login dengan GitHub
3. New Project → Deploy from GitHub repo → pilih repo ini
4. Tunggu deploy selesai (~2 menit)
5. Klik **Settings** → **Networking** → **Generate Domain**
6. Copy URL-nya (contoh: `https://nexplay-api.up.railway.app`)

## Update URL di NexPlay

Buka `index.html`, cari baris ini:
```javascript
const A='https://puruboy-api.vercel.app/api/anime/anichin'
const M='https://puruboy-api.vercel.app/api/anime/mal'
```

Ganti dengan URL Railway kamu:
```javascript
const A='https://URL-RAILWAY-KAMU/api/anime/anichin'
const M='https://URL-RAILWAY-KAMU/api/anime/mal'
```

## Endpoints

### Anichin
| Endpoint | Keterangan |
|----------|------------|
| `GET /api/anime/anichin/home` | Konten halaman utama |
| `GET /api/anime/anichin/schedule` | Jadwal rilis |
| `GET /api/anime/anichin/search?q=query` | Cari anime |
| `GET /api/anime/anichin/detail?url=/seri/slug` | Detail anime |
| `GET /api/anime/anichin/stream?url=/slug` | Link stream episode |

### MAL
| Endpoint | Keterangan |
|----------|------------|
| `GET /api/anime/mal/popular?page=1` | Anime populer |
| `GET /api/anime/mal/ongoing?page=1` | Anime ongoing |
| `GET /api/anime/mal/genre?genreId=1` | Anime per genre |
| `GET /api/anime/mal/search?q=query` | Cari di MAL |

### Health Check
| Endpoint | Keterangan |
|----------|------------|
| `GET /health` | Status API |
