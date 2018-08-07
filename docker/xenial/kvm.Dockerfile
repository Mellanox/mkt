FROM lab/simx:xenial AS simx
FROM lab/base:xenial

# Get the built simx from the simx builder container
COPY --from=simx /opt/simx /opt/simx

RUN /root/basic-setup.sh && /root/kvm-setup.sh
