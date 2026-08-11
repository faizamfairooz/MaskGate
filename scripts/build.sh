#!/bin/bash

# MaskGate Build Script
# This script builds the frontend for production deployment

echo "🔨 Building MaskGate for production..."

# Build frontend
echo "🎨 Building frontend..."
cd frontend

if [ -d "node_modules" ]; then
    npm run build
    
    if [ -d "dist" ]; then
        echo "✅ Frontend build complete!"
        echo "📁 Build output: frontend/dist/"
    else
        echo "❌ Frontend build failed"
        exit 1
    fi
else
    echo "❌ Frontend dependencies not installed. Please run ./scripts/setup.sh first"
    exit 1
fi

cd ..

# Create production directory structure
echo "📁 Creating production directory structure..."
mkdir -p production/backend
mkdir -p production/frontend

# Copy backend files
echo "📦 Copying backend files..."
cp -r backend/app production/backend/
cp backend/requirements.txt production/backend/
cp -r backend/tests production/backend/

# Copy frontend build
echo "📦 Copying frontend build..."
cp -r frontend/dist production/frontend/

# Copy configuration files
echo "📝 Copying configuration files..."
cp .env.example production/.env.example
cp database/schema.sql production/
cp database/seed.sql production/

# Create production README
cat > production/README.md << 'EOF'
# MaskGate Production Deployment

This directory contains the production build of MaskGate.

## Directory Structure

- `backend/` - Backend application files
- `frontend/` - Frontend static files
- `schema.sql` - Database schema
- `seed.sql` - Sample data (optional)

## Deployment Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Nginx (for serving frontend)
- Process manager (systemd, supervisor, etc.)

### Backend Setup

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. Initialize database:
   ```bash
   psql -U postgres -f schema.sql
   ```

4. Start backend:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Configure nginx to serve frontend files:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       root /path/to/production/frontend/dist;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. Restart nginx:
   ```bash
   sudo systemctl restart nginx
   ```

### Security Considerations

- Use strong, unique passwords
- Configure HTTPS with SSL certificates
- Set up firewall rules
- Enable database backups
- Configure log rotation
- Use environment variables for sensitive data

### Monitoring

- Monitor application logs
- Set up error tracking
- Monitor database performance
- Set up uptime monitoring
- Configure alerting

## Support

For issues and questions, refer to the main project documentation.
EOF

echo "✅ Production build complete!"
echo "📁 Production files: production/"
echo ""
echo "📝 Next steps:"
echo "1. Review production/README.md for deployment instructions"
echo "2. Configure production environment variables"
echo "3. Deploy to your production server"
