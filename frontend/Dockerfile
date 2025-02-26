FROM node:18.6.0 as build

WORKDIR /distiller
COPY ./distiller/package.json ./distiller/yarn.lock ./
RUN yarn install
COPY ./distiller .
ARG VITE_API_URL
RUN VITE_API_URL=$VITE_API_URL yarn build

FROM nginx
COPY --from=build /distiller/dist/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf