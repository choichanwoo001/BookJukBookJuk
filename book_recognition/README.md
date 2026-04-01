# 웹캠 제스처 + 책 표지 인식 (ORB) + 쇼핑 리스트

서점 웹캠으로 **손 제스처**를 인식하고, **미리 등록한 표지 이미지**와 **ORB 특징 매칭**으로 책을 식별한 뒤 **알라딘 Open API**로 메타데이터를 붙여 **인메모리 쇼핑 리스트**에 담는 실험용 데모입니다.

모든 스크립트·`refs/`는 **`book_recognition/`** 폴더 안에 있습니다.

| 파일 | 역할 |
|------|------|
| `register.py` | 표지 웹캠 촬영 → `refs/`에 참조 이미지 저장 |
| `gesture_test.py` | MediaPipe 손 제스처 + 쇼핑 리스트 UI |
| `book_identifier.py` | ORB 매칭 + 알라딘 검색 |
| `shopping_list.py` | 리스트 추가/제거/표시 |
| `refs/` | 책마다 1장의 참조 이미지 (jpg/png) |

**GitHub:** `refs/` 안의 이미지 파일은 저장소에 올리지 않습니다(루트 `.gitignore`). 저장소에는 `refs/.gitkeep`만 두고, 클론 후 `register.py`로 로컬에서 표지를 등록하면 됩니다.

---

## 사전 요구 사항

- Python 3.10+
- 웹캠
- (선택) 알라딘 TTB 키 — 없으면 코드에 있는 기본 키로 시도하거나, 환경변수 `ALADIN_TTB_KEY` 설정

---

## 설치

**저장소 루트**에서 (상위 `requirements.txt`):

```bash
pip install -r requirements.txt
```

주요 패키지: `opencv-python`, `numpy`, `mediapipe`, `requests`

---

## 환경 변수 (선택)

`python-dotenv`는 사용하지 않습니다. 터미널에서 직접 설정하세요.

```bash
export ALADIN_TTB_KEY=your_aladin_ttb_key
```

프로젝트 루트 `.env.example` 참고: `ALADIN_TTB_KEY` 만 사용합니다.

---

## 실행 방법

**저장소 루트**에서 모듈로 실행하는 방식을 권장합니다.

### 1. 책 표지 등록

등록할 책마다 **참조 이미지 1장**이 필요합니다.

```bash
# 저장소 루트에서
python -m book_recognition.register
```

또는 이 폴더로 이동 후:

```bash
cd book_recognition
python register.py
```

- 화면 중앙 가이드 안에 표지를 맞춘 뒤 **스페이스바**로 캡처
- 터미널에 `책 제목 입력:` → 제목 입력 → `refs/{제목}.jpg` 로 저장
- **q** 로 종료

### 2. 제스처 데모

```bash
# 저장소 루트에서
python -m book_recognition.gesture_test
```

또는:

```bash
cd book_recognition
python gesture_test.py
```

- **엄지 업 (thumbs_up)** 확정 시: 현재 프레임으로 책 식별 → 리스트 추가  
- **엄지 다운 (thumbs_down)** 확정 시: 식별 후 리스트에서 제거  
- 창 포커스일 때 **q** 로 종료  

MediaPipe 손 모델은 `book_recognition/.models/hand_landmarker.task` 에 캐시됩니다.

### 3. 동작 확인

- `refs/` 가 비어 있으면 ORB 매칭 대상이 없습니다.
- 터미널에 `[ORB] {파일명스템}: {매칭수}개` 가 나오면 ORB가 제목(파일 기준)을 고른 것입니다.
- 알라딘 검색이 실패해도 ORB 제목으로 최소 정보는 리스트에 넣을 수 있습니다.

---

## 기술 구성 요약

| 구분 | 기술 | 역할 |
|------|------|------|
| 손 추적 | **MediaPipe Tasks** `HandLandmarker` (VIDEO) | 랜드마크 기반 제스처 분류 |
| 책 식별 | **OpenCV ORB** + **BFMatcher** (Hamming, cross-check) | `refs/` 참조 이미지와 현재 프레임 매칭 |
| 메타데이터 | **알라딘 TTB** `ItemSearch` (KR) | 제목 검색으로 표지·저자·ISBN·가격 보강 |
| 리스트 | 인메모리 Python 클래스 | ISBN 없을 때는 제목 기준 중복/삭제 |

---

## 기술적 의의

1. **재현 가능한 시연**: OCR·클라우드 비전 없이 **로컬 ORB**로 등록된 책 집합 안에서 식별 가능합니다.
2. **트레이드오프**: 책마다 사전 등록 필요, 조명·각도에 민감. 서점 전체 SKU 자동 커버는 어렵습니다.
3. **파이프라인**: 제스처 → 비전(ORB) → 북 API → 리스트까지 **엔드투엔드 프로토타입**으로 설명 가능합니다.

---

## 한계 및 향후 확장

- `refs/` + SQLite로 메타·경로 관리  
- ORB 대신 딥 임베딩으로 견고도 향상  

---

## 라이선스·API

- 알라딘 TTB: [알라딘 오픈 API](https://www.aladin.co.kr/ttb/wblog_2008.aspx) 약관 준수.

---

## 디렉터리 구조

```
book_recognition/
  __init__.py
  README.md          ← 이 문서
  register.py
  gesture_test.py
  book_identifier.py
  shopping_list.py
  refs/              # 참조 표지 이미지 (이미지는 .gitignore — 로컬 전용)
  .models/           # gesture_test 실행 시 hand_landmarker.task (자동 생성)
```

저장소 루트에는 `requirements.txt`, `.env.example` 등 프로젝트 공통 파일만 두고, **책 인식 데모는 이 폴더만 보면 됩니다.**
