FROM node:18.6.0 as build
COPY ./distiller /distiller
ARG VITE_API_URL
RUN cd /distiller && yarn && VITE_API_URL=$VITE_API_URL yarn build

FROM nginx
COPY --from=build /distiller/build/ /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf