FROM node:18.17-alpine

RUN mkdir /app
COPY . /app



RUN addgroup -S mercari && adduser -S trainee -G mercari

RUN chown -R trainee:mercari /app

# USER trainee


WORKDIR /app
RUN npm ci

CMD ["npm", "start"]
