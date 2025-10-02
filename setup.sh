# ==================== setup.sh ====================
# Quick setup script for local development

echo "🚀 TeleStore Bot Setup"
echo "======================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - API_ID (from https://my.telegram.org)"
    echo "   - API_HASH"
    echo "   - BOT_TOKEN (from @BotFather)"
    echo "   - MONGODB_URI (from MongoDB Atlas)"
    echo ""
else
    echo "✅ .env file exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Run: python main.py"
echo "3. Test bot in Telegram"
echo ""