FROM lab/base:fc28

RUN /root/basic-setup.sh && /root/container-setup.sh

STOPSIGNAL 37
EXPOSE 22
CMD ["/bin/bash","/root/do-init.sh","--unit","container.target"]
