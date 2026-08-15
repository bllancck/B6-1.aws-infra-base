# AWS 기초 웹 인프라 구축

AWS에서 네트워크와 서버를 직접 구성하고, 보안과 사용자 권한을 설정해 외부에서 접속 가능한 웹 서비스를 구축하는 과제입니다. 인프라 구축부터 접속 검증, 문제 해결, 리소스 정리까지의 과정을 담았습니다.

---

## 아키텍처

![아키텍처 다이어그램](docs/architecture.png)

> 용어가 낯설다면 먼저 [AWS 기초 웹 인프라 학습 노트](docs/study-notes.md)를 읽고 아래 내용을 확인하세요.

서울 리전의 VPC 안에 퍼블릭 서브넷을 만들고, 그 안에 Nginx가 실행되는 EC2 인스턴스를 배치했습니다. 외부 요청은 다음 경로를 따라 웹 서버에 도달합니다.

`사용자 → Internet Gateway → Public Subnet → Security Group → EC2 → Nginx`

- **네트워크**: Internet Gateway와 Route Table을 연결해 VPC가 인터넷과 통신하도록 구성했습니다.
- **서버**: 퍼블릭 IP가 할당된 EC2에서 Nginx 웹 서버를 실행합니다.
- **보안**: Security Group으로 웹 접속은 허용하고 SSH 접속은 운영자 IP로 제한합니다.
- **권한**: IAM 사용자에게 인프라 구성에 필요한 권한만 부여합니다.

### 인프라 구축 흐름

1. **권한 준비**

   루트 계정 대신 실습에 필요한 권한만 가진 IAM 사용자를 사용합니다.

2. **네트워크 구성**

   VPC를 생성하고 그 안에 Public Subnet을 만듭니다.

3. **인터넷 연결과 접근 제어**

   Internet Gateway와 Route Table로 인터넷 경로를 만들고, Security Group으로 HTTP와 SSH의 접근 범위를 제한합니다.

4. **웹 서버 배포**

   Public Subnet에 EC2를 생성하고 `user-data`로 Nginx를 자동 설치합니다.

5. **동작 검증**

   SSH로 서버 내부 상태를 확인하고, Public IP와 `/health`를 이용해 외부 접속을 검증합니다.

6. **기록과 정리**

   문제와 해결 과정을 기록한 뒤, 과금 방지를 위해 생성한 리소스를 모두 삭제합니다.

## 구성 요약

| 항목 | 값 |
|------|-----|
| **리전 / AZ** | `ap-northeast-2` (서울) / `ap-northeast-2a` |
| **VPC** | `codyssey-vpc` — `10.0.0.0/16` |
| **서브넷** | `codyssey-public-subnet-a` — `10.0.1.0/24`, 퍼블릭 IPv4 자동 할당 ON |
| **인터넷 경로** | `codyssey-igw` + 라우트 `0.0.0.0/0 → IGW` |
| **인스턴스** | `t2.micro`, Ubuntu 24.04 LTS, EBS gp3 8 GiB (`DeleteOnTermination=true`) |
| **웹 서버** | Nginx 1.24.0 (`:80`) — `/` 정적 페이지, `/health` 고정 응답 |
| **보안 그룹** | `codyssey-web-sg` — 80 ← `0.0.0.0/0`, 22 ← 운영자 IP `/32` |
| **IAM** | `codyssey-infra` 사용자 — EC2/VPC 구성 권한만, `AdministratorAccess` 미부여 |
| **작업 환경** | WSL2 Ubuntu + AWS CLI v2 |
| **실습 일시** | 2026-08-10 23:05 구축 ~ 23:58 정리 완료 (KST) |

---

## 외부 접속 검증

**검증 방식: (B) 헬스체크 호출** — 응답 본문이 고정되어 있어 증빙이 명확하기 때문입니다. (A) 브라우저 접속도 함께 확인했습니다.

| 구분 | 내용 |
|------|------|
| 접속 주소 | `http://43.202.71.184/health` |
| 응답 | `200 OK`, 본문 `OK` |
| 함께 확인 | `http://43.202.71.184/` → `200`, 정적 페이지 표시 |

```console
$ curl -i http://43.202.71.184/health
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Content-Type: text/plain
Content-Length: 3

OK
```

![헬스체크 및 브라우저 접속 결과](docs/images/web-access.png)

### 요구사항 검증 결과

`scripts/verify.sh` 가 아래 항목(마지막 정리 항목 제외)을 한 번에 점검하고, PASS/FAIL 판정을 포함한 전체 출력을 [`docs/verification.log`](docs/verification.log) 에 남깁니다. 11개 항목 전부 통과했습니다.

| 구분 | 요구사항 | 검증 방법 |
|------|----------|-----------|
| 네트워크 | 라우트 `0.0.0.0/0 → IGW` 존재 | `describe-route-tables` 의 게이트웨이 ID 확인 |
| 네트워크 | 서브넷 퍼블릭 IPv4 자동 할당 | `describe-subnets` 의 `MapPublicIpOnLaunch` |
| 네트워크 | 인스턴스의 인터넷 아웃바운드 | 인스턴스 내부 `curl https://example.com` → 200 |
| 컴퓨트 | SSH 접속 가능 | `ssh -i ~/.ssh/codyssey-key.pem ubuntu@43.202.71.184` |
| 컴퓨트 | 웹 서버 실행 상태 | `systemctl is-active nginx` → `active` |
| 컴퓨트 | 로컬 루프백 응답 | 인스턴스 내부 `curl http://localhost` → 200 |
| 보안 | HTTP 80 은 전체 공개 | 보안 그룹 인바운드 규칙 판정 |
| 보안 | SSH 22 는 전체 공개 아님 | 보안 그룹 인바운드 규칙 판정 |
| 보안 | `0.0.0.0/0` 전체 포트 허용 규칙 없음 | 보안 그룹 인바운드 규칙 판정 |
| 외부 접속 | `GET /health` → 200 + 본문 `OK` | 로컬에서 `curl` |
| 운영 | 실습 리소스 정리 완료 | [정리 체크리스트](docs/cleanup-checklist.md) 의 항목별 조회 명령 |

---

## 보안 설계

### Security Group — 네트워크 계층 접근 제어

| 방향 | 포트 | 소스 / 대상 | 근거 |
|------|------|-------------|------|
| 인바운드 | 80/tcp | `0.0.0.0/0` | 웹 서비스는 누구나 접근해야 하므로 공개 |
| 인바운드 | 22/tcp | 운영자 공인 IP `/32` | 서버 전권을 갖는 포트. 공개하면 즉시 무차별 로그인 시도의 표적이 된다 |
| 아웃바운드 | 전체 | `0.0.0.0/0` | 패키지 설치·보안 업데이트에 필요. 기본값 유지 |

`0.0.0.0/0` 에 대한 전체 포트(`0-65535`) 허용 규칙은 만들지 않았습니다.
"잠깐 열고 나중에 닫자"가 그대로 남는 사고가 잦기 때문에, 이 규칙의 부재를 [`scripts/test-sg-rules.sh`](scripts/test-sg-rules.sh) 로 단위 테스트하고 `verify.sh` 가 매번 재확인합니다.

SSH 소스는 `provision.sh` 가 실행 시점의 공인 IP(`curl https://checkip.amazonaws.com`)를 자동으로 `/32` 로 넣습니다.
따라서 공인 IP 가 바뀌면 접속이 끊기는데, 이는 결함이 아니라 의도된 동작입니다. 실습 중 실제로 발생했고([트러블슈팅 Case 3](docs/troubleshooting.md)), 규칙을 넓히는 대신 아래 명령으로 소스를 갱신했습니다.

```bash
SG=$(aws ec2 describe-security-groups --filters Name=tag:Project,Values=codyssey-b6-1 \
       --query 'SecurityGroups[0].GroupId' --output text)
OLD=$(aws ec2 describe-security-groups --group-ids "$SG" \
       --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[].CidrIp" --output text)
aws ec2 revoke-security-group-ingress --group-id "$SG" --protocol tcp --port 22 --cidr "$OLD"
aws ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 22 \
  --cidr "$(curl -s https://checkip.amazonaws.com)/32"
```

### IAM — API 호출 권한 제어

콘솔·CLI 접근은 루트 계정이 아닌 `codyssey-infra` IAM 사용자로만 수행했고, 부여한 정책은 [`infra/iam-policy.json`](infra/iam-policy.json) 입니다.

| 설계 | 내용 |
|------|------|
| 서비스 범위 | EC2/VPC/보안 그룹 조작에 필요한 액션만 열거. S3·RDS 등 무관한 서비스 권한 없음 |
| 리전 제한 | `aws:RequestedRegion = ap-northeast-2` 조건으로 다른 리전 호출 차단 |
| 과금 가드레일 | `ec2:RunInstances` 를 `t2.micro` / `t3.micro` 외 타입에 대해 명시적 `Deny` |
| 정리 확인용 | `ce:GetCostAndUsage` 읽기 권한만 추가 |

액션을 손으로 열거하면 누락이 생깁니다. 실제로 `ec2:ModifySubnetAttribute` 가 빠져 프로비저닝이 중단됐고([트러블슈팅 Case 1](docs/troubleshooting.md)), 스크립트가 호출하는 API 목록을 뽑아 정책과 대조하는 절차를 도입했습니다.

```bash
grep -oh 'aws ec2 [a-z-]*' scripts/*.sh | sort -u
```

> [!NOTE]
> IAM 사용자로 Billing 대시보드를 열려면 루트 계정에서 **계정 설정 → IAM 사용자/역할의 결제 정보 액세스**를 한 번 활성화해야 합니다.

**Security Group 과 IAM 의 차이** — Security Group 은 *패킷* 을 통제하고(어떤 IP 가 어떤 포트로 들어올 수 있는지), IAM 은 *API 호출* 을 통제합니다(누가 어떤 리소스를 만들고 지울 수 있는지).
IAM 을 아무리 좁혀도 22 포트를 전체 공개하면 서버는 털리고, 반대로 보안 그룹을 완벽히 잠가도 IAM 이 열려 있으면 공격자가 규칙 자체를 바꿔버릴 수 있습니다. 두 계층은 서로를 대체하지 않습니다.

---

## 실행 방법

AWS CLI v2 와 `codyssey-infra` 사용자의 자격 증명(`aws configure`)이 필요합니다. 스크립트는 WSL/Linux 셸에서 실행합니다.

```bash
bash scripts/provision.sh      # VPC → 서브넷 → IGW → 라우트 → SG → 키페어 → EC2
sleep 90                       # user-data 의 Nginx 설치 완료 대기
bash scripts/verify.sh         # 요구사항 검증 + docs/verification.log 기록
bash scripts/cleanup.sh        # 실습 종료 후 생성 역순으로 삭제
```

모든 리소스에 `Project=codyssey-b6-1` 태그를 붙이고, `verify.sh` 와 `cleanup.sh` 는 이 태그로 대상을 찾습니다.
따라서 리소스 ID 를 손으로 옮겨 적을 필요가 없고, 정리 누락도 생기지 않습니다.

기본값은 환경변수로 바꿀 수 있습니다.

```bash
INSTANCE_TYPE=t3.micro SSH_CIDR=203.0.113.10/32 bash scripts/provision.sh
```

`infra/user-data.sh` 는 인스턴스 최초 부팅 시 1회 실행되어 Nginx 를 설치하고, 기본 사이트를 다음과 같이 교체합니다.

- `/` — 인스턴스의 AZ·프라이빗 IP 를 표시하는 정적 페이지
- `/health` — 파일이 아닌 `return 200 "OK"` 고정 응답. 디스크 상태와 무관하게 항상 같은 본문을 반환하므로 헬스체크로 적합합니다

`sleep 90` 이 필요한 이유는 `running` 상태가 user-data 완료를 보장하지 않기 때문입니다. 이 차이 때문에 검증이 한 번 실패했습니다([트러블슈팅 Case 2](docs/troubleshooting.md)).

---

## 트러블슈팅

[`docs/troubleshooting.md`](docs/troubleshooting.md) — 1절은 계층별 진단 절차, 2절은 실제 발생한 장애 3건의 증상·가설·검증·조치·결과·재발방지 기록입니다.

| # | 발생 단계 | 증상 | 원인 |
|:-:|-----------|------|------|
| 1 | 인프라 생성 | `UnauthorizedOperation` 으로 프로비저닝 중단 | IAM 정책에 `ec2:ModifySubnetAttribute` 누락 |
| 2 | 외부 접속 검증 | 80 포트 `Connection refused` | user-data 의 Nginx 설치가 아직 진행 중 |
| 3 | SSH 접속 | 되던 SSH 가 갑자기 타임아웃 | 네트워크 전환으로 운영자 공인 IP 변경 |

세 건 모두 "증상이 같아도 원인 계층은 다르다"는 점을 보여줍니다.
2번은 타임아웃이 아니라 `Connection refused` 였다는 점에서 AWS 설정이 아닌 서버 내부 문제로 좁혀졌고, 3번은 80 포트는 되는데 22 포트만 안 되는 비대칭이 보안 그룹을 가리켰습니다.

---

## 리소스 정리

[`docs/cleanup-checklist.md`](docs/cleanup-checklist.md) 에 삭제 순서와 항목별 확인 명령, 실행 기록을 남겼습니다. 2026-08-10 23:58 정리 완료했습니다.

`cleanup.sh` 는 의존 관계 역순(EC2 → EIP → EBS → 라우트 테이블 → IGW → 서브넷 → SG → VPC → 키페어)으로 삭제하고, 마지막에 남은 리소스를 다시 조회해 출력합니다.
구조적으로도 과금 위험을 줄였습니다. 루트 볼륨은 `DeleteOnTermination=true` 이고, Elastic IP 는 아예 할당하지 않았습니다.

---

## 디렉토리 구조

```
B6-1.aws-infra-base/
├── docs/                           # 제출 문서 및 증빙
│   ├── architecture.png            # 아키텍처 다이어그램
│   ├── troubleshooting.md          # 트러블슈팅 보고서
│   ├── cleanup-checklist.md        # 리소스 정리 체크리스트
│   ├── verification.log            # verify.sh 실행 기록
│   └── images/                     # 접속·과금 증빙 스크린샷
├── infra/                          # 인프라 정의
│   ├── iam-policy.json             # IAM 사용자에 부여한 최소 권한 정책
│   └── user-data.sh                # EC2 부팅 시 Nginx 설치·설정
├── scripts/                        # 실행 스크립트
│   ├── common.sh                   # 공통 설정 · 보안 그룹 규칙 판정
│   ├── provision.sh                # 인프라 생성
│   ├── verify.sh                   # 요구사항 검증
│   ├── cleanup.sh                  # 리소스 삭제 (생성 역순)
│   ├── test-sg-rules.sh            # 보안 그룹 판정 로직 단위 테스트
│   └── render_architecture.py      # architecture.png 생성
└── README.md
```

---

## 제약 사항

- 프리티어 범위 내에서 진행합니다. 서울 리전 프리티어 대상인 `t2.micro` 를 기본값으로 두었고, EBS 는 8 GiB 로 시작합니다
- 루트 계정으로는 콘솔·CLI 에 접근하지 않으며, `codyssey-infra` IAM 사용자만 사용합니다
- 키페어 개인키는 생성 시점에만 내려받을 수 있어 재발급이 불가능합니다. `~/.ssh/codyssey-key.pem` 에 권한 `400` 으로 보관하며 저장소에 커밋하지 않습니다
- 단일 AZ · 단일 인스턴스 구성이므로 고가용성은 범위에 없습니다. ALB, Auto Scaling, RDS, HTTPS(보너스 과제)는 구현하지 않았습니다
