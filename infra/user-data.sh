#!/bin/bash
# EC2 최초 부팅 시 1회 실행된다 (cloud-init). 실행 로그: /var/log/cloud-init-output.log
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y nginx

# 인스턴스 메타데이터 (IMDSv2). 실패해도 부팅을 막지 않는다.
imds() {
  local token
  token=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null) || return 0
  curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/meta-data/$1" 2>/dev/null || true
}

AZ=$(imds placement/availability-zone)
PRIVATE_IP=$(imds local-ipv4)

# 기본 사이트를 교체한다. /health 는 파일이 아닌 고정 응답으로 처리해
# 디스크 상태와 무관하게 항상 같은 본문(200 "OK")을 반환하도록 한다.
cat > /etc/nginx/sites-available/default <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;
    root /var/www/html;
    index index.html;

    location = /health {
        access_log off;
        default_type text/plain;
        return 200 "OK\n";
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX

cat > /var/www/html/index.html <<HTML
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Codyssey B6-1</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 4rem auto; max-width: 34rem; color: #232f3e; }
    h1 { font-size: 1.4rem; }
    dt { font-weight: 600; margin-top: .6rem; }
    code { background: #f2f4f7; padding: .1rem .3rem; border-radius: .2rem; }
  </style>
</head>
<body>
  <h1>Hello Cloud — Codyssey B6-1</h1>
  <p>VPC 퍼블릭 서브넷의 EC2에서 Nginx가 응답하고 있습니다.</p>
  <dl>
    <dt>Availability Zone</dt><dd>${AZ:-unknown}</dd>
    <dt>Private IPv4</dt><dd>${PRIVATE_IP:-unknown}</dd>
    <dt>Health check</dt><dd><code>GET /health</code> → <code>200 OK</code></dd>
  </dl>
</body>
</html>
HTML

nginx -t
systemctl enable --now nginx
systemctl reload nginx
