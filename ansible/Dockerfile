FROM ubuntu:22.04

RUN apt update && apt install -y \
    ansible \
    python3 \
    python3-pip \
    ssh \
    curl \
    apt-utils \
    man-db \
    apt-transport-https \
    software-properties-common

# Reduce warnings
ENV DEBIAN_FRONTEND=noninteractive

# Work directory
WORKDIR /ansible

# Copy playbooks + runner
COPY playbook_scan.yml .
COPY playbook_update.yml .
COPY runner.py .

# inventory.ini is mounted at runtime (don't copy)

CMD [ "sleep", "infinity" ]
