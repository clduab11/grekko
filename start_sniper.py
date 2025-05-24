#!/usr/bin/env python3
"""
Quick start script for Grekko Solana Sniper Bot.

This script initializes the database and starts the API server
with the sniper bot ready to go.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.database import init_db
from src.utils.logger import configure_logging, get_logger
from src.api.main import app
import uvicorn


def check_environment():
    """Check required environment variables."""
    required_vars = [
        'HELIUS_API_KEY',
        'SOLANA_WALLET_PRIVATE_KEY',
        'DATABASE_URL',
        'API_TOKEN'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment")
        sys.exit(1)
    
    print("✅ All required environment variables found")


def setup_example_env():
    """Create example .env file if it doesn't exist."""
    env_file = Path(".env")
    
    if not env_file.exists():
        example_content = """# Grekko Sniper Bot Configuration

# Helius API Key (get from https://helius.xyz)
HELIUS_API_KEY=your-helius-api-key-here

# Solana Wallet Private Key (hex format, no brackets)
# Generate with: solana-keygen new --no-bip39-passphrase
SOLANA_WALLET_PRIVATE_KEY=your-wallet-private-key-hex

# Database URL
DATABASE_URL=postgresql://grekko:grekkopassword@localhost:5432/grekko

# API Authentication Token
API_TOKEN=grekko-secret-token

# Optional: Birdeye API Key for enhanced token analysis
BIRDEYE_API_KEY=your-birdeye-api-key
"""
        
        with open(env_file, 'w') as f:
            f.write(example_content)
        
        print(f"📝 Created example .env file. Please edit it with your actual values.")
        sys.exit(0)


async def main():
    """Main startup function."""
    print("""
    ╔═══════════════════════════════════════════╗
    ║        GREKKO SOLANA SNIPER BOT           ║
    ║   High-Speed Memecoin Trading System      ║
    ╚═══════════════════════════════════════════╝
    """)
    
    # Check/create example env
    setup_example_env()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment
    check_environment()
    
    # Configure logging
    configure_logging(log_level='INFO', log_to_file=True, log_to_console=True)
    logger = get_logger('startup')
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct")
        sys.exit(1)
    
    # Start API server
    print("\n🚀 Starting Grekko API Server...")
    print("   API docs: http://localhost:8000/docs")
    print("   WebSocket: ws://localhost:8000/ws")
    print("\nBot Control:")
    print("   Start bot: POST http://localhost:8000/bot/start")
    print("   Stop bot: POST http://localhost:8000/bot/stop")
    print("   Status: GET http://localhost:8000/bot/status")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Grekko sniper bot stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)