# smtc_analytics_heatmap_xeon_gst

FROM smtc_analytics_common_xeon_gst

RUN  apt-get update -qq && apt-get install -qq python3-paho-mqtt python3-ply python3-requests python3-munkres python3-shapely python3-watchdog python3-scipy && rm -rf /var/lib/apt/lists/*

COPY --from=aividtech/smtc_common /home/*.py /home/
COPY *.py /home/
COPY models /home/models
#COPY gallery /home/gallery
COPY Xeon/gst/pipeline /home/pipelines/heatmap
COPY custom_transforms /home/custom_transforms
#VOLUME /home/gallery
CMD ["/home/detect-object.py"]
ENV  PATH=${PATH}:/home/custom_transforms


####
ARG  UID
USER ${UID}
####
