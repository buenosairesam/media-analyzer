Real-Time Video Analysis Platform

Project Overview
A scalable real-time video streaming and AI analysis platform 
that demonstrates modern cloud-native architecture and machine learning integration. 
The system ingests RTMP video streams (from sources like OBS), 
processes them with computer vision AI models, 
and provides live analysis results through a responsive web dashboard.

Core Functionality

Video Ingestion: Accept RTMP streams and convert to HLS for web playback
AI Processing: Real-time object detection (YOLO) and scene analysis (CLIP) on video segments
Live Dashboard: Angular frontend with WebSocket-powered real-time analysis overlays
Scalable Architecture: Kubernetes-deployed microservices with configurable processing modes
Cloud Integration: GCP services integration while maintaining platform agnostic design

Technical Stack

Backend: Django + Django Channels, PostgreSQL, Redis, Celery
AI/ML: OpenCV, YOLO, CLIP, Whisper (Hugging Face Transformers)
Frontend: Angular 17+ with HLS.js video player and Canvas overlays
Infrastructure: Docker containers, Kubernetes, NGINX
Cloud: Google Cloud Platform integration (Storage, Vision API, Build, Logging)
Streaming: FFmpeg for RTMP→HLS conversion, WebSocket for real-time data

Key Features

Dual processing modes (real-time vs batch) with runtime switching
Live video analysis overlays (bounding boxes, object labels, confidence scores)
OBS Studio integration for testing with various video sources
Kubernetes auto-scaling based on processing queue depth
Performance monitoring and benchmarking for 1080p30 video streams
Platform-agnostic design with cloud-specific optimizations

Architecture Goals

Demonstrate event-driven microservices architecture
Showcase AI model deployment and inference at scale
Implement real-time data streaming and WebSocket communication
Show proficiency with modern web frameworks and container orchestration
Prove understanding of video processing pipelines and streaming protocols

This project serves as a technical showcase for backend development, AI/ML integration, cloud platform expertise, and modern web application architecture - directly addressing the requirements for a streaming media and AI-focused development role.



Master Implementation Checklist
Core Infrastructure Setup

 Django project structure - Create apps: streaming, ai_processing, api, dashboard
 Database models - Stream, MediaSegment, VideoAnalysis, ObjectDetection tables
 Docker containers - Django app, PostgreSQL, Redis, Nginx
 Basic Kubernetes manifests - Deployments, services, configmaps, PVCs
 RTMP ingestion endpoint - Accept OBS streams, trigger ffmpeg HLS conversion
 HLS segment monitoring - File watcher to detect new video segments

AI Processing Pipeline

 Video analysis models setup - CLIP for scene understanding, YOLO for object detection
 Frame extraction service - Extract keyframes from HLS segments
 Real-time vs batch processing abstraction - Strategy pattern implementation
 AI processing worker - Celery tasks for video analysis
 Results storage - Store detection results with timestamps and confidence scores
 Processing queue management - Handle backlog and prioritization

Real-Time Video Effects Pipeline

 GPU-accelerated shader pipeline - OpenGL/CUDA integration with FFmpeg
 AI-triggered effects system - Apply shaders based on detection results
 Custom filter development - Face blur, object highlighting, scene-based color grading
 WebGL frontend effects - Client-side shader preview and control

Angular Frontend

 Angular 17+ project setup - Standalone components, signals, new control flow
 WebSocket service - Real-time communication with Django Channels
 Video player component - HLS.js integration for stream playback
 Analysis overlay component - Canvas-based bounding boxes and labels
 Stream control dashboard - Start/stop streams, processing mode toggle
 Real-time results panel - Live object detection and scene analysis display

Real-time Communication

 Django Channels setup - WebSocket consumers for live data streaming
 WebSocket message protocols - Define message types for analysis results
 Frontend WebSocket integration - Angular service for real-time updates
 Overlay synchronization - Match analysis results with video timeline

GCP Integration Features

 Cloud Storage integration - Store processed video segments and analysis results
 Cloud Vision API comparison - Benchmark against local models (within free tier)
 Cloud Logging - Structured logging for monitoring and debugging
 Cloud Build CI/CD - Automated Docker builds and deployments
 GKE-specific configurations - Node selectors, resource requests/limits
 Cloud Load Balancer - External access to the application

Video Processing & Effects

 FFmpeg integration - HLS generation with proper segment duration
 Video quality optimization - Handle 1080p streams efficiently
 Frame rate analysis - Detect motion and activity levels
 Color analysis - Dominant colors and scene brightness
 Performance monitoring - Track processing latency and throughput

Kubernetes Production Setup

 Resource management - CPU/memory limits for AI processing
 Auto-scaling configuration - HPA based on processing queue length
 Persistent storage - Claims for video segments and database
 Service mesh setup - Istio for traffic management (optional)
 Monitoring stack - Prometheus and Grafana integration
 Ingress configuration - NGINX ingress with SSL termination

Testing & Validation

 OBS integration testing - Verify RTMP stream ingestion
 AI model accuracy testing - Validate object detection results
 Performance benchmarking - Process 1080p30 streams in real-time
 WebSocket stress testing - Multiple concurrent viewers
 End-to-end pipeline testing - OBS → Processing → Angular display

Documentation & Deployment

 API documentation - OpenAPI/Swagger specs
 Kubernetes deployment guide - Step-by-step cluster setup
 GCP setup instructions - Service account, IAM, and resource creation
 Architecture diagrams - System overview and data flow
 Performance metrics documentation - Benchmarks and optimization notes



Suggested Implementation Order:
Phase 1 (Foundation): Infrastructure Setup → Django + Models → Docker Setup
Phase 2 (Core Features): RTMP Ingestion → AI Processing Pipeline → Results Storage
Phase 3 (Frontend): Angular Setup → WebSocket Service → Video Player
Phase 4 (Integration): Real-time Communication → Analysis Overlays → Stream Control
Phase 5 (Cloud): GCP Services → Kubernetes Production → Monitoring
Phase 6 (Polish): Testing → Documentation → Performance Optimization
This order ensures each component builds on the previous ones and you can test functionality incrementally. The GCP integration is spread throughout to demonstrate platform knowledge without being overwhelming.
Ready to start with the foundation phase?



Media Analyzer - Complete Project Structure
media-analyzer/
├── README.md
├── docker-compose.yml              # Development environment
├── requirements.txt                # Python dependencies
├── manage.py                      # Django management
│
├── backend/                       # Django application root
│   ├── media_analyzer/           # Main Django project
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base settings
│   │   │   ├── development.py    # Dev overrides
│   │   │   └── production.py     # Prod overrides
│   │   ├── urls.py               # Main URL routing
│   │   ├── wsgi.py              # WSGI application
│   │   └── asgi.py              # ASGI for Django Channels
│   │
│   ├── streaming/                # RTMP/HLS handling app
│   │   ├── __init__.py
│   │   ├── models.py            # Stream, MediaSegment models
│   │   ├── views.py             # RTMP endpoints
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── rtmp_handler.py      # RTMP server logic
│   │   ├── hls_monitor.py       # File system watcher
│   │   └── urls.py
│   │
│   ├── ai_processing/            # AI analysis app
│   │   ├── __init__.py
│   │   ├── models.py            # Analysis results models
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Processing strategy interface
│   │   │   ├── realtime.py      # Real-time processor
│   │   │   ├── batch.py         # Batch processor
│   │   │   └── video_analyzer.py # CLIP/YOLO integration
│   │   ├── tasks.py             # Celery tasks
│   │   └── apps.py              # App configuration
│   │
│   ├── effects/                  # Real-time video effects app
│   │   ├── __init__.py
│   │   ├── models.py            # Effect presets, shader configs
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── gpu_pipeline.py  # OpenGL/CUDA processing
│   │   │   ├── ffmpeg_filters.py # FFmpeg custom filters
│   │   │   └── effect_engine.py  # Main effects orchestrator
│   │   ├── shaders/             # GLSL shader files
│   │   │   ├── vertex/          # Vertex shaders
│   │   │   ├── fragment/        # Fragment shaders
│   │   │   ├── blur.glsl       # Face blur shader
│   │   │   ├── highlight.glsl   # Object highlight shader
│   │   │   └── color_grade.glsl # Scene-based color grading
│   │   ├── triggers/
│   │   │   ├── __init__.py
│   │   │   ├── ai_triggers.py   # AI detection → effect mapping
│   │   │   └── manual_triggers.py # User-controlled effects
│   │   ├── tasks.py             # GPU processing Celery tasks
│   │   └── apps.py
│   │
│   └── api/                     # REST API app
│       ├── __init__.py
│       ├── serializers.py       # DRF serializers
│       ├── views.py            # API endpoints
│       └── urls.py
│
├── frontend/                    # Angular application
│   ├── package.json
│   ├── angular.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts
│   │   │   ├── app.config.ts    # Angular 17+ config
│   │   │   │
│   │   │   ├── components/
│   │   │   │   ├── stream-viewer/
│   │   │   │   │   ├── stream-viewer.component.ts
│   │   │   │   │   ├── stream-viewer.component.html
│   │   │   │   │   └── stream-viewer.component.scss
│   │   │   │   ├── analysis-panel/
│   │   │   │   │   └── analysis-panel.component.ts
│   │   │   │   ├── stream-control/
│   │   │   │   │   └── stream-control.component.ts
│   │   │   │   └── effects-panel/
│   │   │   │       ├── effects-panel.component.ts
│   │   │   │       ├── effects-panel.component.html
│   │   │   │       └── shader-editor.component.ts
│   │   │   │
│   │   │   ├── services/
│   │   │   │   ├── websocket.service.ts
│   │   │   │   ├── stream.service.ts
│   │   │   │   ├── analysis.service.ts
│   │   │   │   └── effects.service.ts
│   │   │   │
│   │   │   ├── webgl/            # Client-side effects engine
│   │   │   │   ├── shader.service.ts
│   │   │   │   ├── effects-engine.ts
│   │   │   │   ├── webgl-utils.ts
│   │   │   │   └── shaders/      # WebGL shaders
│   │   │   │       ├── overlay.vert.glsl
│   │   │   │       ├── overlay.frag.glsl
│   │   │   │       ├── particle.vert.glsl
│   │   │   │       └── particle.frag.glsl
│   │   │   │
│   │   │   └── models/
│   │   │       ├── stream.interface.ts
│   │   │       ├── analysis.interface.ts
│   │   │       └── effects.interface.ts
│   │   │
│   │   └── main.ts              # Angular bootstrap
│   └── ...
│
├── docker/                     # Docker configurations
│   ├── Dockerfile.django       # Django app container
│   ├── Dockerfile.nginx        # Nginx for HLS serving
│   └── docker-compose.override.yml
│
├── k8s/                        # Kubernetes manifests
│   ├── base/                   # Base configurations
│   │   ├── namespace.yaml
│   │   ├── django-deployment.yaml
│   │   ├── nginx-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── services.yaml
│   │   └── configmaps.yaml
│   │
│   ├── overlays/              # Environment-specific
│   │   ├── development/
│   │   │   └── kustomization.yaml
│   │   └── production/
│   │       ├── kustomization.yaml
│   │       └── gcp-specific.yaml
│   │
│   └── scripts/
│       ├── deploy.sh
│       └── setup-cluster.sh
│
├── media/                     # Media storage (mounted volume)
│   ├── segments/             # HLS video segments
│   ├── playlists/           # HLS playlists
│   └── uploads/             # Uploaded content
│
├── scripts/                  # Helper scripts
│   ├── setup-dev.sh         # Development environment setup
│   ├── start-rtmp-server.sh # RTMP server startup
│   └── load-ai-models.py    # Download and setup AI models
│
└── docs/                    # Documentation
    ├── api.md              # API documentation
    ├── deployment.md       # Deployment guide
    └── architecture.md     # System architecture





vertical separation instead of phases

Slice 1: Basic Stream Ingestion

RTMP endpoint (basic)
HLS conversion (minimal)
Stream model + API
Simple Angular video player
Basic K8s deployment

Slice 2: AI Processing Foundation

Video segment detection
Single AI model integration (YOLO)
Processing strategy abstraction
Results storage + API
Analysis display component

Slice 3: Real-time Communication

WebSocket setup
Live analysis streaming
Frontend overlay system
Processing queue monitoring

Slice 4: GCP Integration

Cloud Storage for segments
GKE deployment
Monitoring integration




considerations for deployment / testing

does this planning take into consideration running it on a local kubernetes cluster? I use kind and tilt for running tough a prefer not to depend on it for developing just test the orchestration?

The current planning assumes traditional development (Django dev server + Angular dev server) with K8s only for testing orchestration. This is actually perfect for your workflow! Let me clarify the development vs testing approach:

## **Development Mode (Local Servers)**
```bash
# Backend development
cd backend
python manage.py runserver 8000

# Frontend development  
cd frontend
ng serve --port 4200

# Supporting services (via Docker Compose)
docker-compose up redis postgres
```

**Benefits:**
- Hot reload for both Django and Angular
- Easy debugging with IDE integration
- Fast iteration cycles
- No K8s complexity during development

## **Testing Mode (KIND + K8s)**
```bash
# Build and deploy to KIND cluster
kind create cluster --name media-analyzer
kubectl apply -k k8s/overlays/development
```

**For orchestration testing only:**
- Container builds and registry
- Service discovery and networking
- Volume mounts and persistence
- Resource limits and scaling
- Inter-service communication

## **Suggested Development Workflow**## **Key Points for Your Workflow:**

### **Development (95% of time):**
- **No K8s dependency** - just Docker Compose for supporting services
- **Fast hot reload** - Django and Angular dev servers
- **Easy debugging** - direct access to logs and debugger
- **Simple database migrations** and model changes

### **K8s Testing (when needed):**
- **Container builds** work correctly
- **Service networking** functions properly  
- **Volume mounts** for media files
- **Resource limits** don't break anything
- **Horizontal scaling** works as expected

### **Perfect for KIND:**
- KIND cluster only created when testing orchestration
- No overhead during daily development
- Easy to tear down and recreate
- Matches production K8s behavior

### **Tilt Usage (Optional):**
- **If you use Tilt**: Only for K8s testing, not development
- **If you skip Tilt**: Use the simple `kubectl` commands for testing

This approach gives you:
- **Fast development** without K8s complexity
- **Realistic testing** of the actual deployment
- **No vendor lock-in** to Tilt (though it's great if you want it)
- **Easy CI/CD** since K8s manifests are tested locally

The planning already supports this perfectly - you develop fast locally and test orchestration when needed!


CURRENT STEP 

now that I have a basic stream pipeline a need to add an AI feature (something simple) before stepping everything to something that scales. I was thinking on detecting my extend hand, but maybe some more bussines oriented feature would work better (read the very first message with the JD in spanish to think about this)

Edit
Looking back at the job description, they mention analyzing "millones de emisiones en medios y redes sociales" for communication and advertising optimization. For a business-oriented AI feature that aligns with Seenka's focus, I'd suggest:

🎯 Brand/Logo Detection
Business Value: Identify brands and logos in video streams (like TV broadcasts, social media content)

Detect when competitors appear in content
Monitor brand visibility and placement
Track advertising effectiveness
Technical Implementation:

Use CLIP for general brand recognition
Train on common logos/brand imagery
Output: Brand name, confidence, screen position, duration
📺 Content Classification
Business Value: Categorize video content for media monitoring

Detect content types: "news", "sports", "entertainment", "advertising"
Identify show segments vs commercial breaks
Monitor content themes and topics
Technical Implementation:

CLIP scene classification with predefined categories
Frame sampling every few seconds
Output: Content category, confidence, timestamp
🗣️ Speaker Detection
Business Value: Media monitoring and audience analysis

Count people on screen (audience size estimation)
Detect when someone is speaking/presenting
Monitor speaker time and engagement
Technical Implementation:

YOLO for person detection
Basic pose estimation to detect "presentation pose"
Output: Person count, speaking activity, screen position
My Recommendation: Content Classification
Why it's perfect for your demo:

Business relevant: Directly matches Seenka's media analysis focus
Technically achievable: CLIP can classify scenes out-of-the-box
Visually impressive: Live categorization overlay on your OBS stream
Extensible: Easy to add more categories or confidence thresholds
Demo scenario: Stream different content types with OBS (news clips, sports, entertainment) and watch the AI classify them in real-time.

Which direction appeals to you most? The hand detection is cool for personal interaction, but content classification would really showcase understanding of their business domain.




Im using streams of myself (I have a decent setup) so for now the input will be just that but I think i can be fun if I display logos with my phone or something like that

Edit
Perfect! Logo detection with your phone is brilliant - it's both business-relevant (brand monitoring) and interactive demo-friendly. You can hold up logos on your phone screen or physical items and watch the AI detect them in real-time.

🏷️ Logo Detection Implementation
Simple Approach (Weekend-friendly):
CLIP-based Brand Recognition:

python
# Use CLIP's zero-shot classification
brands = ["Apple", "Google", "Nike", "Coca-Cola", "McDonald's", "Amazon"]
# Hold up logos on phone/laptop and classify scenes
Demo Flow:

You stream yourself with OBS
Hold up different brand logos on your phone/laptop screen
AI detects and labels them with confidence scores
Live overlay shows: "Apple Logo detected (87% confidence)"
Enhanced Approach:
Combine YOLO + CLIP:

YOLO: Detect objects in scene (phone, laptop, clothing, etc.)
CLIP: Classify detected regions for brand/logo content
Output: "iPhone detected", "Nike logo on shirt", "Starbucks cup visible"
Fun Demo Scenarios:
Tech Logos: Show Apple, Google, Microsoft logos on your devices
Fashion Brands: Wear branded clothing/accessories
Food/Drink: Hold up branded items from your desk
Mixed Reality: Point phone camera at branded items around your room
Business Value Demo:
Brand Monitoring: "Track when competitors appear in streams"
Advertising Analysis: "Measure brand visibility duration and positioning"
Content Compliance: "Detect unauthorized brand usage"
Implementation in Your Matrix:
This fits perfectly in AI Analysis → Local Single Server:

 Frame extraction from HLS ✓
 CLIP logo classification (instead of YOLO objects)
 Analysis results storage
 Results API endpoint
Want to start with basic CLIP brand classification, or go straight for the object detection + brand recognition combo?