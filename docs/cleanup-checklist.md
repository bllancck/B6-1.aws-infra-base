# AWS 리소스 정리 체크리스트

- 정리 일시: 2026-09-20
- 리전: `ap-northeast-2`
- 프로젝트 태그: `Project=codyssey-b6-1`
- 정리 방식: AWS CLI를 이용한 수동 삭제

---

## 1. 정리 목적

AWS 실습이 끝난 후 생성한 리소스를 그대로 두면 불필요한 비용이 발생할 수 있으므로,
실습에서 생성한 AWS 리소스를 의존 관계에 맞는 순서로 삭제했다.

삭제 전 다음 자료가 저장되어 있는지 확인했다.

- 외부 접속 성공 스크린샷
- 아키텍처 다이어그램
- README 외부 접속 검증 내용
- 트러블슈팅 기록

---

## 2. 삭제 순서

리소스 간 의존 관계를 고려해 다음 순서로 정리했다.

```text
EC2 종료
→ EBS 삭제 확인
→ Elastic IP 확인
→ Route Table 연결 해제 및 삭제
→ Internet Gateway Detach 및 삭제
→ Public Subnet 삭제
→ Security Group 삭제
→ VPC 삭제
→ AWS Key Pair 삭제
→ 로컬 Private Key 삭제
```

---

## 3. 정리 결과

| 항목 | 결과 | 비고 |
|---|---|---|
| EC2 인스턴스 | ✅ 종료 | 상태 `terminated` 확인 |
| EBS 볼륨 | ✅ 삭제 | `DeleteOnTermination=true`로 EC2 종료 시 자동 삭제 |
| Elastic IP | ✅ 없음 | 이번 실습에서는 생성하지 않음 |
| Route Table | ✅ 삭제 | Subnet 연결 해제 후 삭제 |
| Internet Gateway | ✅ 삭제 | VPC에서 Detach 후 삭제 |
| Public Subnet | ✅ 삭제 | 프로젝트 Subnet 삭제 |
| Security Group | ✅ 삭제 | `codyssey-web-sg` 삭제 |
| VPC | ✅ 삭제 | 프로젝트 VPC 삭제 |
| AWS Key Pair | ✅ 삭제 | `codyssey-key` 삭제 |
| 로컬 Private Key | ✅ 삭제 | `~/.ssh/codyssey-key.pem` 삭제 |
| NAT Gateway | 해당 없음 | 생성하지 않음 |
| ELB / ALB | 해당 없음 | 생성하지 않음 |
| RDS | 해당 없음 | 생성하지 않음 |

---

## 4. 주요 확인 방법

각 리소스는 삭제 후 AWS CLI의 조회 명령으로 다시 확인했다.

대부분의 리소스는 프로젝트 태그를 기준으로 조회했으며,
정상적으로 삭제된 경우 결과가 빈 배열 `[]`로 출력되는 것을 확인했다.

예:

```bash
aws ec2 describe-vpcs \
  --filters "Name=tag:Project,Values=codyssey-b6-1" \
  --query 'Vpcs[].VpcId' \
  --output json
```

정리 완료 시:

```json
[]
```

EC2는 종료 후 다음과 같이 상태가 표시되는 것을 확인했다.

```text
terminated
```

---

## 5. EBS 정리

EC2의 루트 EBS 볼륨은 생성 시 다음과 같이 설정했다.

```text
DeleteOnTermination=true
```

따라서 EC2를 종료하면서 루트 EBS도 함께 삭제되었다.

삭제 후 프로젝트 태그로 EBS를 조회했으며 남은 볼륨이 없음을 확인했다.

---

## 6. Elastic IP

이번 실습에서는 별도의 Elastic IP를 생성하지 않았다.

Public Subnet에서 EC2에 자동으로 할당된 Public IPv4 주소를 사용했기 때문에
별도로 Release할 Elastic IP는 없었다.

---

## 7. Key Pair 정리

EC2 SSH 접속에 사용한 AWS Key Pair:

```text
codyssey-key
```

를 AWS에서 삭제했다.

AWS Key Pair 삭제와 별개로 로컬 WSL에 저장되어 있던 Private Key:

```text
~/.ssh/codyssey-key.pem
```

도 더 이상 필요하지 않아 직접 삭제했다.

---

## 8. 최종 체크리스트

- [x] 외부 접속 성공 스크린샷 저장
- [x] 아키텍처 다이어그램 저장
- [x] 트러블슈팅 기록 저장
- [x] README 검증 내용 작성
- [x] EC2 종료
- [x] EBS 삭제 확인
- [x] Elastic IP 미사용 확인
- [x] Route Table 삭제
- [x] Internet Gateway Detach 및 삭제
- [x] Public Subnet 삭제
- [x] Security Group 삭제
- [x] VPC 삭제
- [x] AWS Key Pair 삭제
- [x] 로컬 Private Key 삭제
- [x] Billing Dashboard 최종 확인
