FROM local_mkt/kvm_simx:fc28

# Get the built simx from the simx builder container
COPY --from=local_mkt/kvm_simx:fc28 /opt/simx /opt/simx

RUN /root/basic-setup.sh && /root/kvm-setup.sh
