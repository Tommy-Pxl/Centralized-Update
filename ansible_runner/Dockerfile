FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt update && \
    apt install -y tzdata ansible python3 python3-pip ssh && \
    ln -fs /usr/share/zoneinfo/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

WORKDIR /ansible
CMD ["sleep", "infinity"]
