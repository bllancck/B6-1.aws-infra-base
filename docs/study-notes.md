# AWS 기초 웹 인프라 학습 노트

이 문서는 AWS 용어를 전부 외우기 위한 사전이 아닙니다. 이 과제의 구조를 이해하고, 직접 구축하고, 문제가 생겼을 때 원인을 찾는 데 필요한 개념만 설명합니다.

처음에는 **1장 전체 구조**와 **2장 핵심 구성 요소**만 읽고 아키텍처를 다시 확인하세요. 나머지는 구축과 검증 과정에서 필요할 때 찾아보면 됩니다.

---

## 1. 전체 구조부터 이해하기

이 과제는 다음 흐름을 만드는 작업입니다.

```text
사용자
  → Internet Gateway
  → Route Table이 연결한 Public Subnet
  → Security Group
  → EC2
  → Nginx
  → HTTP 응답
```

AWS 리소스의 포함 관계는 다음과 같습니다.

```text
AWS 계정
└── 서울 리전
    └── VPC
        ├── Internet Gateway
        ├── Route Table
        ├── Security Group (EC2에 연결)
        └── Public Subnet (하나의 가용 영역에 속함)
            └── EC2
                └── Nginx
```

IAM은 위 네트워크 안에 있는 장비가 아닙니다. AWS 계정에서 **누가 리소스를 만들고 변경할 수 있는지** 결정하는 별도의 권한 체계입니다.

---

## 2. 가장 먼저 알아야 할 구성 요소

### VPC

AWS 계정 안에 만드는 독립된 가상 네트워크입니다. 이 과제에서는 `10.0.0.0/16` 범위를 사용하며, Subnet과 EC2 같은 네트워크 리소스가 이 안에 배치됩니다.

### Subnet

VPC의 IP 범위를 더 작게 나눈 공간입니다. EC2는 반드시 하나의 Subnet에 배치되며, Subnet 하나는 하나의 가용 영역에 속합니다.

이 과제의 `10.0.1.0/24` Subnet은 인터넷으로 향하는 경로와 퍼블릭 IP 자동 할당 설정을 가진 **Public Subnet**입니다.

### Internet Gateway

VPC와 인터넷을 연결하는 출입구입니다. VPC에 연결하기만 해서는 인터넷 통신이 되지 않으며, Route Table에도 Internet Gateway로 향하는 경로가 있어야 합니다.

### Route Table

네트워크 트래픽을 어디로 보낼지 정하는 규칙 모음입니다.

```text
0.0.0.0/0 → Internet Gateway
```

위 규칙은 VPC 내부 목적지가 아닌 모든 IPv4 트래픽을 Internet Gateway로 보내라는 뜻입니다. 이 경로가 연결된 Subnet을 Public Subnet이라고 부릅니다.

### EC2

AWS에서 빌려 사용하는 가상 서버입니다. 이 과제에서는 Ubuntu가 설치된 EC2 한 대를 만들고 그 안에서 Nginx를 실행합니다.

### Nginx

브라우저나 `curl`이 보낸 HTTP 요청을 받아 웹 페이지나 상태 값을 반환하는 웹 서버 프로그램입니다. 이 프로젝트에서는 `/` 요청에 웹 페이지를, `/health` 요청에 `OK`를 반환합니다.

### Security Group

EC2에 연결하는 가상 방화벽입니다. 어떤 출발지에서 어떤 포트로 들어오는 통신을 허용할지 정합니다.

- HTTP 80번 포트: 모든 사용자에게 허용
- SSH 22번 포트: 운영자 IP 한 개에만 허용
- 나머지 인바운드 통신: 허용 규칙이 없으므로 차단

Security Group은 **네트워크 통신**을 제어합니다. AWS 리소스를 만들거나 삭제할 권한을 제어하는 IAM과 역할이 다릅니다.

### IAM

AWS에서 사용자와 권한을 관리하는 서비스입니다. 이 과제에서는 별도의 IAM 사용자가 EC2와 VPC 관련 작업만 수행하도록 제한하고, 전체 관리자 권한은 부여하지 않습니다.

IAM은 **AWS API를 누가 호출할 수 있는지** 제어합니다. 예를 들어 EC2 생성 권한이 없으면 서버를 만들 수 없지만, 이미 실행 중인 웹 서버의 80번 포트 통신을 막지는 않습니다.

### AWS CLI, Resource, Tag

- **AWS CLI**: 터미널에서 명령어로 AWS를 조작하는 도구입니다. 이 프로젝트의 자동화 스크립트가 사용합니다.
- **Resource**: VPC, Subnet, EC2처럼 AWS에서 생성하고 관리하는 대상을 뜻합니다.
- **Tag**: 리소스에 붙이는 이름표입니다. 이 프로젝트는 같은 프로젝트의 리소스를 찾아 검증하고 빠짐없이 삭제하는 데 Tag를 사용합니다.

---

## 3. 함께 알아야 하는 네트워크 용어

### Region과 Availability Zone

- **Region**: AWS 데이터센터가 모여 있는 지리적 지역입니다. 이 과제는 서울 리전 `ap-northeast-2`를 사용합니다.
- **Availability Zone(AZ)**: 한 Region 안에서 물리적으로 분리된 데이터센터 그룹입니다. 이 과제의 Subnet은 `ap-northeast-2a`에 생성됩니다.

VPC는 Region 범위의 리소스이고, Subnet은 하나의 AZ에 속합니다.

### CIDR

IP 주소 범위를 표현하는 방식입니다.

- `10.0.0.0/16`: VPC가 사용하는 넓은 사설 IP 범위
- `10.0.1.0/24`: Subnet이 사용하는 더 작은 범위
- `운영자 IP/32`: IPv4 주소 한 개만 의미
- `0.0.0.0/0`: 모든 IPv4 주소를 의미

뒤의 숫자가 클수록 주소 범위는 작아집니다. 따라서 `/32`는 주소 한 개이고 `/16`은 많은 주소를 포함합니다.

### Public IP와 Private IP

- **Private IP**: VPC 내부 통신에 사용하는 주소
- **Public IP**: 인터넷에서 EC2에 접근할 때 사용하는 주소

EC2가 Public Subnet 안에 있더라도 Public IP가 없으면 인터넷에서 직접 접속할 수 없습니다. 이 과제는 Subnet의 퍼블릭 IPv4 자동 할당 기능을 사용합니다.

### Port

한 서버 안에서 어떤 프로그램과 통신할지 구분하는 번호입니다.

- `80`: HTTP 웹 서비스
- `22`: SSH 원격 접속

서버에 Public IP가 있어도 Security Group에서 해당 포트를 허용하지 않으면 접속할 수 없습니다.

### Inbound와 Outbound

- **Inbound**: 외부에서 EC2로 들어오는 통신
- **Outbound**: EC2에서 외부로 나가는 통신

웹 사용자의 요청은 Inbound이고, EC2가 Ubuntu 패키지를 내려받는 통신은 Outbound입니다.

---

## 4. 서버를 만들 때 등장하는 용어

### AMI

EC2를 생성할 때 사용하는 운영체제 이미지입니다. 이 과제는 Ubuntu 24.04 LTS 이미지를 사용합니다.

### Instance Type

EC2의 CPU와 메모리 크기를 정하는 유형입니다. 이 과제는 프리 티어 범위를 고려해 `t2.micro`를 사용합니다.

### EBS

EC2에 연결하는 디스크입니다. 운영체제와 Nginx 파일이 저장됩니다. 루트 EBS의 `DeleteOnTermination`을 활성화하면 EC2 삭제 시 디스크도 함께 삭제되어 불필요한 과금을 방지할 수 있습니다.

### Key Pair와 SSH

- **Key Pair**: EC2 로그인에 사용하는 공개 키와 개인 키의 쌍
- **SSH**: 원격 서버의 터미널에 안전하게 접속하는 방식

AWS에는 공개 키가 등록되고, 사용자는 개인 키 파일을 보관합니다. 개인 키는 저장소에 커밋하면 안 됩니다.

### User Data

EC2가 처음 시작될 때 자동으로 실행하는 초기 설정 스크립트입니다. 이 과제에서는 [`infra/user-data.sh`](../infra/user-data.sh)가 Nginx를 설치하고 웹 페이지와 `/health` 경로를 설정합니다.

EC2 상태가 `running`이어도 User Data 작업은 아직 끝나지 않았을 수 있습니다. 따라서 인스턴스 생성 직후에는 Nginx가 응답할 때까지 기다려야 할 수 있습니다.

### localhost

현재 컴퓨터 자신을 가리키는 주소입니다. EC2 안에서 `curl http://localhost`를 실행하면 외부 네트워크를 거치지 않고 EC2 내부의 Nginx만 검사합니다.

---

## 5. 보안과 권한의 차이

두 개념을 다음 질문으로 구분하면 됩니다.

- **Security Group**: 누가 EC2의 어느 포트로 통신할 수 있는가?
- **IAM**: 누가 AWS 리소스를 생성·조회·변경·삭제할 수 있는가?

예를 들어 IAM 권한을 최소화해도 Security Group에서 SSH를 전체 공개하면 서버 접근 위험이 생깁니다. 반대로 SSH를 안전하게 제한해도 IAM 사용자에게 관리자 권한을 주면 AWS 리소스 전체가 위험해질 수 있습니다.

### 최소 권한 원칙

사용자나 시스템에 작업 수행에 필요한 권한만 부여하는 원칙입니다.

이 과제에서는 다음과 같이 적용합니다.

- IAM 사용자에게 EC2와 VPC 구성에 필요한 작업만 허용
- 관련 없는 S3, RDS 등의 서비스 권한은 부여하지 않음
- `AdministratorAccess`는 부여하지 않음
- SSH는 모든 IP가 아니라 운영자 IP만 허용

---

## 6. 구축 순서와 이유

인프라는 앞 단계의 리소스를 다음 단계가 사용하므로 순서대로 생성해야 합니다.

```text
VPC
→ Subnet
→ Internet Gateway
→ Route Table
→ Security Group
→ Key Pair
→ EC2
→ Nginx
```

[`scripts/provision.sh`](../scripts/provision.sh)는 이 순서대로 리소스를 생성합니다. 처음 읽을 때는 AWS CLI 옵션을 전부 해석하려 하지 말고, 각 코드 블록이 위 단계 중 무엇을 만드는지만 확인하세요.

리소스를 삭제할 때는 의존 관계 때문에 대체로 생성의 역순을 따릅니다. EC2가 Subnet을 사용 중이면 VPC부터 먼저 삭제할 수 없습니다.

---

## 7. 검증할 때 알아야 하는 개념

### HTTP와 상태 코드

HTTP는 웹 클라이언트와 서버가 요청과 응답을 주고받는 규칙입니다. `200 OK`는 요청이 정상 처리되었다는 의미입니다.

### curl

터미널에서 HTTP 요청을 보내는 도구입니다.

```bash
curl -i http://<퍼블릭-IP>/health
```

위 명령으로 외부에서 Nginx까지 전체 경로가 정상인지 확인할 수 있습니다.

### Health Check

서비스가 요청을 처리할 수 있는지 확인하는 전용 경로입니다. 이 과제의 `/health`는 정상일 때 `200 OK`와 고정된 본문 `OK`를 반환하므로 검증 결과를 판단하기 쉽습니다.

### 내부 검증과 외부 검증

- EC2 내부의 `curl http://localhost`: Nginx 자체가 동작하는지 확인
- 외부의 `curl http://<퍼블릭-IP>/health`: Public IP, Internet Gateway, Route Table, Security Group, EC2, Nginx의 전체 경로 확인

내부 검증은 성공하지만 외부 검증이 실패한다면 Nginx보다 네트워크 경로나 Security Group을 먼저 확인합니다.

[`scripts/verify.sh`](../scripts/verify.sh)는 네트워크, 보안 규칙, 외부 응답, EC2 내부 상태를 한 번에 검사합니다.

---

## 8. 증상으로 문제 범위 좁히기

### Timeout

요청을 보냈지만 정해진 시간 안에 응답이 오지 않은 상태입니다. Public IP, Route Table, Internet Gateway, Security Group처럼 통신 경로에 문제가 없는지 확인합니다.

### Connection refused

서버까지는 도달했지만 해당 포트에서 요청을 받는 프로그램이 없는 경우가 많습니다. Nginx 설치와 실행 상태, 포트 설정을 확인합니다.

### UnauthorizedOperation 또는 AccessDenied

AWS API를 호출한 사용자에게 필요한 IAM 권한이 없다는 의미입니다. 실패한 작업에 필요한 권한이 정책에 포함되어 있는지 확인합니다.

### 문제 해결 순서

```text
증상 기록
→ 원인 가설 세우기
→ 명령이나 로그로 확인하기
→ 필요한 부분만 수정하기
→ 같은 방법으로 다시 검증하기
→ 재발 방지 방법 기록하기
```

실제 발생한 문제는 [`troubleshooting.md`](troubleshooting.md)에 정리되어 있습니다.

---

## 9. 과금과 리소스 정리

클라우드 리소스는 사용하지 않아도 실행 중이거나 할당된 상태로 남아 있으면 과금될 수 있습니다. 특히 EC2, EBS, Elastic IP, NAT Gateway 같은 리소스를 확인해야 합니다.

이 과제에서는 [`scripts/cleanup.sh`](../scripts/cleanup.sh)로 리소스를 의존 관계의 역순으로 삭제하고, [`cleanup-checklist.md`](cleanup-checklist.md)로 남은 리소스가 없는지 확인합니다.

NAT Gateway, ALB, RDS는 이번 기본 구성에서 생성하지 않습니다. 과제 설명에 등장하더라도 지금 단계에서 사용법까지 학습할 필요는 없습니다.

---

## 10. 과제 해결 순서

1. 아키텍처 그림에서 VPC, Subnet, Internet Gateway, EC2, Security Group을 찾습니다.
2. 외부 요청이 Nginx까지 이동하는 경로를 말로 설명합니다.
3. Security Group과 IAM의 차이를 설명합니다.
4. `provision.sh`에서 각 리소스를 생성하는 부분을 순서대로 찾습니다.
5. 인프라를 생성하고 Nginx 설치가 끝날 때까지 기다립니다.
6. `verify.sh`로 내부 상태와 외부 접속을 검증합니다.
7. 문제가 생기면 증상, 가설, 검증, 조치, 결과, 재발 방지를 기록합니다.
8. 제출에 필요한 다이어그램과 접속 증빙을 정리합니다.
9. `cleanup.sh`와 체크리스트로 모든 실습 리소스를 정리합니다.

---

## 11. 스스로 확인할 질문

다음 질문에 짧게 답할 수 있으면 이 과제에 필요한 핵심 개념을 이해한 것입니다.

1. VPC와 Subnet은 어떤 관계인가?
2. Public Subnet이 인터넷과 통신하려면 무엇이 필요한가?
3. EC2에 Public IP가 필요한 이유는 무엇인가?
4. Security Group과 IAM은 각각 무엇을 제어하는가?
5. HTTP 80번 포트와 SSH 22번 포트의 공개 범위가 다른 이유는 무엇인가?
6. `curl localhost`는 성공하지만 외부 접속은 실패한다면 어디부터 확인해야 하는가?
7. EC2가 `running`이어도 Nginx가 바로 응답하지 않을 수 있는 이유는 무엇인가?
8. 실습 종료 후 리소스를 삭제해야 하는 이유는 무엇인가?

답이 막히면 해당 용어의 정의만 외우지 말고, 아키텍처에서 그 구성 요소가 어디에 있고 앞뒤로 무엇과 연결되는지 다시 확인하세요.
