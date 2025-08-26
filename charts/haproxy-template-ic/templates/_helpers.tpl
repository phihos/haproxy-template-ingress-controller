{{/*
Expand the name of the chart.
*/}}
{{- define "haproxy-template-ic.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "haproxy-template-ic.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "haproxy-template-ic.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "haproxy-template-ic.labels" -}}
helm.sh/chart: {{ include "haproxy-template-ic.chart" . }}
{{ include "haproxy-template-ic.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "haproxy-template-ic.selectorLabels" -}}
app.kubernetes.io/name: {{ include "haproxy-template-ic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "haproxy-template-ic.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "haproxy-template-ic.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Shared HAProxy scripts - used by both production and validation
*/}}
{{- define "haproxy-template-ic.haproxy-scripts" -}}
docker-entrypoint.sh: |
  #!/bin/sh
  set -e

  echo "Starting HAProxy entrypoint script..."

  # Copy default configuration to runtime location
  cp /usr/local/etc/haproxy-default/haproxy.cfg /etc/haproxy/haproxy.cfg
  echo "Configuration copied to /etc/haproxy/haproxy.cfg"

  # Ensure required directories exist with correct permissions
  mkdir -p /etc/haproxy /etc/haproxy/maps /etc/haproxy/certs /etc/haproxy/errors
  chown -R haproxy:haproxy /etc/haproxy

  # Check if we should start HAProxy or pass through other commands
  if [ "$1" = "haproxy" ] || [ $# -eq 0 ]; then
      echo "Starting HAProxy in master-worker mode..."
      # Start HAProxy in master-worker mode with management socket
      exec haproxy -W -db -S "/etc/haproxy/haproxy-master.sock,level,admin" -- /etc/haproxy/haproxy.cfg
  else
      echo "Executing: $@"
      exec "$@"
  fi
haproxy-socket-reload.sh: |
  #!/usr/bin/env bash
  echo reload | nc local:/etc/haproxy/haproxy-master.sock
dataplane-entrypoint.sh: |
  #!/bin/sh
  set -e

  echo "Starting Dataplane API entrypoint script..."

  # Copy default configuration to runtime location
  cp /usr/local/etc/dataplane-default/dataplaneapi.yaml /etc/haproxy/dataplaneapi.yaml
  echo "Configuration copied to /etc/haproxy/dataplaneapi.yaml"

  # Ensure required directories exist with correct permissions
  mkdir -p /etc/haproxy/maps /etc/haproxy/certs /etc/haproxy/errors /etc/haproxy/ssl /etc/haproxy/general /etc/haproxy/spoe
  mkdir -p /var/lib/dataplaneapi/transactions /var/lib/dataplaneapi/backups
  chown -R haproxy:haproxy /etc/haproxy /var/lib/dataplaneapi

  # Start Dataplane API
  echo "Starting HAProxy Dataplane API..."
  exec dataplaneapi
{{- end }}

{{/*
HAProxy configuration template - parameterized for production/validation
*/}}
{{- define "haproxy-template-ic.haproxy-config" -}}
global
    stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin

userlist dataplaneapi
    user {{ .Values.dataplaneConfig.username }} insecure-password {{ .password }}

defaults
    mode http
    timeout connect 1s
    timeout client 1s
    timeout server 1s

frontend status
    bind *:{{ .healthPort }}
    http-request return status 200 content-type text/plain string "OK" if { path /healthz }
{{- end }}

{{/*
Dataplane API configuration template - parameterized for production/validation
*/}}
{{- define "haproxy-template-ic.dataplane-config" -}}
config_version: 2
name: haproxy-dataplaneapi
dataplaneapi:
  host: 0.0.0.0
  port: {{ .Values.dataplaneConfig.port }}
  user:
    - name: {{ .Values.dataplaneConfig.username | quote }}
      password: {{ .password | quote }}
      insecure: true
  transaction:
    transaction_dir: /var/lib/dataplaneapi/transactions
    backups_number: 10
    backups_dir: /var/lib/dataplaneapi/backups
  resources:
    maps_dir: /etc/haproxy/maps
    ssl_certs_dir: /etc/haproxy/ssl
    general_storage_dir: /etc/haproxy/general
    spoe_dir: /etc/haproxy/spoe
haproxy:
  config_file: /etc/haproxy/haproxy.cfg
  haproxy_bin: /usr/local/sbin/haproxy
  reload:
    reload_delay: 1
    reload_cmd: /etc/haproxy/haproxy-socket-reload.sh
    restart_cmd: /etc/haproxy/haproxy-socket-reload.sh
    reload_strategy: custom
log_targets:
  - log_to: stdout
    log_level: info
{{- end }}

{{/*
Unified dataplane container specification - used by both production and validation
Parameters: .environment ("production" or "validation"), .context (root context)
*/}}
{{- define "haproxy-template-ic.dataplane-container" -}}
- name: {{ .environment }}-dataplane
  image: "{{ .context.Values.haproxyImage.repository }}:{{ .context.Values.haproxyImage.tag }}"
  imagePullPolicy: {{ .context.Values.haproxyImage.pullPolicy }}
  command: ["/usr/local/bin/dataplane-entrypoint.sh"]
  ports:
    - name: {{ .environment }}-api
      containerPort: {{ .context.Values.dataplaneConfig.port }}
      protocol: TCP
  env:
    - name: HAPROXY_USERNAME
      value: {{ .context.Values.dataplaneConfig.username | quote }}
    - name: HAPROXY_PASSWORD
      value: {{ index .context.Values.dataplaneConfig.passwords .environment | quote }}
  volumeMounts:
    - name: {{ .environment }}-config
      mountPath: /etc/haproxy
    - name: {{ .environment }}-dataplane-config
      mountPath: /usr/local/bin/dataplane-entrypoint.sh
      subPath: dataplane-entrypoint.sh
    - name: {{ .environment }}-dataplane-config
      mountPath: /usr/local/etc/dataplane-default/dataplaneapi.yaml
      subPath: dataplaneapi-default.yaml
      readOnly: true
    - name: {{ .environment }}-dataplane-config
      mountPath: /etc/haproxy/haproxy-socket-reload.sh
      subPath: haproxy-socket-reload.sh
      readOnly: true
  livenessProbe:
    httpGet:
      path: /v3/info
      port: {{ .context.Values.dataplaneConfig.port }}
      httpHeaders:
        - name: Authorization
          value: "Basic {{ printf "%s:%s" .context.Values.dataplaneConfig.username (index .context.Values.dataplaneConfig.passwords .environment) | b64enc }}"
    initialDelaySeconds: 15
    periodSeconds: 10
{{- end }}

{{/*
Generate CA bundle for webhook (placeholder for self-signed certificates)
*/}}
{{- define "haproxy-template-ic.webhook.caBundle" -}}
{{- if eq .Values.webhook.tls.certProvider "self-signed" }}
{{/* Placeholder CA bundle - actual certificate generated by webhook-cert-job */}}
{{- printf "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t" | b64enc }}
{{- else }}
{{- printf "" }}
{{- end }}
{{- end }}
