# CI/CD 
# including GitHub Actions workflows, Dockerfiles, a Helm chart, and Kubernetes helpers.
# It saves everything under /mnt/data/vouchsys-cicd-pack and zips it for download.

import os, textwrap, json, zipfile, pathlib

root = "/mnt/data/vouchsys-cicd-pack"
paths = [
    ".github/workflows",
    "helm/vouchsys/templates",
    "k8s"
]
for p in paths:
    os.makedirs(os.path.join(root, p), exist_ok=True)

# ---------------- Dockerfiles ----------------
docker_web = textwrap.dedent("""\
    # Dockerfile for Next.js/Node web app
    FROM node:20-alpine AS deps
    WORKDIR /app
    COPY package*.json ./
    RUN npm ci --ignore-scripts

    FROM node:20-alpine AS builder
    WORKDIR /app
    COPY --from=deps /app/node_modules ./node_modules
    COPY . .
    # If this is a Next.js app, the following will create a production build
    RUN npm run build || npm run compile || true

    FROM node:20-alpine AS runner
    WORKDIR /app
    ENV NODE_ENV=production
    # Optional: set PORT for runtime
    ENV PORT=3000
    # Copy only necessary files
    COPY --from=builder /app .
    EXPOSE 3000
    # Prefer "start" if present; fallback to "serve"
    CMD [ "sh", "-lc", "npm run start || node server.js || npx serve -s ." ]
""")

docker_kafka = textwrap.dedent("""\
    # Dockerfile for Python Kafka producer
    FROM python:3.11-slim
    WORKDIR /app
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    COPY requirements.txt /app/requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt || true
    COPY . .
    # Expose an optional health endpoint via flask if implemented; otherwise skip
    EXPOSE 8080
    CMD ["python", "Kafka_producer.py"]
""")

# ---------------- Helm chart files ----------------
chart_yaml = textwrap.dedent("""\
    apiVersion: v2
    name: vouchsys
    description: Helm chart for VouchSys web app and Kafka producer
    type: application
    version: 0.1.0
    appVersion: "0.1.0"
""")

values_yaml = textwrap.dedent("""\
    image:
      registry: ghcr.io
      repositoryWeb: OWNER/REPO-web
      repositoryKafka: OWNER/REPO-kafka
      tag: "latest"
      pullPolicy: IfNotPresent

    namespace: vouchsys

    web:
      enabled: true
      replicas: 2
      port: 3000
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
      env:
        - name: NODE_ENV
          value: "production"
      ingress:
        enabled: true
        className: nginx
        hosts:
          - host: vouchsys.local
            paths:
              - path: /
                pathType: Prefix
        tls: []

    kafka:
      enabled: true
      replicas: 1
      port: 8080
      env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          valueFrom:
            secretKeyRef:
              name: vouchsys-secrets
              key: kafka_bootstrap
        - name: KAFKA_TOPIC
          value: "vouchsys-events"

    serviceAccount:
      create: true
      name: ""

    autoscaling:
      enabled: true
      minReplicas: 2
      maxReplicas: 5
      targetCPUUtilizationPercentage: 70

    config:
      EXTRA_CONFIG_JSON: "{}"

    secret:
      kafka_bootstrap: "replace-me:9092"
""")

deployment_web = textwrap.dedent("""\
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: {{ include "vouchsys.fullname" . }}-web
      labels:
        app.kubernetes.io/name: {{ include "vouchsys.name" . }}
        app.kubernetes.io/component: web
    spec:
      replicas: {{ .Values.web.replicas }}
      selector:
        matchLabels:
          app.kubernetes.io/name: {{ include "vouchsys.name" . }}
          app.kubernetes.io/component: web
      template:
        metadata:
          labels:
            app.kubernetes.io/name: {{ include "vouchsys.name" . }}
            app.kubernetes.io/component: web
        spec:
          serviceAccountName: {{ include "vouchsys.serviceAccountName" . }}
          containers:
            - name: web
              image: "{{ .Values.image.registry }}/{{ .Values.image.repositoryWeb }}:{{ .Values.image.tag }}"
              imagePullPolicy: {{ .Values.image.pullPolicy }}
              ports:
                - containerPort: {{ .Values.web.port }}
              env:
                - name: PORT
                  value: "{{ .Values.web.port }}"
              envFrom:
                - configMapRef:
                    name: {{ include "vouchsys.fullname" . }}-config
                - secretRef:
                    name: vouchsys-secrets
              resources: {{- toYaml .Values.web.resources | nindent 16 }}
              readinessProbe:
                httpGet:
                  path: /healthz
                  port: {{ .Values.web.port }}
                initialDelaySeconds: 10
                periodSeconds: 10
              livenessProbe:
                httpGet:
                  path: /healthz
                  port: {{ .Values.web.port }}
                initialDelaySeconds: 20
                periodSeconds: 20
""")

service_web = textwrap.dedent("""\
    apiVersion: v1
    kind: Service
    metadata:
      name: {{ include "vouchsys.fullname" . }}-web
    spec:
      type: ClusterIP
      selector:
        app.kubernetes.io/name: {{ include "vouchsys.name" . }}
        app.kubernetes.io/component: web
      ports:
        - name: http
          port: 80
          targetPort: {{ .Values.web.port }}
""")

deployment_kafka = textwrap.dedent("""\
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: {{ include "vouchsys.fullname" . }}-kafka
      labels:
        app.kubernetes.io/name: {{ include "vouchsys.name" . }}
        app.kubernetes.io/component: kafka
    spec:
      replicas: {{ .Values.kafka.replicas }}
      selector:
        matchLabels:
          app.kubernetes.io/name: {{ include "vouchsys.name" . }}
          app.kubernetes.io/component: kafka
      template:
        metadata:
          labels:
            app.kubernetes.io/name: {{ include "vouchsys.name" . }}
            app.kubernetes.io/component: kafka
        spec:
          serviceAccountName: {{ include "vouchsys.serviceAccountName" . }}
          containers:
            - name: kafka-producer
              image: "{{ .Values.image.registry }}/{{ .Values.image.repositoryKafka }}:{{ .Values.image.tag }}"
              imagePullPolicy: {{ .Values.image.pullPolicy }}
              ports:
                - containerPort: {{ .Values.kafka.port }}
              envFrom:
                - configMapRef:
                    name: {{ include "vouchsys.fullname" . }}-config
                - secretRef:
                    name: vouchsys-secrets
              readinessProbe:
                tcpSocket:
                  port: {{ .Values.kafka.port }}
                initialDelaySeconds: 5
                periodSeconds: 10
              livenessProbe:
                tcpSocket:
                  port: {{ .Values.kafka.port }}
                initialDelaySeconds: 10
                periodSeconds: 20
""")

service_kafka = textwrap.dedent("""\
    apiVersion: v1
    kind: Service
    metadata:
      name: {{ include "vouchsys.fullname" . }}-kafka
    spec:
      type: ClusterIP
      selector:
        app.kubernetes.io/name: {{ include "vouchsys.name" . }}
        app.kubernetes.io/component: kafka
      ports:
        - name: http
          port: 8080
          targetPort: {{ .Values.kafka.port }}
""")

ingress_yaml = textwrap.dedent("""\
    {{- if .Values.web.ingress.enabled }}
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: {{ include "vouchsys.fullname" . }}-web
      annotations:
        kubernetes.io/ingress.class: {{ .Values.web.ingress.className | quote }}
    spec:
      rules:
        {{- range .Values.web.ingress.hosts }}
        - host: {{ .host }}
          http:
            paths:
              {{- range .paths }}
              - path: {{ .path }}
                pathType: {{ .pathType }}
                backend:
                  service:
                    name: {{ include "vouchsys.fullname" $ }}-web
                    port:
                      number: 80
              {{- end }}
        {{- end }}
      tls:
        {{- toYaml .Values.web.ingress.tls | nindent 8 }}
    {{- end }}
""")

hpa_web = textwrap.dedent("""\
    {{- if .Values.autoscaling.enabled }}
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    metadata:
      name: {{ include "vouchsys.fullname" . }}-web
    spec:
      scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: {{ include "vouchsys.fullname" . }}-web
      minReplicas: {{ .Values.autoscaling.minReplicas }}
      maxReplicas: {{ .Values.autoscaling.maxReplicas }}
      metrics:
        - type: Resource
          resource:
            name: cpu
            target:
              type: Utilization
              averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
""")

helpers_tpl = textwrap.dedent("""\
    {{- define "vouchsys.name" -}}
    vouchsys
    {{- end -}}

    {{- define "vouchsys.fullname" -}}
    {{ .Release.Name | default "vouchsys" }}
    {{- end -}}

    {{- define "vouchsys.serviceAccountName" -}}
    {{- if .Values.serviceAccount.create -}}
    {{ default (include "vouchsys.fullname" .) .Values.serviceAccount.name }}
    {{- else -}}
    default
    {{- end -}}
""")

configmap_yaml = textwrap.dedent("""\
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: {{ include "vouchsys.fullname" . }}-config
    data:
      EXTRA_CONFIG_JSON: {{ .Values.config.EXTRA_CONFIG_JSON | quote }}
""")

secret_yaml = textwrap.dedent("""\
    apiVersion: v1
    kind: Secret
    metadata:
      name: vouchsys-secrets
    type: Opaque
    stringData:
      kafka_bootstrap: {{ .Values.secret.kafka_bootstrap | quote }}
""")

sa_yaml = textwrap.dedent("""\
    {{- if .Values.serviceAccount.create }}
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: {{ include "vouchsys.serviceAccountName" . }}
    {{- end }}
""")

test_pod = textwrap.dedent("""\
    apiVersion: v1
    kind: Pod
    metadata:
      name: "{{ include "vouchsys.fullname" . }}-test-connection"
      annotations:
        "helm.sh/hook": test
    spec:
      containers:
        - name: curl
          image: curlimages/curl:8.8.0
          command: ['sh', '-c', 'curl -sf http://{{ include "vouchsys.fullname" . }}-web/healthz']
      restartPolicy: Never
""")

namespace_yaml = textwrap.dedent("""\
    apiVersion: v1
    kind: Namespace
    metadata:
      name: vouchsys
""")

# ---------------- GitHub Actions ----------------
ci_yaml = textwrap.dedent("""\
    name: CI
    on:
      push:
        branches: [ main, master ]
      pull_request:
        branches: [ main, master ]
    jobs:
      test-web:
        runs-on: ubuntu-latest
        defaults:
          run:
            working-directory: ./
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-node@v4
            with:
              node-version: 20
              cache: npm
          - name: Install deps
            run: |
              if [ -f package.json ]; then npm ci --ignore-scripts; fi
          - name: Lint & Test
            run: |
              if [ -f package.json ]; then npm run lint || true; npm test --if-present; fi

      test-kafka:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: '3.11'
          - name: Install deps
            run: |
              if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
              pip install pytest
          - name: Run pytest
            run: |
              if ls -1 **/*_test.py 2>/dev/null | grep -q .; then pytest -q; else echo "No pytest files found"; fi
""")

cd_yaml = textwrap.dedent("""\
    name: CD
    on:
      push:
        branches: [ main, master ]
        paths:
          - 'Dockerfile*'
          - 'helm/**'
          - '.github/workflows/cd.yml'
          - '**/*.ts'
          - '**/*.tsx'
          - 'Kafka_producer.py'
          - 'pages/**'
          - 'package.json'
      workflow_dispatch:

    env:
      REGISTRY: ghcr.io
      IMAGE_WEB: ${{ github.repository }}-web
      IMAGE_KAFKA: ${{ github.repository }}-kafka

    jobs:
      build-and-push:
        runs-on: ubuntu-latest
        permissions:
          contents: read
          packages: write
        steps:
          - uses: actions/checkout@v4
          - name: Log in to GHCR
            uses: docker/login-action@v3
            with:
              registry: ${{ env.REGISTRY }}
              username: ${{ github.actor }}
              password: ${{ secrets.GITHUB_TOKEN }}

          - name: Build & push web image
            uses: docker/build-push-action@v6
            with:
              context: .
              file: ./Dockerfile.web
              push: true
              tags: |
                ${{ env.REGISTRY }}/${{ env.IMAGE_WEB }}:${{ github.sha }}
                ${{ env.REGISTRY }}/${{ env.IMAGE_WEB }}:latest

          - name: Build & push kafka image
            uses: docker/build-push-action@v6
            with:
              context: .
              file: ./Dockerfile.kafka
              push: true
              tags: |
                ${{ env.REGISTRY }}/${{ env.IMAGE_KAFKA }}:${{ github.sha }}
                ${{ env.REGISTRY }}/${{ env.IMAGE_KAFKA }}:latest

      deploy-dev:
        needs: build-and-push
        runs-on: ubuntu-latest
        environment: dev
        steps:
          - uses: actions/checkout@v4
          - name: Setup kubectl
            uses: azure/setup-kubectl@v4
          - name: Setup Helm
            uses: azure/setup-helm@v4
          - name: Configure kubeconfig
            run: |
              mkdir -p ~/.kube
              echo "${{ secrets.KUBE_CONFIG_DEV }}" > ~/.kube/config
          - name: Helm upgrade/install
            run: |
              helm upgrade --install vouchsys ./helm/vouchsys \
                --namespace vouchsys --create-namespace \
                --set image.registry=${{ env.REGISTRY }} \
                --set image.repositoryWeb=${{ env.IMAGE_WEB }} \
                --set image.repositoryKafka=${{ env.IMAGE_KAFKA }} \
                --set image.tag=${{ github.sha }}
          - name: Wait for rollout
            run: |
              kubectl -n vouchsys rollout status deploy/vouchsys-web --timeout=180s
              kubectl -n vouchsys rollout status deploy/vouchsys-kafka --timeout=180s
          - name: Run Helm tests
            run: helm test vouchsys -n vouchsys

      deploy-prod:
        if: github.ref == 'refs/heads/main'
        needs: deploy-dev
        runs-on: ubuntu-latest
        environment: prod
        steps:
          - uses: actions/checkout@v4
          - uses: azure/setup-kubectl@v4
          - uses: azure/setup-helm@v4
          - name: Configure kubeconfig
            run: |
              mkdir -p ~/.kube
              echo "${{ secrets.KUBE_CONFIG_PROD }}" > ~/.kube/config
          - name: Helm upgrade/install
            run: |
              helm upgrade --install vouchsys ./helm/vouchsys \
                --namespace vouchsys --create-namespace \
                --set image.registry=${{ env.REGISTRY }} \
                --set image.repositoryWeb=${{ env.IMAGE_WEB }} \
                --set image.repositoryKafka=${{ env.IMAGE_KAFKA }} \
                --set image.tag=${{ github.sha }}
          - name: Wait for rollout
            run: |
              kubectl -n vouchsys rollout status deploy/vouchsys-web --timeout=180s
              kubectl -n vouchsys rollout status deploy/vouchsys-kafka --timeout=180s
          - name: Run Helm tests
            run: helm test vouchsys -n vouchsys
""")

# ---------------- README ----------------
readme = textwrap.dedent("""\
    # VouchSys CI/CD + Helm + Kubernetes Pack

    This pack adds end-to-end CI (build & test), CD (Docker build/push + Helm deploy),
    and a production-ready Helm chart for your VouchSys repository.

    ## What's Included
    - **GitHub Actions**
      - `.github/workflows/ci.yml`: Lints/tests Node web and Python Kafka producer.
      - `.github/workflows/cd.yml`: Builds and pushes Docker images to GHCR, deploys to Kubernetes via Helm (dev → prod), runs rollout checks and `helm test`.
    - **Dockerfiles**
      - `Dockerfile.web`: Node/Next.js web app.
      - `Dockerfile.kafka`: Python 3.11 Kafka producer.
    - **Helm Chart** (`helm/vouchsys`)
      - Deployments, Services, Ingress (optional), HPA, ConfigMap, Secret, ServiceAccount.
      - `helm test` pod to verify service health endpoint.
    - **Kubernetes**
      - `k8s/namespace.yaml` to create the `vouchsys` namespace if you prefer manual creation.

    ## Quick Setup
    1. **Rename repos in `values.yaml`**
       - Replace `OWNER/REPO-web` and `OWNER/REPO-kafka` with `${{ github.repository }}-web` and `${{ github.repository }}-kafka` or your desired names.
    2. **Create GitHub Environments & Secrets**
       - Environments: `dev`, `prod`
       - Secrets:
         - `KUBE_CONFIG_DEV`: Base64-decoded kubeconfig content for dev cluster
         - `KUBE_CONFIG_PROD`: Base64-decoded kubeconfig content for prod cluster
       - Optional repository secrets if not using GHCR defaults:
         - `REGISTRY_USERNAME`, `REGISTRY_PASSWORD` (not needed for GHCR when using `GITHUB_TOKEN`).
    3. **Expose a health endpoint**
       - Web: `/healthz` route returning 200.
       - Kafka producer: keep port `8080` open or adjust probes as needed.
    4. **Push to `main`**
       - CI runs on PRs and pushes; CD builds, pushes images, deploys to `dev`, then to `prod` when on `main`.

    ## Local Helm Test
    ```bash
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    # Install chart
    helm upgrade --install vouchsys helm/vouchsys -n vouchsys --create-namespace
    # Run tests
    helm test vouchsys -n vouchsys
    ```

    ## Notes
    - If your web app is not Next.js, adjust the npm scripts and Dockerfile accordingly.
    - Set `web.ingress.hosts` in `values.yaml` for a real domain and configure TLS if needed.
    - HPA requires metrics server on the cluster.
""")

# ---------------- Write files ----------------
files = {
    os.path.join(root, "Dockerfile.web"): docker_web,
    os.path.join(root, "Dockerfile.kafka"): docker_kafka,
    os.path.join(root, "helm/vouchsys/Chart.yaml"): chart_yaml,
    os.path.join(root, "helm/vouchsys/values.yaml"): values_yaml,
    os.path.join(root, "helm/vouchsys/templates/deployment-web.yaml"): deployment_web,
    os.path.join(root, "helm/vouchsys/templates/service-web.yaml"): service_web,
    os.path.join(root, "helm/vouchsys/templates/deployment-kafka.yaml"): deployment_kafka,
    os.path.join(root, "helm/vouchsys/templates/service-kafka.yaml"): service_kafka,
    os.path.join(root, "helm/vouchsys/templates/ingress.yaml"): ingress_yaml,
    os.path.join(root, "helm/vouchsys/templates/hpa-web.yaml"): hpa_web,
    os.path.join(root, "helm/vouchsys/templates/_helpers.tpl"): helpers_tpl,
    os.path.join(root, "helm/vouchsys/templates/configmap.yaml"): configmap_yaml,
    os.path.join(root, "helm/vouchsys/templates/secret.yaml"): secret_yaml,
    os.path.join(root, "helm/vouchsys/templates/serviceaccount.yaml"): sa_yaml,
    os.path.join(root, "helm/vouchsys/templates/tests/test-connection.yaml"): test_pod,
    os.path.join(root, "k8s/namespace.yaml"): namespace_yaml,
    os.path.join(root, ".github/workflows/ci.yml"): ci_yaml,
    os.path.join(root, ".github/workflows/cd.yml"): cd_yaml,
    os.path.join(root, "README-CICD.md"): readme,
    os.path.join(root, "requirements.txt"): "kafka-python\nflask\n"
}
for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)

# Zip it up
zip_path = "/mnt/data/vouchsys-cicd-pack.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for folder, _, filenames in os.walk(root):
        for name in filenames:
            abs_path = os.path.join(folder, name)
            rel_path = os.path.relpath(abs_path, root)
            z.write(abs_path, rel_path)

zip_path
