# 리소스 정리 체크리스트

실습이 끝나면 `scripts/cleanup.sh` 가 생성 역순으로 리소스를 삭제한다.
이 문서는 그 결과를 **조회 명령 출력으로 검증**한 기록이다. 콘솔 화면만으로는 "안 보이는 것"과 "없는 것"을 구분하기 어렵기 때문이다.

- 정리 일시: **2026-08-22 19:30 ~ 19:31 KST**
- 실행: `bash scripts/cleanup.sh`

---

## 1. 삭제 순서

의존 관계가 있어 순서를 지켜야 한다. 앞 단계가 남아 있으면 뒤 단계는 `DependencyViolation` 으로 실패한다.

```
EC2 종료 → Elastic IP 릴리스 → 잔여 EBS 삭제 → 라우트 테이블 연결 해제·삭제
        → IGW detach·삭제 → 서브넷 삭제 → 보안 그룹 삭제 → VPC 삭제 → 키페어 삭제
```

## 2. 정리 결과

`aws ec2 <명령> --filters Name=tag:Project,Values=codyssey-b6-1` 으로 확인했다.
EC2 를 제외한 모든 항목은 **출력이 비어 있어야** 정리 완료다.

| # | 자원 | 리소스 | 확인 명령 (`aws ec2 …`) | 기대 결과 | 확인 |
|:-:|------|--------|--------------------------|-----------|:----:|
| 1 | EC2 인스턴스 | `i-03bc357db0b1ceaca` | `describe-instances --query 'Reservations[].Instances[].[InstanceId,State.Name]'` | `terminated` | ☑ |
| 2 | EBS 볼륨 | DeleteOnTermination 적용 | `describe-volumes --query 'Volumes[].VolumeId'` | 빈 출력 | ☑ |
| 3 | Elastic IP | (할당하지 않음) | `describe-addresses --query 'Addresses[].PublicIp'` | 빈 출력 | ☑ |
| 4 | 라우트 테이블 | `rtb-023d5a4b9a84280ca` | `describe-route-tables --query 'RouteTables[].RouteTableId'` | 빈 출력 | ☑ |
| 5 | Internet Gateway | `igw-05bd1f5a737f67d35` | `describe-internet-gateways --query 'InternetGateways[].InternetGatewayId'` | 빈 출력 | ☑ |
| 6 | 서브넷 | `subnet-05222c94e3865cfef` | `describe-subnets --query 'Subnets[].SubnetId'` | 빈 출력 | ☑ |
| 7 | 보안 그룹 | `sg-05b67dd8ecc6e9c67` | `describe-security-groups --query 'SecurityGroups[].GroupId'` | 빈 출력 | ☑ |
| 8 | VPC | `vpc-0fb9fd469e22b36cc` | `describe-vpcs --query 'Vpcs[].VpcId'` | 빈 출력 | ☑ |
| 9 | 키페어 | `codyssey-key` | `describe-key-pairs --key-names codyssey-key` | `InvalidKeyPair.NotFound` | ☑ |

생성하지 않았으므로 점검 대상이 아닌 항목: **NAT Gateway, ELB/ALB, RDS**.
NAT Gateway 와 ALB 는 프리티어가 없어 시간당 과금되므로, 이번 구성에서는 아웃바운드를 IGW 로만 처리했다.

### 실행 기록

```console
$ bash scripts/cleanup.sh

[19:30:44] 1. EC2 인스턴스 종료
  terminate 요청: i-03bc357db0b1ceaca — terminated 대기
  종료 완료

[19:31:17] 2. Elastic IP 릴리스
  할당된 Elastic IP 없음

[19:31:17] 3. 잔여 EBS 볼륨 삭제
  미사용 볼륨 없음 (DeleteOnTermination 으로 함께 삭제됨)

[19:31:18] 4. 라우트 테이블 연결 해제 및 삭제
  disassociated rtbassoc-009a8bee93f57685c
  deleted rtb-023d5a4b9a84280ca

[19:31:21] 5. 인터넷 게이트웨이 detach 및 삭제
  detached igw-05bd1f5a737f67d35 ← vpc-0fb9fd469e22b36cc
  deleted igw-05bd1f5a737f67d35

[19:31:25] 6. 서브넷 삭제
  deleted subnet-05222c94e3865cfef

[19:31:26] 7. 보안 그룹 삭제
  deleted sg-05b67dd8ecc6e9c67

[19:31:28] 8. VPC 삭제
  deleted vpc-0fb9fd469e22b36cc

[19:31:30] 9. 키페어
  deleted codyssey-key
  로컬 개인키는 직접 삭제: /home/byjol4324/.ssh/codyssey-key.pem

[19:31:32] 남은 리소스 확인
  instances                        i-03bc357db0b1ceaca terminated
  volumes
  addresses
  internet-gateways
  subnets
  route-tables
  security-groups
  vpcs
```

`instances` 만 `terminated` 로 남고 나머지는 모두 비어 있다.
종료된 인스턴스 기록은 약 1시간 후 목록에서 사라지며, 종료 시점부터 과금되지 않는다.

## 3. 과금 확인

Billing and Cost Management → Bills 에서 당월 청구액을 확인했다.

최종 확인 시 Billing 대시보드에서 당월 비용과 예상 비용을 직접 확인한다.

## 4. 놓치기 쉬운 과금 항목

| 항목 | 왜 남는가 | 결과 |
|------|-----------|------|
| Elastic IP | 인스턴스를 종료하면 **연결이 해제될 뿐 할당은 유지**된다 | 미연결 EIP 는 시간당 과금 |
| EBS 볼륨 | `DeleteOnTermination=false` 로 만들면 인스턴스만 사라진다 | 볼륨 용량만큼 계속 과금 |
| 스냅샷 / AMI | 인스턴스·볼륨 삭제와 무관하게 남는다 | 스냅샷 스토리지 과금 |
| 다른 리전 리소스 | 콘솔이 한 리전만 보여준다 | 눈에 안 띈 채 과금 |

이번 구성은 루트 볼륨을 `DeleteOnTermination=true` 로 만들어 2번을 구조적으로 차단했고,
Elastic IP 는 아예 할당하지 않고 서브넷의 퍼블릭 IPv4 자동 할당을 사용해 1번을 회피했다.
