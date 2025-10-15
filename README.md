# ==================== README.md ====================
# TeleStore Bot

A Telegram bot for organizing and streaming video files with a nested folder structure.

## Features

- 📁 **Folder Management**: Create, rename, and delete folders
- 🎬 **File Storage**: Upload videos/documents with automatic metadata extraction
- 🔗 **Direct Streaming**: Get embeddable URLs for instant playback
- ⬇️ **Direct Downloads**: Download files without additional pages
- 🎥 **Quality Detection**: Automatically detect video quality (720p, 1080p, etc.)
- 🗣️ **Language Detection**: Extract language info from filenames
- 📊 **Statistics**: Track views, downloads, and storage usage
- 🌐 **CORS Enabled**: Embed videos on any website

## Tech Stack

- **Bot Framework**: Pyrogram (Telegram MTProto API)
- **API Framework**: FastAPI
- **Database**: MongoDB (Motor async driver)
- **Deployment**: Docker (Koyeb-ready)

## Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo>
cd telestore-bot
```

2. **Create .env file**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the bot**
```bash
python main.py
```

The bot will start on `http://localhost:8000`

### Docker Deployment

1. **Build image**
```bash
docker build -t telestore-bot .
```

2. **Run container**
```bash
docker run -d \
  --name telestore \
  -p 8000:8000 \
  --env-file .env \
  telestore-bot
```

### Koyeb Deployment

1. **Connect your GitHub repository to Koyeb**

2. **Configure environment variables** in Koyeb dashboard:
   - `API_ID`
   - `API_HASH`
   - `BOT_TOKEN`
   - `MONGODB_URI`
   - `MONGODB_DB`
   - `BASE_APP_URL` (your Koyeb app URL)
   - `PORT` (leave as 8000)

3. **Deploy from Dockerfile**

4. **Update BASE_APP_URL** with your Koyeb URL after first deployment

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_ID` | Telegram API ID | `12345678` |
| `API_HASH` | Telegram API Hash | `abcdef123456...` |
| `BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `MONGODB_DB` | Database name | `telestore` |
| `BASE_APP_URL` | Your app's public URL | `https://app.koyeb.app` |
| `PORT` | Port to run on | `8000` |

## Getting Telegram Credentials

1. **API_ID and API_HASH**:
   - Visit https://my.telegram.org
   - Login with your phone number
   - Go to "API Development Tools"
   - Create a new application
   - Copy `api_id` and `api_hash`

2. **BOT_TOKEN**:
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow instructions
   - Copy the bot token

3. **MongoDB**:
   - Sign up at https://www.mongodb.com/cloud/atlas
   - Create a free cluster
   - Get connection string from "Connect" button
   - Replace `<password>` with your database password

## Usage

### Creating Folders
```
/newfolder My Movies
```

### Adding Files
1. Open folder from `/myfolders`
2. Click "Add Files"
3. Send your video files
4. Use `/done` when finished

### Getting Links
- Click any file in a folder
- Get Watch URL: `domain.com/fileId`
- Get Download URL: `domain.com/dl/fileId`

## URL Structure

- **Stream/Watch**: `https://your-domain.com/{fileId}`
- **Download**: `https://your-domain.com/dl/{fileId}`
- **Embedded Player**: `https://your-domain.com/watch/{fileId}`

## Supported Formats

- **Video**: MP4, MKV, AVI, MOV, WMV, FLV, WEBM
- **All formats supported by Telegram's 2GB file limit**

## API Endpoints
GET /api/folder_list?user_id=1740287480&page=1& page_size=200
GET /api/file_list/{folder_id} - Simplified file list with master_group_id
GET /api/stream/{master_group_id}?quality=1080p - Stream by master group
GET /api/quality_info/{file_id} - Get available qualities for a file
GET /api/master_info/{master_group_id} - Get master group information
GET /api/quality_folders/{parent_folder_id} - List quality subfolders
- `GET /` - API info
- `GET /health` - Health check
- `GET /{fileId}` - Stream file (direct video URL)
- `GET /watch/{fileId}` - Embedded player page
- `GET /dl/{fileId}` - Download file

## Features Explained

### Automatic Metadata Extraction
- Quality: 720p, 1080p, 4K, etc.
- Language: Hindi, English, Multi Audio, etc.
- Duration, file size, thumbnail

### Streaming Support
- Range requests for seeking
- Resume download support
- CORS enabled for embedding

### Database Indexes
Automatically creates indexes for:
- Fast folder lookups
- Quick file searches
- Efficient pagination

## License

MIT License

## Support

For issues and questions, open an issue on GitHub.
