# smtc_analytics_queuemanage_xeon_gst

FROM smtc_analytics_common_xeon_gst
ENV DEBIAN_FRONTEND=noninteractive

RUN  apt-get update -qq && apt-get install -qq python3-paho-mqtt python3-ply python3-requests python3-watchdog python3-munkres python3-scipy python3-shapely python3-memory-profiler && rm -rf /var/lib/apt/lists/*

COPY --from=aividtech/smtc_common /home/*.py /home/
COPY *.py /home/
COPY models /home/models
COPY Xeon/gst/pipeline /home/pipelines/queuemanage
COPY custom_transforms /home/custom_transforms
COPY botconfig /home/botconfig
CMD ["/home/detect-object.py"]
ENV PATH=${PATH}:/home/custom_transforms

####
ARG  UID
USER ${UID}
####
