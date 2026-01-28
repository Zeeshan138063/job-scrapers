FROM nginx:alpine

# Copy static assets
COPY index.html /usr/share/nginx/html/index.html

# Copy entrypoint script
COPY entrypoint.sh /docker-entrypoint.d/99-env-config.sh
RUN chmod +x /docker-entrypoint.d/99-env-config.sh

EXPOSE 80
