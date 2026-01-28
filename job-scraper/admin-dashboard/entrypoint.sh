#!/bin/sh

# Create a JS file that sets window.env variables based on Docker environment
cat <<EOF > /usr/share/nginx/html/env-config.js
window.env = {
  SUPABASE_URL: "${SUPABASE_URL}",
  SUPABASE_KEY: "${SUPABASE_KEY}"
};
EOF
