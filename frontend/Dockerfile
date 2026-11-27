FROM node:20 AS build

WORKDIR /app

RUN useradd -m -d /app -s /bin/sh appuser && chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser package*.json ./

RUN npm ci

COPY --chown=appuser:appuser . .

RUN npm run build

FROM nginx:alpine



COPY --from=build /app/dist /usr/share/nginx/html


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]