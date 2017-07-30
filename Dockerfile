FROM alpine:3.5

RUN apk --no-cache add nginx
RUN mkdir /run/nginx

RUN sed -i -e 's!return 404;!root /var/www/html;!' \
  /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
