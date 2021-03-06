include(platform.m4)
include(../../../script/loop.m4)
include(../../../maintenance/db-init/sensor-info.m4)

looplist(SCENARIO_NAME,defn(`SCENARIOS'),`
loop(OFFICEIDX,1,defn(`NOFFICES'),`
include(office.m4)
ifelse(len(defn(`OFFICE_LOCATION')),0,,`

apiVersion: v1
kind: Service
metadata:
  name: defn(`OFFICE_NAME')-mqtt-service
  labels:
    app: defn(`OFFICE_NAME')-mqtt
spec:
#  clusterIP: 10.108.227.47
#  externalTrafficPolicy: Cluster
#  ports:
#  - nodePort: 32581
#    port: 1883
#    protocol: TCP
#    targetPort: 1833
#  selector:
#    app: defn(`OFFICE_NAME')-mqtt
#  sessionAffinity: None
#  type: NodePort
spec:
  ports:
  #- nodePort:32581
  - port: 1883
    protocol: TCP
    targetPort: 1883
    nodePort: 32571
  selector:
    app: defn(`OFFICE_NAME')-mqtt
  type: NodePort
---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: defn(`OFFICE_NAME')-mqtt
  labels:
     app: defn(`OFFICE_NAME')-mqtt
spec:
  replicas: 1
  selector:
    matchLabels:
      app: defn(`OFFICE_NAME')-mqtt
  template:
    metadata:
      labels:
        app: defn(`OFFICE_NAME')-mqtt
    spec:
      enableServiceLinks: false
      containers:
        - name: defn(`OFFICE_NAME')-mqtt
          image: eclipse-mosquitto:1.5.8
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 1883
          env:
            - name: NO_PROXY
              value: "*"
            - name: no_proxy
              value: "*"
          volumeMounts:
            - mountPath: /etc/localtime
              name: timezone
              readOnly: true
          securityContext:
            runAsUser: 1883
      volumes:
          - name: timezone
            hostPath:
                path: /etc/localtime
                type: File
PLATFORM_NODE_SELECTOR(`Xeon')dnl

---
')')')
