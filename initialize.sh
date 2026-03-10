#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# Inputs / layout
# -------------------------------------------------------------------
FILE="/var/tmp/aether-ansible/ansible/ansible_config_vars.yml"
SANDBOX_ROOT="/home/dt_training/dtu_sandbox_logs"

FILES_DIR="${SANDBOX_ROOT}/files"
MANIFEST_KUBE="${FILES_DIR}/kube-settings/manifest.yaml"
MANIFEST_ONEAGENT="${FILES_DIR}/oneagent-features/manifest.yaml"
MANIFEST_LOGS="${FILES_DIR}/logs-settings/manifest.yaml"

LOG_GEN_DIR="${SANDBOX_ROOT}/log-generator"
LOG_GEN_YAML="${LOG_GEN_DIR}/logGen.yaml"

TOKEN_ENV_FILE="${SANDBOX_ROOT}/generated_token.env"

OTEL_DEMO_URL="https://raw.githubusercontent.com/open-telemetry/opentelemetry-demo/59c9b2ca32be41e464fedc1eed6dcf4ad1503c3d/kubernetes/opentelemetry-demo.yaml"

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 127; }
}

mask() {
  local s="${1:-}"
  if [[ ${#s} -ge 12 ]]; then
    printf '%s…%s' "${s:0:6}" "${s: -4}"
  else
    printf '<redacted>'
  fi
}

load_vars_from_yaml() {
  local f="${1:?vars file required}"
  [[ -f "$f" ]] || { echo "Vars file not found: $f" >&2; exit 1; }

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue

    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*:[[:space:]]*(.*)[[:space:]]*$ ]]; then
      key="${BASH_REMATCH[1]}"
      val="${BASH_REMATCH[2]}"

      val="${val#"${val%%[![:space:]]*}"}"
      val="${val%"${val##*[![:space:]]}"}"

      if [[ "$val" =~ ^\"(.*)\"$ ]]; then
        val="${BASH_REMATCH[1]}"
      elif [[ "$val" =~ ^\'(.*)\'$ ]]; then
        val="${BASH_REMATCH[1]}"
      fi

      printf -v "$key" '%s' "$val"
      export "$key"
    fi
  done < "$f"
}

create_dt_token_settings_rw() {
  : "${dynatrace_environment_url:?Missing dynatrace_environment_url}"
  : "${dynatrace_environment_access_token:?Missing dynatrace_environment_access_token}"
  require_cmd jq
  require_cmd curl

  local name="${1:-custom_api_token}"
  local expiration="${2:-now+14d}"

  response="$(curl -sS -X POST \
    "${dynatrace_environment_url}/api/v2/apiTokens" \
    -H "Authorization: Api-Token ${dynatrace_environment_access_token}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"${name}\",
      \"expirationDate\": \"${expiration}\",
      \"scopes\": [\"settings.write\", \"settings.read\"]
    }"
  )"

  dt_token_id="$(echo "$response" | jq -r '.id')"
  dttoken="$(echo "$response" | jq -r '.token')"
  dt_token_expiration="$(echo "$response" | jq -r '.expirationDate')"

  : "${dt_token_id:?Missing token id}"
  : "${dttoken:?Missing token value}"
  : "${dt_token_expiration:?Missing expiration}"

  export dt_token_id dttoken dt_token_expiration
}

write_token_env() {
  local out="${1:?output file required}"

  umask 077
  : > "$out"

  {
    echo "DT_API_TOKEN_ID=${dt_token_id}"
    echo "DT_API_TOKEN=${dttoken}"
    echo "DT_API_TOKEN_EXPIRATION=${dt_token_expiration}"
  } >> "$out"

  chmod 600 "$out"
  echo "Wrote token env file: $out"
}

restart_k3s() {
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl restart k3s
  else
    sudo service k3s restart
  fi
}

# -------------------------------------------------------------------
# Preflight
# -------------------------------------------------------------------
require_cmd sed
require_cmd kubectl
require_cmd docker

# -------------------------------------------------------------------
# Execution
# -------------------------------------------------------------------
load_vars_from_yaml "$FILE"

: "${instance_user:?Missing instance_user}"
: "${dynatrace_environment_url:?Missing dynatrace_environment_url}"
: "${dynatrace_environment_access_token:?Missing dynatrace_environment_access_token}"

create_dt_token_settings_rw "custom_api_token"
#sleep 300

echo "${dttoken}" >> "/home/${instance_user}/customtoken.txt"
export dttoken

write_token_env "$TOKEN_ENV_FILE"

tenantUUID="$(kubectl get dynakube -n dynatrace -o jsonpath='{.items[0].status.activeGate.connectionInfoStatus.tenantUUID}')"
tenantFull="https://${tenantUUID}.live.dynatrace.com"
export tenantUUID tenantFull

sed -i "s,TENANTURL_TOREPLACE,${tenantUUID},g" \
  "$MANIFEST_KUBE" "$MANIFEST_ONEAGENT" "$MANIFEST_LOGS"

curl -L \
  https://github.com/Dynatrace/dynatrace-configuration-as-code/releases/latest/download/monaco-linux-amd64 \
  -o "/home/${instance_user}/monaco"
chmod +x "/home/${instance_user}/monaco"

/home/${instance_user}/monaco deploy "$MANIFEST_KUBE"
/home/${instance_user}/monaco deploy "$MANIFEST_ONEAGENT"
/home/${instance_user}/monaco deploy "$MANIFEST_LOGS"

sleep 30
restart_k3s
sleep 300

kubectl get namespace otel-demo >/dev/null 2>&1 || kubectl create namespace otel-demo
kubectl apply -n otel-demo -f "$OTEL_DEMO_URL"

docker build -t log-generator "$LOG_GEN_DIR"
sleep 30
docker save log-generator:latest | sudo k3s ctr images import -
sleep 10
kubectl apply -n otel-demo -f "$LOG_GEN_YAML"

echo "✅ Sandbox provisioning complete"