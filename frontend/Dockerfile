FROM node:16.6.1 as build
COPY ./still /still
ARG REACT_APP_API_URL
RUN cd /still && yarn && REACT_APP_API_URL=$REACT_APP_API_URL yarn build

FROM nginx
COPY --from=build /still/build/ /usr/share/nginx/html
