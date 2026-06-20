# DevGuard AI frontend image.
# Stage 1: build the static SPA with Vite. The API base URL is baked in at build
# time (Vite inlines VITE_* vars), so it points at the published backend host port.
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Overridable at build time via compose build args.
ARG VITE_API_BASE_URL=http://localhost:8009/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: serve the static build with nginx.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
