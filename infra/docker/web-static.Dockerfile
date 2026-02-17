FROM node:20-alpine AS build

WORKDIR /workspace/apps/web
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

COPY apps/web ./
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY infra/nginx/web-spa.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html
EXPOSE 80
