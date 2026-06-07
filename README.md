# DSES_book_code

지구과학 데이터 사이언스 노트북 공통 유틸리티(`dses_utils.py`).

## 코랩/주피터에서 사용

```python
import urllib.request, sys, os
URL = "https://raw.githubusercontent.com/guitar79/DSES_book_code/main/dses_utils.py"
if not os.path.exists("dses_utils.py"):
    urllib.request.urlretrieve(URL, "dses_utils.py")
import dses_utils as du

du.check_and_install("numpy, pandas, matplotlib")   # 필요한 모듈 점검/설치/버전표
PROJ = du.make_project_dir("내_프로젝트_폴더")        # 자료 저장 폴더 생성
du.download("https://.../data.csv", PROJ / "data.csv")  # 데이터 내려받기
du.save_figure(fig, PROJ / "result")                # result.pdf + result.png 저장
```

## 함수
- `check_and_install(packages_str, install=True, show_versions=True)`
- `make_project_dir(name, base=".")`
- `download(url, dest, overwrite=False)`
- `save_figure(fig, path_without_ext, formats=("pdf","png"), dpi=200)`
