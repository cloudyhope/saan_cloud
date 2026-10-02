FROM node:14-bullseye AS build-stage
LABEL author="CB-DevOps"
WORKDIR /app
COPY package.json package-lock.json ./
ENV NODE_OPTIONS=--max-old-space-size=1536
RUN npm ci --legacy-peer-deps --no-audit --no-fund
COPY . .
# The public API address is baked into the bundle at build time (it overrides .env.production).
ARG VUE_APP_SAAN_APP_PATH
ENV VUE_APP_SAAN_APP_PATH=${VUE_APP_SAAN_APP_PATH}
ARG VUE_APP_CAR_PIECE_PATH
ENV VUE_APP_CAR_PIECE_PATH=${VUE_APP_CAR_PIECE_PATH:-${VUE_APP_SAAN_APP_PATH}}
RUN npm run build-production

FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
