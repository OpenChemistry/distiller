FROM node:16.6.1 as build
COPY ./distiller /distiller
ARG REACT_APP_API_URL
RUN cd /distiller && yarn && REACT_APP_API_URL=$REACT_APP_API_URL yarn build

FROM nginx
COPY --from=build /distiller/build/ /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf