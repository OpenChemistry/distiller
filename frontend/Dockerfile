FROM node:18.6.0 as build

WORKDIR /distiller

COPY ./distiller/package.json ./
COPY ./distiller/package-lock.json ./
RUN yarn

COPY ./distiller .
ARG REACT_APP_API_URL
ARG REACT_APP_SENTRY_DSN_URL
RUN REACT_APP_API_URL=$REACT_APP_API_URL REACT_APP_SENTRY_DSN_URL=$REACT_APP_SENTRY_DSN_URL yarn build

FROM nginx
COPY --from=build /distiller/build/ /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf