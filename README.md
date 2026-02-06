# 🍊 제주 농산품 판매 분석 대시보드

이 프로젝트는 제주 농산품의 판매 데이터를 분석하고 경영 전략을 수립하기 위한 Streamlit 기반의 인터랙티브 대시보드입니다.

## 🚀 주요 기능
- **매출 성과 분석**: 일자별/요일별 매출 추이 및 수익 분석
- **셀러 심층 분석**: 셀러별 성과 지표(매출, 이익률, 재구매율) 및 유입 채널 히트맵 통합 분석
- **구매 패턴 분석**: 요일/시간별 골든타임 시각화 및 마케팅 인사이트 제공
- **경영 전략 보고서**: 데이터 기반의 마케팅 전략 및 EDA 분석 리포트 연동
- **지능형 타겟팅**: 상위 지역 페르소나 및 고객 재구매 패턴 분석

## 🛠 설치 및 실행 방법

### 1. 레포지토리 클론
```bash
git clone https://github.com/사용자아이디/레포지토리명.git
cd 레포지토리명
```

### 2. 가상환경 설정 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 4. 대시보드 실행
```bash
streamlit run app_dashboard.py
```

## 📂 디렉토리 구조
- `app_dashboard.py`: 메인 대시보드 애플리케이션
- `data/`: 전처리된 데이터 파일 (`preprocessed_data.csv`)
- `docs/`: 마케팅 전략 및 EDA 분석 보고서
- `requirements.txt`: 배포 및 실행에 필요한 라이브러리 목록
- `.gitignore`: Git 제외 파일 설정

## ☁️ 배포 안내
본 대시보드는 **Streamlit Cloud**를 통해 간편하게 배포할 수 있습니다. 자세한 내용은 `docs/deployment/github_guide.md`를 참고해 주세요.
