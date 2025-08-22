


              +-------+
              |  OBS  |   RTMP stream
              +---+---+ --------------+
                  |                    |
                  v                    |
            +-----+------+             |
            | nginx-rtmp |-- HLS ───+  |
            | (RTMP/HLS) |          |  |
            +-----+------+          |  |
                  |                 |  |
           HLS on /media             |  |
                  |                 |  |
                  v                 |  |
       +----------+-----------+     |  |
       |   Host “media/” dir  |<----+  |
       +----------+-----------+        |
                  | File watcher        |
                  v                     |
       +----------+-----------+        |
       |   Django Backend     |        |
       | (REST + ASGI + WS)   +<--WebSocket--+  
       +---+------------------+             |
           |   |                          |
           |   +-------+  HTTP/API        |
           |           v                   |
           |   +-------+------+            |
           |   | PostgreSQL   |            |
           |   +-------+------+            |
           |                              |
           |      Celery tasks            |
           v                              |
    +------+--------+    queue    +------+--------+
    | celery-logo   |<-----------| celery-default |
    +---------------+            +---------------+
           |                            ^
           |                            |
           +----> Redis (broker) <------+
     
     Frontend:
                +-----------+
                | Angular   |
                |  (4200)   |
                +-----+-----+
                      |
                      | HTTP/API (/api/…)
                      |
                +-----v-----+
                |  Nginx    |
                |  (SSP)    |
                +-----------+

Legend:

• OBS pushes RTMP into nginx-rtmp, which writes HLS (.m3u8/.ts) into the shared media/ folder.
• Django’s file-watcher polls media/ for new segments and enqueues Celery tasks.
• Django Backend serves REST API, WebSockets (via Channels → Redis), and hosts analysis logic.
• Celery Workers consume tasks from Redis:
  – celery-logo for logo detection
  – celery-default (or others) for visual analysis, etc.
• PostgreSQL holds application & analysis metadata.
• Angular (dev or static via Nginx) calls the Django API and listens on WebSockets.
• Nginx (frontend) proxies /api and /ws to Django and serves the Angular SPA.

This layout keeps streaming, AI-processing, data storage, and UI layers cleanly separated.




codex
Below is an updated architecture sketch—with the local webcam path and AI execution‐strategy layer added. Each box is a service or component, and arrows show the main flows:

                            +--------+
                            |  OBS   |   RTMP stream
                            +---+----+ --------+
                                |               |
                                v               |
                        +-------+------+        |
                        |  nginx-rtmp  |-- HLS →|   (writes .m3u8/.ts to host media/)
                        | (RTMP/HLS)   |        |
                        +-------+------+        |
                                |               |
                   +------------+---------------+-------------+
                   |                   HLS                       |
                   v                                            |
            +------+-------+                                    |
            | Host “media/”|<-----------------------------------+
            |   directory  |    (mount in backend & nginx-rtmp)  
            +------+-------+
                   |
                   | (poll .ts files)
                   v
            +------+-------+
            | File Watcher | → enqueues Celery tasks
            +------+-------+
                   |
                   v
            +------+-------+
            | Django       |  REST API & WebSocket (ASGI)
            |  Backend     |
            | - RTMP/Webcam|
            |   Adapters   |
            +------+-------+
                   |            +--------------------------------+
                   | WebSocket  |                                |
                   +---------->+  Frontend Nginx (SPA + proxy)  |
                   |           |  – Serves Angular app on 80    |
                   |           |  – Proxies /api → Django       |
                   v           |  – Proxies /ws  → Django       |
            +------+-------+   |  – Proxies /streaming → nginx-rtmp
            | PostgreSQL   |   +--------------------------------+
            +------+-------+
                   |
                   v
            +------+-------+            +------------------------+
            |   Redis      |<-----------+ Celery Workers         |
            | (broker)     |  tasks     | – Worker queues:       |
            +------+-------+            |   logo_detection,     |
                   |                    |   visual_analysis,    |
                   |                    |   default…            |
                   +------------------→ | – Uses AnalysisEngine  |
                                        |   with Execution       |
                                        |   Strategies:          |
                                        |   • local (in-worker)  |
                                        |   • remote LAN (via    |
                                        |     worker_host)       |
                                        |   • cloud (via API)    |
                                        +------------------------+
            +--------+
            | Webcam | local device          
            +---+----+                  
                |                      
                | via Django’s Webcam  
                |SourceAdapter (ffmpeg) 
                v                      
         [ Django Backend ]             
                |                      
                v                      
            +------+-------+            
            | Host “media/”|            
            +--------------+            

Key points:

 • OBS → nginx-rtmp → host “media/” → Django file-watcher → Celery tasks
 • Local Webcam → Django backend (WebcamSourceAdapter with ffmpeg) → host “media/” → same pipeline
 • Django Backend (REST + ASGI/WebSocket) ↔ Angular (served by Frontend Nginx)
 • Celery Workers pick up tasks from Redis, run AnalysisEngine → can execute locally, offload to remote LAN workers, or call cloud APIs
 • PostgreSQL stores streams, queue, and analysis results

This should give a clear bird’s-eye of how data and control flow through your streaming+AI stack.
