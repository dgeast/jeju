# ☁️ GitHub 배포 및 Streamlit Cloud 연동 가이드
> 50개의 전문 분석 탭이 포함된 이 대시보드를 전 세계 어디서나 접속할 수 있도록 배포하는 방법입니다.

---

## 🚀 1. GitHub 저장소에 코드 업로드

### 1) GitHub 저장소 생성
1.  [GitHub](https://github.com)에 로그인합니다.
2.  우측 상단 `+` 버튼 -> **New repository** 클릭.
3.  Repository name 입력 (예: `sales-dashboard-legend`).
4.  Public(공개) 또는 Private(비공개) 선택 후 **Create repository** 클릭.

### 2) 코드 업로드 (터미널 명령어)
VS Code 터미널에서 아래 명령어를 순서대로 입력하세요.

```bash
# 1. Git 초기화
git init

# 2. 모든 파일 스테이징 (.gitignore에 있는 파일 제외됨)
git add .

# 3. 커밋 생성
git commit -m "Initial commit: Legendary Sales Dashboard (50 Tabs)"

# 4. 원격 저장소 연결 (GitHub에서 복사한 주소 사용)
# 예: git remote add origin https://github.com/사용자명/sales-dashboard-legend.git
git remote add origin <당신의_GITHUB_저장소_주소>

# 5. GitHub로 코드 푸시
git push -u origin master
```

---

## ☁️ 2. Streamlit Cloud 배포

### 1) 앱 생성
1.  [Streamlit Cloud](https://streamlit.io/cloud)에 접속하여 로그인(GitHub 계정 연동).
2.  **New app** 클릭.
3.  **Use existing repo** 선택.

### 2) 설정 입력
*   **Repository**: 방금 만든 저장소 선택 (`sales-dashboard-legend`)
*   **Branch**: `master` (또는 `main`)
*   **Main file path**: `app_sales.py`
*   **App URL**: 원하는 주소 입력 (선택 사항)

### 3) 배포 (Deploy)
*   **Deploy!** 버튼을 클릭합니다.
*   약 1~2분 후, 전 세계 어디서나 접속 가능한 대시보드가 열립니다! 🎉

---

## ⚠️ 주의사항 (백업 필수)
*   **데이터 파일**: `.gitignore` 설정 상 현재 `data/` 폴더 내의 CSV 파일도 함께 업로드되도록 설정되어 있습니다. (데모 실행을 위해)
*   만약 **실제 고객 데이터(개인정보)**가 포함된 경우라면, `data/` 폴더를 업로드하지 말고 Streamlit Cloud의 **Manage app -> Settings -> Secrets** 기능을 활용하거나, 데이터를 별도로 관리해야 합니다.
