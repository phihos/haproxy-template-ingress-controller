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
Merge template libraries based on enabled flags
Returns merged config with libraries applied in order: base -> ingress -> gateway -> haproxytech -> values.yaml
*/}}
{{- define "haproxy-template-ic.mergeLibraries" -}}
{{- $merged := dict }}
{{- $context := . }}

{{- /* Load base library if enabled */ -}}
{{- if $context.Values.controller.templateLibraries.base.enabled }}
  {{- $baseLibrary := $context.Files.Get "libraries/base.yaml" | fromYaml }}
  {{- $merged = merge $merged $baseLibrary }}
{{- end }}

{{- /* Load ingress library if enabled */ -}}
{{- if $context.Values.controller.templateLibraries.ingress.enabled }}
  {{- $ingressLibrary := $context.Files.Get "libraries/ingress.yaml" | fromYaml }}
  {{- $merged = merge $merged $ingressLibrary }}
{{- end }}

{{- /* Load gateway library if enabled */ -}}
{{- if $context.Values.controller.templateLibraries.gateway.enabled }}
  {{- $gatewayLibrary := $context.Files.Get "libraries/gateway.yaml" | fromYaml }}
  {{- $merged = merge $merged $gatewayLibrary }}
{{- end }}

{{- /* Load haproxytech library if enabled */ -}}
{{- if $context.Values.controller.templateLibraries.haproxytech.enabled }}
  {{- $haproxytechLibrary := $context.Files.Get "libraries/haproxytech.yaml" | fromYaml }}
  {{- $merged = merge $merged $haproxytechLibrary }}
{{- end }}

{{- /* Merge user-provided config from values.yaml (highest priority) */ -}}
{{- $userConfig := dict }}
{{- if $context.Values.controller.config.templateSnippets }}
  {{- $_ := set $userConfig "templateSnippets" $context.Values.controller.config.templateSnippets }}
{{- end }}
{{- if $context.Values.controller.config.maps }}
  {{- $_ := set $userConfig "maps" $context.Values.controller.config.maps }}
{{- end }}
{{- if $context.Values.controller.config.files }}
  {{- $_ := set $userConfig "files" $context.Values.controller.config.files }}
{{- end }}
{{- if $context.Values.controller.config.haproxyConfig }}
  {{- $_ := set $userConfig "haproxyConfig" $context.Values.controller.config.haproxyConfig }}
{{- end }}
{{- if $context.Values.controller.config.validationTests }}
  {{- $_ := set $userConfig "validationTests" $context.Values.controller.config.validationTests }}
{{- end }}

{{- /* Merge user config last so it overrides libraries */ -}}
{{- $merged = merge $merged $userConfig }}

{{- /* Return merged config as YAML */ -}}
{{- $merged | toYaml }}
{{- end }}
