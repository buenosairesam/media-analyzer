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

# Copy built Angular app from build stage
COPY --from=build /app/dist/frontend /usr/share/nginx/html

# Copy custom nginx configuration for Angular SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Stage 3: Development stage (for docker-compose)
FROM node:18-alpine as development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY . .

# Expose port for dev server
EXPOSE 4200

# Start development server with hot reload
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--poll", "2000"]