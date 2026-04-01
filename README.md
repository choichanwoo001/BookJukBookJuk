# Paige 문서

핵심 설계 문서는 아래 flow 문서를 참고해 주세요.

- `Paige_agent_flow_docs.md`: `ai/paigee/docs/Paigee_agent_flow_docs.md`
- `Paige_database_schema.md`: `ai/paigee/docs/Paigee_database_schema.md`
- API 전체 목록: `ai/paigee/docs/API_Index.md`
- 인증 API: `ai/paigee/docs/API_Auth.md`

## 웹캠 제스처 + 책 표지 인식 (ORB) 데모

코드·문서·`refs/` 참조 이미지는 **`book_recognition/`** 에 있습니다. 사용법은 [book_recognition/README.md](book_recognition/README.md) 를 참고하세요.

```bash
pip install -r requirements.txt
python -m book_recognition.register
python -m book_recognition.gesture_test
```
