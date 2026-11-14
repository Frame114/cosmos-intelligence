FROM node:22.22.2-alpine3.23 AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY index.html ./
COPY vite.config.ts tsconfig.json ./
COPY src ./src
RUN npm run build

FROM nginx:stable-alpine3.24-slim
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
USER nginx
