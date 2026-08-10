# 트러블슈팅 보고서

외부에서 웹 서버까지 도달하려면 **라우팅 → 퍼블릭 IP → 보안 그룹 → OS → 웹 서버** 다섯 계층이 모두 열려 있어야 한다.
어느 계층이 막혀도 브라우저에는 똑같이 "접속할 수 없음"으로 보이므로, 증상만으로는 원인을 좁힐 수 없다.
1절은 계층을 하나씩 배제하는 진단 절차, 2절은 실습 중 실제로 발생한 장애 3건의 기록이다.

---

## 1. 진단 절차 — 외부 접속 실패

위에서 아래로 순서대로 확인한다. 먼저 실패한 계층이 원인이므로, 그 아래는 확인하지 않아도 된다.

| # | 계층 | 확인 방법 | 정상 판정 | 실패 시 원인 |
|:-:|------|-----------|-----------|--------------|
| 1 | 인스턴스 | `aws ec2 describe-instances --instance-ids <id> --query 'Reservations[].Instances[].[State.Name,PublicIpAddress]'` | `running` + 퍼블릭 IP 존재 | IP 가 `None` 이면 서브넷의 퍼블릭 IPv4 자동 할당이 꺼져 있음 |
| 2 | 라우팅 | 서브넷에 연결된 라우트 테이블의 `0.0.0.0/0` 대상 확인 | `igw-...` | 경로 누락 또는 IGW 가 VPC 에 attach 되지 않음 |
| 3 | 보안 그룹 | 인바운드 규칙의 80/tcp 소스 확인 | `0.0.0.0/0` | 80 규칙 누락, 또는 소스가 내 IP 로만 제한됨 |
| 4 | OS | `ss -tlnp \| grep :80` | nginx 가 `0.0.0.0:80` LISTEN | nginx 미기동, 또는 `127.0.0.1:80` 에만 바인딩 |
| 5 | 웹 서버 | `curl -i http://localhost` | `200` | 설정 오류. `journalctl -u nginx -n 50` 확인 |

계층 1~3 은 AWS 설정 문제, 4~5 는 서버 내부 문제다. 두 영역은 **증상이 다르게 나타난다.**

| curl 결과 | 의미 | 원인 위치 |
|-----------|------|-----------|
| `Connection timed out` | 패킷이 응답 없이 버려짐 | 계층 1~3 (AWS) |
| `Connection refused` | 패킷은 도달했으나 리스닝 프로세스가 없음 | 계층 4~5 (서버 내부) |
| `4xx` / `5xx` | 웹 서버까지 도달 후 처리 실패 | 계층 5 (Nginx 설정) |

`scripts/verify.sh` 는 이 다섯 계층을 한 번에 점검한다.

### 함께 보는 로그

| 대상 | 위치 | 용도 |
|------|------|------|
| cloud-init (user-data) | `/var/log/cloud-init-output.log` | Nginx 설치·설정 자동화 실패 원인 |
| Nginx 접근 로그 | `/var/log/nginx/access.log` | 외부 요청이 서버까지 도달했는지 판정 |
| Nginx 오류 로그 | `/var/log/nginx/error.log` | 설정 문법 오류, 권한 오류 |
| 부팅 콘솔 출력 | `aws ec2 get-console-output --instance-id <id>` | SSH 조차 안 될 때의 최후 수단 |

---

## 2. 장애 기록

| # | 발생 단계 | 증상 | 원인 | 조치 |
|:-:|-----------|------|------|------|
| 1 | 인프라 생성 | `UnauthorizedOperation` 으로 프로비저닝 중단 | IAM 정책에 `ec2:ModifySubnetAttribute` 누락 | 정책에 액션 추가 후 재실행 |
| 2 | 외부 접속 검증 | 80 포트 `Connection refused` | user-data 의 Nginx 설치가 아직 진행 중 | cloud-init 완료 대기 후 재검증 |
| 3 | SSH 접속 | 20분 전까지 되던 SSH 가 타임아웃 | 네트워크 전환으로 운영자 공인 IP 변경 | 보안 그룹 22 규칙의 소스 갱신 |

---

### Case 1. IAM 권한 부족으로 프로비저닝 중단

**증상** — 2026-08-10 22:41, `scripts/provision.sh` 실행 중 서브넷 생성 직후 중단됐다.

```console
[22:41:03] VPC 생성 (10.0.0.0/16)
  vpc-0b8c14e2a9f3d7c51

[22:41:06] 퍼블릭 서브넷 생성 (10.0.1.0/24, ap-northeast-2a)
An error occurred (UnauthorizedOperation) when calling the ModifySubnetAttribute
operation: You are not authorized to perform this operation.
User: arn:aws:iam::428139057361:user/codyssey-infra is not authorized to perform:
ec2:ModifySubnetAttribute on resource:
arn:aws:ec2:ap-northeast-2:428139057361:subnet/subnet-04e7a1c9b6d2f8e30
because no identity-based policy allows the ec2:ModifySubnetAttribute action
```

**원인 가설**

1. 직접 작성한 IAM 정책에 해당 액션이 빠져 있다.
2. 정책의 리전 조건(`aws:RequestedRegion`)이 요청을 걸러냈다.

**검증**

| 가설 | 확인 방법 | 결과 | 판정 |
|:-:|------|------|:-:|
| 1 | `grep -c ModifySubnetAttribute infra/iam-policy.json` | `0` — 액션이 정책에 없음 | **채택** |
| 2 | 같은 리전의 `CreateVpc`·`CreateSubnet` 은 직전에 성공 | 리전 조건은 통과하고 있음 | 기각 |

오류 메시지의 `because no identity-based policy allows ...` 문구도 조건 거부가 아닌 **액션 누락**을 가리킨다.
조건에 걸린 경우라면 `with an explicit deny in an identity-based policy` 로 표시된다.

**조치**

`infra/iam-policy.json` 의 `ManageLabNetwork` 문에 `ec2:ModifySubnetAttribute` 를 추가하고 정책을 갱신했다.
중단 시점에 VPC 와 서브넷이 남아 있어 `provision.sh` 가 중복 생성을 거부하므로, `scripts/cleanup.sh` 로 먼저 정리한 뒤 재실행했다.

**결과** — 22:52 정책 갱신, 23:05 재실행이 EC2 생성까지 완주했다.

```console
[23:05:41] EC2 인스턴스 생성 (t2.micro, gp3 8GiB)
  i-0a3f5c9d2b7e41f68 — running 대기

생성 완료
  Public IPv4     43.202.71.184
```

**재발 방지** — 정책을 손으로 열거하다 보면 이런 누락이 반복된다.
스크립트가 호출하는 API 를 뽑아 정책과 대조하는 절차를 정리 작업에 포함했다.

```bash
grep -oh 'aws ec2 [a-z-]*' scripts/*.sh | sort -u
```

---

### Case 2. 웹 서버 미기동 상태에서 외부 접속 검증

**증상** — 23:07, 인스턴스가 `running` 이 된 직후 `scripts/verify.sh` 를 실행했더니 외부 접속 3개 항목만 실패했다.

```console
[23:07:12] 3. 외부 접속 검증
  FAIL  GET http://43.202.71.184/                000   (기대: 200)
  FAIL  GET http://43.202.71.184/health          000   (기대: 200)
  FAIL  /health 응답 본문                                (기대: OK)
```

```console
$ curl -v http://43.202.71.184/
*   Trying 43.202.71.184:80...
* connect to 43.202.71.184 port 80 failed: Connection refused
```

**원인 가설**

1. 보안 그룹에 80 포트 인바운드 규칙이 없다.
2. Nginx 가 아직 기동하지 않았다.

**검증**

| 가설 | 확인 방법 | 결과 | 판정 |
|:-:|------|------|:-:|
| 1 | 같은 실행의 보안 그룹 점검 항목 | `HTTP 80 ← 0.0.0.0/0 허용  PASS` | 기각 |
| 2 | SSH 접속 후 `systemctl is-active nginx` | `inactive` (유닛이 아직 설치되지 않음) | **채택** |

증상이 타임아웃이 아니라 **`Connection refused`** 였다는 점이 결정적이었다.
패킷이 인스턴스까지 도달해 RST 를 받은 것이므로 보안 그룹과 라우팅은 정상이고, 문제는 서버 내부에 있다.
cloud-init 이 여전히 실행 중이었다.

```console
ubuntu@ip-10-0-1-147:~$ cloud-init status
status: running

ubuntu@ip-10-0-1-147:~$ tail -3 /var/log/cloud-init-output.log
Get:14 http://ap-northeast-2.ec2.archive.ubuntu.com/ubuntu noble/main amd64 nginx amd64 1.24.0-2ubuntu7
Setting up nginx-core (1.24.0-2ubuntu7) ...
Setting up nginx (1.24.0-2ubuntu7) ...
```

**조치** — `cloud-init status --wait` 로 초기화 완료를 기다린 뒤 재검증했다. 설정 변경은 필요하지 않았다.

**결과** — 23:11 재실행에서 11개 항목 전부 통과했다. 전체 출력은 [`verification.log`](verification.log) 에 있다.

```console
[23:11:50] 3. 외부 접속 검증
  PASS  GET http://43.202.71.184/                200
  PASS  GET http://43.202.71.184/health          200
  PASS  /health 응답 본문                          OK

결과: 11개 통과 / 0개 실패
```

**재발 방지** — 인스턴스가 `running` 인 것과 애플리케이션이 서비스 가능한 것은 다르다.
`running` 은 하이퍼바이저 관점의 상태일 뿐 user-data 완료를 보장하지 않으므로, 검증 전에 대기 단계를 명시적으로 두었다.
README 실행 절차에 `sleep 90` 을 넣고, SSH 가 가능한 상황에서는 `cloud-init status --wait` 를 쓰도록 정리했다.

---

### Case 3. 공인 IP 변경으로 SSH 접속 차단

**증상** — 23:35, 20분 전까지 정상이던 SSH 접속이 타임아웃됐다. 같은 시각 HTTP 접속은 정상이었다.

```console
$ ssh -i ~/.ssh/codyssey-key.pem ubuntu@43.202.71.184
ssh: connect to host 43.202.71.184 port 22: Connection timed out

$ curl -s -o /dev/null -w '%{http_code}\n' http://43.202.71.184/health
200
```

**원인 가설**

1. 인스턴스가 중단·재부팅되었다.
2. 보안 그룹 22 규칙의 소스 IP 와 현재 공인 IP 가 달라졌다.

**검증**

| 가설 | 확인 방법 | 결과 | 판정 |
|:-:|------|------|:-:|
| 1 | `describe-instances` 상태 확인 + HTTP 200 응답 | `running`, 웹 서비스 정상 | 기각 |
| 2 | 현재 공인 IP 와 보안 그룹 규칙 비교 | `39.7.51.202` vs 규칙 `118.235.12.77/32` | **채택** |

```console
$ curl -s https://checkip.amazonaws.com
39.7.51.202

$ aws ec2 describe-security-groups --group-ids sg-0d1e6a8c37b95f2a4 \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[].CidrIp" --output text
118.235.12.77/32
```

**80 포트는 되는데 22 포트만 안 되는 비대칭**이 단서였다.
인스턴스·라우팅·IGW 는 두 포트가 공유하므로, 한쪽만 실패한다면 원인은 포트별로 다른 설정, 즉 보안 그룹 규칙일 수밖에 없다.
실습 도중 Wi-Fi 에서 모바일 테더링으로 전환하면서 공인 IP 가 바뀐 것이 원인이었다.

**조치** — 기존 규칙을 제거하고 현재 IP 로 다시 등록했다. 편의를 위해 `0.0.0.0/0` 으로 열지는 않았다.

```bash
aws ec2 revoke-security-group-ingress --group-id sg-0d1e6a8c37b95f2a4 \
  --protocol tcp --port 22 --cidr 118.235.12.77/32
aws ec2 authorize-security-group-ingress --group-id sg-0d1e6a8c37b95f2a4 \
  --protocol tcp --port 22 --cidr "$(curl -s https://checkip.amazonaws.com)/32"
```

**결과** — 23:42 SSH 접속이 즉시 복구됐다.

```console
$ ssh -i ~/.ssh/codyssey-key.pem ubuntu@43.202.71.184
Welcome to Ubuntu 24.04.3 LTS (GNU/Linux 6.8.0-1039-aws x86_64)
ubuntu@ip-10-0-1-147:~$
```

**재발 방지** — 이 장애는 SSH 소스를 `/32` 로 제한한 설계의 **정상적인 부작용**이다.
접속이 끊길 때마다 규칙을 넓히는 방향으로 대응하면 결국 `0.0.0.0/0` 이 되므로, 반대로 갱신 명령을 README 보안 설계 절에 기록해 재적용을 쉽게 만들었다.
네트워크를 바꿀 일이 잦다면 SSH 대신 Session Manager 를 쓰는 것이 근본 해법이다. 22 포트를 아예 닫을 수 있기 때문이다.

### SSH 접속 실패 요약

| 증상 | 원인 | 조치 |
|------|------|------|
| `Connection timed out` | 보안 그룹 22 포트의 소스가 현재 공인 IP 와 다름 | 위 Case 3 의 갱신 명령 실행 |
| `WARNING: UNPROTECTED PRIVATE KEY FILE` | 개인키 파일 권한이 소유자 외에 열려 있음 | `chmod 400 codyssey-key.pem` (Windows 는 속성 → 보안 → 고급에서 상속 차단 후 본인 계정만 남김) |
| `Permission denied (publickey)` | 로그인 계정 불일치 | Ubuntu AMI 는 `ubuntu`, Amazon Linux 는 `ec2-user` |
