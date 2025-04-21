"""
Application entry point
"""
import uvicorn
import argparse

from app.core.config import settings


def main():
    """
    Run the application with uvicorn
    """
    parser = argparse.ArgumentParser(description='Run the NAPOLCOM OMR Processing System')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload on file changes')
    parser.add_argument('--workers', type=int, default=settings.WORKERS_COUNT, help='Number of worker processes')
    
    args = parser.parse_args()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()
