FROM ubuntu:22.04

# Prevent timezone prompt
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system packages (including tzdata FIRST)
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

# Work directory
WORKDIR /ansible

# Copy playbooks + runner
COPY playbook_scan.yml .
COPY playbook_update.yml .
COPY runner.py .

# inventory.ini is mounted at runtime
CMD [ "sleep", "infinity" ]
