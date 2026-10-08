FROM node:24.14.0-bookworm-slim@sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8 AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN test "$(node --version)" = v24.14.0 && test "$(npm --version)" = 11.9.0 && npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.30.5-alpine@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/cognitive-graph.conf
USER 101:101
EXPOSE 8080
STOPSIGNAL SIGQUIT
# Substitute only our marker; Nginx's $host/$uri variables must remain intact.
ENTRYPOINT ["/bin/sh", "-ec"]
CMD ["budget=0; for value in \"${CG_RUN_ACTIVE_TIMEOUT_SECONDS:-1800}\" \"${CG_TOOL_WAIT_TIMEOUT_SECONDS:-1800}\" \"${CG_LLM_TIMEOUT_SECONDS:-300}\"; do case $value in ''|*[!0-9]*) echo 'Invalid configured timeout' >&2; exit 2;; esac; test \"$value\" -gt 0; if test \"$value\" -gt \"$budget\"; then budget=$value; fi; done; timeout=$(expr \"$budget\" + 60); test \"$timeout\" -gt \"$budget\"; sed \"s/__CG_PROXY_TIMEOUT_SECONDS__/${timeout}/g\" /etc/nginx/cognitive-graph.conf > /tmp/nginx.conf; exec nginx -c /tmp/nginx.conf -g 'daemon off;' "]
