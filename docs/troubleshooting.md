# 트러블슈팅 보고서

## WSL Ubuntu에서 AWS CLI 설치 실패

### 증상

WSL Ubuntu 환경에서 AWS CLI를 설치하기 위해 다음 명령을 실행했다.

```bash
sudo apt update
sudo apt install -y awscli
```

하지만 다음 오류가 발생하면서 설치되지 않았다.

```text
E: Package 'awscli' has no installation candidate
```

따라서 `aws` 명령을 사용할 수 없어 AWS 인프라 생성 작업을 시작할 수 없는 상태였다.

### 원인 가설

현재 사용 중인 Ubuntu 환경의 APT 패키지 저장소에서 설치 가능한 `awscli` 패키지를 제공하지 않는 것으로 추정했다.

AWS 계정이나 IAM 권한 문제가 아니라, AWS CLI 프로그램 자체가 아직 로컬 환경에 설치되지 않은 문제라고 판단했다.

### 검증

`apt update`는 정상적으로 수행됐지만 `apt install awscli`에서 패키지를 찾지 못했다.

또한 설치 전에는 다음 명령으로 정상적인 버전 정보를 확인할 수 없었다.

```bash
aws --version
```

아직 AWS API를 호출하기 전 단계에서 실패했으므로, AWS 권한 문제가 아닌 로컬 설치 문제임을 확인했다.

### 조치

APT를 통한 설치 대신 AWS CLI v2의 공식 Linux 설치 방식을 사용해 AWS CLI를 설치했다.

설치 후 다음 명령으로 정상 설치 여부를 확인했다.

```bash
aws --version
```

이후 다음 명령으로 AWS CLI 환경을 설정하고 기본 리전을 서울 리전으로 지정했다.

```bash
aws configure
```

```text
ap-northeast-2
```

### 결과

다음과 같이 AWS CLI 버전 정보가 정상적으로 출력됐다.

```text
aws-cli/2.36.49 Python/3.14.6 Linux/6.6.87.2-microsoft-standard-WSL2 script-exe/x86_64.ubuntu.24
```

마지막으로 다음 명령을 실행했다.

```bash
aws sts get-caller-identity
```

IAM 사용자 `codyssey-infra`로 정상 인증되는 것을 확인했고, 이후 AWS CLI를 이용해 VPC, Subnet, Internet Gateway, Security Group, EC2 등의 리소스를 생성할 수 있었다.

### 재발 방지

WSL 또는 Ubuntu 환경에서 `apt install awscli`가 항상 가능한 것은 아니므로, 패키지를 찾지 못하는 경우 같은 명령을 반복하지 않는다.

먼저 다음 명령으로 AWS CLI 설치 여부를 확인한다.

```bash
aws --version
```

설치돼 있지 않고 APT에서 패키지를 제공하지 않는 경우에는 AWS CLI v2의 공식 Linux 설치 방법을 사용한다.

설치 후에는 AWS 리소스를 생성하기 전에 다음 두 명령을 먼저 확인한다.

```bash
aws --version
aws sts get-caller-identity
```

이를 통해 AWS CLI 자체의 설치 문제와 AWS 인증 문제를 구분할 수 있다.
