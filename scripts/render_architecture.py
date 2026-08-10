"""docs/architecture.png 생성 스크립트.

구성이 바뀌면 상단 상수만 고치고 다시 실행한다.
    python scripts/render_architecture.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REGION = "ap-northeast-2 (Seoul)"
VPC_CIDR = "10.0.0.0/16"
SUBNET_CIDR = "10.0.1.0/24"
AZ = "ap-northeast-2a"
INSTANCE = "t2.micro / Ubuntu 24.04 LTS"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "architecture.png"

NAVY = "#232f3e"
ORANGE = "#ed7100"
BLUE = "#1a73c7"
GREEN = "#2e7d32"
RED = "#c1272d"
GRAY = "#5f6b7a"

# 트래픽이 지나는 수직 경로 (요청 / 응답)
X_REQ, X_RES = 38, 44


def box(ax, xy, w, h, *, edge, face="white", style="solid", lw=1.4):
    ax.add_patch(
        FancyBboxPatch(
            xy, w, h,
            boxstyle="round,pad=0,rounding_size=0.8",
            linewidth=lw, edgecolor=edge, facecolor=face, linestyle=style, zorder=1,
        )
    )


def title(ax, x, y, text, *, color=NAVY, size=9.5, ha="left"):
    ax.text(x, y, text, color=color, fontsize=size, fontweight="bold",
            ha=ha, va="top", zorder=3)


def body(ax, x, y, text, *, color=NAVY, size=8.2, ha="left"):
    ax.text(x, y, text, color=color, fontsize=size, ha=ha, va="top",
            linespacing=1.7, zorder=3)


def arrow(ax, x, y0, y1, *, color):
    ax.add_patch(
        FancyArrowPatch(
            (x, y0), (x, y1), arrowstyle="-|>", mutation_scale=15,
            linewidth=1.7, color=color, shrinkA=0, shrinkB=0, zorder=4,
        )
    )


def main():
    plt.rcParams["font.sans-serif"] = ["Malgun Gothic", "AppleGothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(11.5, 8.5), dpi=160)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ── 외부 클라이언트 ─────────────────────────────────────────────
    box(ax, (24, 92), 36, 7, edge=GRAY)
    title(ax, 26, 97.7, "Client")
    body(ax, 26, 94.9, "브라우저 / curl  ·  출발지: 학습자 공인 IP", color=GRAY)

    ax.text(35, 85, "Internet", color=GRAY, fontsize=10,
            fontweight="bold", ha="right", va="center", zorder=3)

    # ── AWS Cloud ──────────────────────────────────────────────────
    box(ax, (3, 3), 95, 77, edge=NAVY, face="#f6f8fa", lw=1.7)
    title(ax, 5.5, 78.4, f"AWS Cloud  ·  {REGION}")

    # IAM (계정 단위 리소스이므로 VPC 밖에 표기)
    box(ax, (60, 63), 33, 12, edge=GRAY, style="dashed", lw=1.2)
    title(ax, 62, 73.6, "IAM User  ·  codyssey-infra", color=GRAY, size=9)
    body(ax, 62, 70.4, "EC2 / VPC / SG 구성 권한만 부여\nAdministratorAccess 미부여",
         color=GRAY, size=7.8)

    # Internet Gateway
    box(ax, (30, 66), 24, 8, edge=ORANGE, lw=1.8)
    title(ax, 42, 72.6, "Internet Gateway", color=ORANGE, ha="center")
    body(ax, 42, 69.6, "codyssey-igw", ha="center")

    # ── VPC ────────────────────────────────────────────────────────
    box(ax, (6, 8), 90, 54, edge=BLUE, lw=1.6)
    title(ax, 8.5, 60.6, f"VPC  ·  codyssey-vpc  ·  {VPC_CIDR}", color=BLUE)

    # Route Table
    box(ax, (60, 38), 33, 20, edge=BLUE, face="#edf4fb", style="dashed", lw=1.2)
    title(ax, 62, 56.6, "② Route Table (public)", color=BLUE, size=9)
    body(ax, 62, 53.2, f"{VPC_CIDR}   → local\n0.0.0.0/0     → codyssey-igw")
    body(ax, 62, 45.6, "연결 서브넷: codyssey-public-subnet-a\n아웃바운드도 이 경로를 사용",
         color=GRAY, size=7.8)

    # Public Subnet
    box(ax, (9, 12), 44, 42, edge=GREEN, face="#f3f9f2", lw=1.5)
    title(ax, 11, 52.6, f"Public Subnet  ·  {SUBNET_CIDR}", color=GREEN, size=9)
    body(ax, 11, 49.4, f"{AZ}  ·  퍼블릭 IPv4 자동 할당 ON", color=GRAY, size=7.8)

    # Security Group
    box(ax, (12, 15), 38, 30, edge=RED, style="dashed", lw=1.3)
    title(ax, 14, 43.6, "Security Group  codyssey-web-sg", color=RED, size=9)

    # EC2
    box(ax, (15, 18), 32, 22, edge=ORANGE, face="#fff8ee", lw=1.6)
    title(ax, 17, 38.6, "EC2  ·  codyssey-web", color=ORANGE, size=9)
    body(
        ax, 17, 35.4,
        f"{INSTANCE}\n"
        "EBS gp3 8 GiB\n"
        "Nginx :80  —  /  ·  /health\n"
        "Private IPv4  10.0.1.x\n"
        "Public IPv4   자동 할당",
    )

    # 보안 그룹 규칙
    box(ax, (60, 12), 33, 22, edge=RED, face="#fdf2f2", style="dashed", lw=1.2)
    title(ax, 62, 32.6, "③ Security Group 규칙", color=RED, size=9)
    body(
        ax, 62, 29.2,
        "IN   80/tcp  ←  0.0.0.0/0\n"
        "IN   22/tcp  ←  <내 공인 IP>/32\n"
        "OUT  all       →  0.0.0.0/0",
    )
    body(ax, 62, 19.4, "0.0.0.0/0 에 대한 0-65535 전체 허용\n규칙은 생성하지 않음",
         color=RED, size=7.8)

    # ── 트래픽 흐름 ─────────────────────────────────────────────────
    arrow(ax, X_REQ, 92, 74, color=BLUE)     # Client → IGW
    arrow(ax, X_REQ, 66, 40, color=BLUE)     # IGW → EC2
    arrow(ax, X_RES, 40, 66, color=GREEN)    # EC2 → IGW
    arrow(ax, X_RES, 74, 92, color=GREEN)    # IGW → Client

    ax.text(46.5, 87.5, "① HTTP :80 요청", color=BLUE, fontsize=8.5,
            ha="left", va="center", zorder=3)
    ax.text(46.5, 83, "④ 200 OK 응답", color=GREEN, fontsize=8.5,
            ha="left", va="center", zorder=3)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, bbox_inches="tight", facecolor="white")
    print(f"saved: {OUTPUT}")


if __name__ == "__main__":
    main()
