FROM ubuntu:20.04

WORKDIR /root

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update
RUN apt install -y git npm python3 python3-pip
RUN git clone https://github.com/YuhangQ/JLU-UIMS-WEB

EXPOSE 80

CMD node /root/JLU-UIMS-WEB/main.js