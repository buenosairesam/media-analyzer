# Multi-stage build for Angular application
# Stage 1: Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files first (for better Docker layer caching)
COPY package*.json ./

# Install ALL dependencies (including devDependencies for building)
RUN npm ci --silent

# Copy source code
COPY . .

# Build the application for production
RUN npm run build

# Stage 2: Production stage with NGINX
FROM nginx:alpine as production

# Copy built Angular app from build stage (Angular 17+ builds to browser subfolder)
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Copy custom nginx configuration for Angular SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development stage with NGINX (for unified approach)
FROM nginx:alpine as development

# Install Node.js for building
RUN apk add --no-cache nodejs npm

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Build for development (with source maps)
RUN npm run build

# Copy built app to nginx html directory (Angular 17+ builds to browser subfolder)
RUN cp -r /app/dist/frontend/browser/* /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]