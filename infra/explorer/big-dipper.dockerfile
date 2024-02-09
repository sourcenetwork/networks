FROM node:18-alpine3.18 as builder

RUN npm i -g turbo
COPY big-dipper-2.0-cosmos /app
RUN cd /app/apps/web-sourcehub && yarn install && yarn run build

WORKDIR /app/apps/web-sourcehub

EXPOSE 3000

CMD ["yarn", "run", "next", "start"]
