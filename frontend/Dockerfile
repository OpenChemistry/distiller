FROM node:22.15.0 AS build
COPY ./distiller /distiller
ARG VITE_API_URL
RUN cd /distiller && yarn && VITE_API_URL=$VITE_API_URL yarn build

FROM nginx
COPY --from=build /distiller/dist/ /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf