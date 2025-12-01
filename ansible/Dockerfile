FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt update && \
    apt install -y tzdata && \
    ln -fs /usr/share/zoneinfo/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt install -y \
        ansible \
        python3 \
        python3-pip \
        ssh \
        curl \
        apt-utils \
        man-db \
        apt-transport-https \
        software-properties-common

WORKDIR /ansible

COPY playbook_scan.yml .
COPY playbook_update.yml .
COPY runner.py .

CMD [ "sleep", "infinity" ]
