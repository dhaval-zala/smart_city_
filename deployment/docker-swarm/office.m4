define(`OFFICE_NAME',defn(`SCENARIO_NAME')`_office'defn(`OFFICEIDX'))dnl
define(`OFFICE_LOCATION',ifelse(index(defn(`SCENARIO'),defn(`SCENARIO_NAME')),-1,,`defn(defn(`SCENARIO_NAME')`_office'defn(`OFFICEIDX')_location)'))dnl
define(`CAMERA_RTSP_PORT',17000)dnl
define(`CAMERA_RTP_PORT',27000)dnl
define(`CAMERA_PORT_STEP',10)dnl
define(`DISCOVER_IP_CAMERA',`true')dnl
define(`DISCOVER_SIMULATED_CAMERA',`true')dnl
define(`WEBRTC_UDP_PORT',10000)dnl
define(`WEBRTC_STREAMING_LIMIT',10)dnl
define(`OT_TYPE',`false')dnl

