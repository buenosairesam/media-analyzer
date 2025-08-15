# Media Analyzer Project Setup Commands

# ===== PROJECT ROOT SETUP =====
mkdir media-analyzer
cd media-analyzer

# Create main directories
mkdir -p {docker,k8s/{base,overlays/{development,production}},media/{segments,playlists,uploads},scripts,docs}

# ===== DJANGO BACKEND SETUP =====
cd backend

# Create Django project
django-admin startproject media_analyzer .

# Create Django apps with proper structure
python manage.py startapp streaming
python manage.py startapp ai_processing  
python manage.py startapp effects
python manage.py startapp api

# Create settings directory structure
mkdir media_analyzer/settings
touch media_analyzer/settings/__init__.py
mv media_analyzer/settings.py media_analyzer/settings/base.py
touch media_analyzer/settings/{development.py,production.py}

# Create subdirectories for complex apps
mkdir -p ai_processing/processors
touch ai_processing/processors/{__init__.py,base.py,realtime.py,batch.py,video_analyzer.py}

mkdir -p effects/{processors,shaders/{vertex,fragment},triggers}
touch effects/processors/{__init__.py,gpu_pipeline.py,ffmpeg_filters.py,effect_engine.py}
touch effects/shaders/{blur.glsl,highlight.glsl,color_grade.glsl}
touch effects/triggers/{__init__.py,ai_triggers.py,manual_triggers.py}

# ===== ANGULAR FRONTEND SETUP =====
# Create Angular 17+ project (this creates the frontend directory)
ng new frontend --routing --style=scss --standalone --skip-git

# NOW enter the created Angular project directory
cd frontend

# Generate components (must be run inside Angular project)
ng generate component components/stream-viewer --standalone
ng generate component components/analysis-panel --standalone  
ng generate component components/stream-control --standalone
ng generate component components/effects-panel --standalone
ng generate component components/effects-panel/shader-editor --standalone

# Generate services (must be run inside Angular project)
ng generate service services/websocket
ng generate service services/stream
ng generate service services/analysis
ng generate service services/effects
ng generate service webgl/shader
ng generate service webgl/effects-engine

# Create interfaces (must be run inside Angular project)
ng generate interface models/stream
ng generate interface models/analysis
ng generate interface models/effects

# Create WebGL utilities directory (can use mkdir here)
mkdir -p src/app/webgl/shaders
touch src/app/webgl/{webgl-utils.ts,effects-engine.ts}
touch src/app/webgl/shaders/{overlay.vert.glsl,overlay.frag.glsl,particle.vert.glsl,particle.frag.glsl}

# ===== ADDITIONAL SETUP =====
cd ..

# Create Docker files
touch docker/{Dockerfile.django,Dockerfile.nginx,docker-compose.override.yml}
touch docker-compose.yml

# Create Kubernetes manifests
touch k8s/base/{namespace.yaml,django-deployment.yaml,nginx-deployment.yaml,postgres-statefulset.yaml,redis-deployment.yaml,services.yaml,configmaps.yaml}
touch k8s/overlays/development/kustomization.yaml
touch k8s/overlays/production/{kustomization.yaml,gcp-specific.yaml}

# Create scripts
touch scripts/{setup-dev.sh,start-rtmp-server.sh,load-ai-models.py}
chmod +x scripts/*.sh

# Create requirements and config files
touch {requirements.txt,README.md}

# ===== DJANGO ADDITIONAL SETUP =====
cd backend

# Create Django Channels routing
touch media_analyzer/routing.py

# Create consumers for WebSocket
touch streaming/consumers.py

# Create custom management commands
mkdir -p streaming/management/commands
touch streaming/management/__init__.py
touch streaming/management/commands/{__init__.py,start_rtmp_server.py}

mkdir -p ai_processing/management/commands  
touch ai_processing/management/__init__.py
touch ai_processing/management/commands/{__init__.py,load_models.py}

# Create Celery configuration
touch media_analyzer/celery.py

# ===== VERIFICATION COMMANDS =====
echo "=== DJANGO STRUCTURE VERIFICATION ==="
cd ../backend  # Go back to backend from frontend
find . -name "*.py" | head -20

echo "=== ANGULAR STRUCTURE VERIFICATION ==="
cd ../frontend  # Go to frontend from backend
find src/app -type f | head -20

echo "=== PROJECT ROOT VERIFICATION ==="
cd ..  # Go to project root
tree -I 'node_modules|__pycache__|*.pyc' -L 3