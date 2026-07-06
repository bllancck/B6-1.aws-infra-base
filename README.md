# AWS 클라우드 웹 서비스 인프라 구축 프로젝트
   
[![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=flat-square&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Nginx](https://img.shields.io/badge/Nginx-%23009639.svg?style=flat-square&logo=nginx&logoColor=white)](https://nginx.org/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-%23E95420.svg?style=flat-square&logo=ubuntu&logoColor=white)](https://ubuntu.com/)

이 프로젝트는 AWS(Amazon Web Services) 환경에서 안정적이고 보안이 강화된 웹 서비스 인프라를 직접 설계 및 구축하고, 웹 서버(Nginx)를 가동하여 외부 트래픽을 처리할 수 있도록 구현한 결과물입니다. 최소 권한의 보안 원칙(Security Group, IAM Role)을 적용하고 실습 종료 후 자원 정리를 완료하였습니다.

---

## 프로젝트 개요

* **분야**: AI/SW 기초 (클라우드와 AI API)
* **목표**: VPC 설계, Public Subnet 구성, Internet Gateway 연동, Route Table 작성, EC2 가상 서버 기동, Nginx 웹 서버 배포, 인바운드 보안 그룹 제한, IAM 최소권한 적용 및 과금 방지를 위한 리소스 정리
* **리전**: 서울 리전 (`ap-northeast-2`)

---

## 시스템 아키텍처 다이어그램

구축한 network 및 가상 서버 인프라의 아키텍처 설계도입니다.

```text
 ┌────────────────────────────────────────────────────────┐
 │ AWS Cloud (Seoul Region: ap-northeast-2)               │
 │                                                        │
 │ ┌────────────────────────────────────────────────────┐ │
 │ │ VPC (10.0.0.0/16)                                  │ │
 │ │                                                    │ │
 │ │ ┌────────────────────────────────────────────────┐ │ │
 │ │ │ Public Subnet (10.0.1.0/24)                    │ │ │
 │ │ │                                                │ │ │
 │ │ │ ┌────────────────────────────────────────────┐ │ │ │
 │ │ │ │ EC2 Instance (t2.micro / Ubuntu)           │ │ │ │
 │ │ │ │ - Private IP: 10.0.1.x                     │ │ │ │
 │ │ │ │ - Public IP: [작성 필요: 예 54.180.x.x]   │ │ │ │
 │ │ │ │ - Web Server: Nginx (Port 80)              │ │ │ │
 │ │ │ └────────────────────────────────────────────┘ │ │ │ │
 │ │ └─────────────────────────┬──────────────────────┘ │ │
 │ └───────────────────────────┼────────────────────────┘ │
 │                             │                          │
 │                    ┌────────┴────────┐                 │
 │                    │ Internet Gateway│                 │
 │                    └────────┬────────┘                 │
 └─────────────────────────────┼──────────────────────────┘
                               │ (HTTP: 80 / SSH: 22)
                           [Internet]
                               │
                       ┌───────┴───────┐
                       │   Client PC   │
                       └───────────────┘
```

* **다이어그램 상세 제출본**: [docs/architecture.png](file:///c:/Users/byjyj/Desktop/Codyssey/B6-1/docs/architecture.png) 또는 `docs/architecture.pdf`로 대체 제출 가능.

---

## 인프라 세부 스펙 (Tech Spec)

### 1. VPC & 네트워크 구성
* **VPC CIDR**: `10.0.0.0/16`
* **Subnet**: Public Subnet 1개 (`10.0.1.0/24`)
* **Internet Gateway**: `IGW` 생성 후 VPC에 Attach 완료
* **Route Table**: Public Subnet에 라우팅 테이블 연결 (`0.0.0.0/0` -> Internet Gateway ID)

### 2. 가상 컴퓨터 (EC2)
* **인스턴스 타입**: `t2.micro` (또는 `t3.micro`)
* **OS**: `Ubuntu 22.04 LTS` (또는 `Amazon Linux 2023`)
* **스토리지**: EBS `8 GiB` (General Purpose SSD - gp3)
* **웹 서버**: Nginx v1.18+ (정상 기동 및 로컬 루프백 `curl http://localhost` 200 OK 검증 완료)

### 3. 접근 제어 및 보안 (Security Group & IAM)
* **Security Group (보안 그룹) 규칙**:
  * **Inbound Rules**:
    * **HTTP (80)**: `0.0.0.0/0` (모든 IP에 대해 웹 서비스 공개)
    * **SSH (22)**: `[작성 필요: 본인의 개인 IP]/32` (학습자 IP 외 다른 접속 차단)
  * **Outbound Rules**:
    * **All Traffic**: `0.0.0.0/0` (EC2에서 인터넷으로 나가는 모든 통신 허용 - 패키지 설치용)

> [!WARNING]
> 보안 사고 방지를 위해 `0.0.0.0/0` 대역에 대한 전체 포트(0-65535) 개방은 절대 금지합니다.

* **IAM 최소 권한 규칙**:
  * 관리자 권한(`AdministratorAccess`)을 완전히 배제하고, EC2 및 VPC, Security Group 제어 권한만을 가진 IAM 계정을 생성하여 실습을 수행함. (S3, RDS 등 무관한 서비스 접근 권한 제한)

---

## 외부 접속 검증 및 증빙 (Verification)

웹 인프라 구축 완료 후 외부 인터넷 망을 통한 접속 검증 결과입니다.

* **외부 접속 확인 방식**: [선택한 방식 기재: (A) 브라우저 접속 또는 (B) GET health API 호출]
* **접속 주소 (URL 또는 IP)**: `http://[여기에 퍼블릭 IP 또는 도메인 주소 기재]`
* **접속 결과 응답 상태**: HTTP Status `200 OK` (정상 응답 확인)

### 외부 접속 스크린샷 (제출 필수)

> [!NOTE]
> 아래 경로에 실습 결과 확인 스크린샷 이미지를 위치시켜 주십시오. (예: `docs/images/web_access.png`)

![웹 서비스 외부 접속 증빙 스크린샷](docs/images/web_access.png)

---

## 트러블슈팅 및 로그 분석 요약 (Troubleshooting Summary)

실습 인프라를 구축하는 과정에서 겪은 네트워크 통신 및 권한 오류에 대한 트러블슈팅 결과 요약입니다.

| 발생 단계 | 발생 증상 | 원인 가설 | 검증 방법 | 조치 내용 및 결과 |
| :--- | :--- | :--- | :--- | :--- |
| **네트워크 설정** | 외부 브라우저 접속 불가 | 보안 그룹에 HTTP 80번 규칙이 유실되었거나 활성화 안 됨 | AWS Console 보안 그룹 탭 확인 | 인바운드 규칙에 HTTP (80) `0.0.0.0/0` 허용 추가 후 접속 정상화 |
| **서버 접속** | EC2 키페어 오류로 SSH 거부 | 로컬 키페어 파일(`.pem`)의 권한이 지나치게 열려 있음 | `ssh` 접속 시 permission warning 확인 | Windows PowerShell에서 보안 속성 제한 설정 후 정상 로그인 |

* **상세 분석 보고서**: [docs/troubleshooting.md](file:///c:/Users/byjyj/Desktop/Codyssey/B6-1/docs/troubleshooting.md)

---

## 자원 회수 및 과금 방지 검증 (Resource Cleanup)

AWS 프리티어 범위를 준수하고 과도한 청구를 막기 위해 실습 종료 즉시 모든 자원의 폐기를 완료하고 체크리스트로 확인을 마쳤습니다.

* **자원 정리 상태**: **삭제 완료**
* **정리 대상**: EC2 인스턴스(Terminated), EBS 볼륨(Deleted), Elastic IP(Released), Internet Gateway(Detached & Deleted), VPC & Subnet(Deleted)
* **리소스 정리 세부 내역 및 Billing 증빙**: [docs/cleanup-checklist.md](file:///c:/Users/byjyj/Desktop/Codyssey/B6-1/docs/cleanup-checklist.md)
