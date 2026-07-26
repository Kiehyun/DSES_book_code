"""지구과학 데이터 사이언스 — 노트북 공통 유틸리티.

각 노트북에서 반복되는 코드를 줄이기 위한 함수 모음입니다.
노트북 맨 앞에서 아래처럼 불러와 사용하세요(별도 설치 불필요, 표준 라이브러리 기반).

    import sys
    sys.path.append("code")          # 이 파일이 있는 폴더를 경로에 추가
    import dses_utils as du

    du.check_and_install("numpy, pandas, matplotlib, astropy")  # 필요한 모듈 점검/설치/버전표
    PROJ = du.make_project_dir("03_01_Astronomical_time")        # 저장 폴더(보통 노트북 파일명) 생성
    du.download("https://.../data.csv", PROJ / "data.csv")       # 데이터 내려받기
    du.save_figure(fig, PROJ / "result")                         # result.pdf + result.png 동시 저장

함수 목록
    check_and_install(packages_str, install=True, show_versions=True)
    make_project_dir(name, base=".")
    download(url, dest, overwrite=False)
    list_files(directory, ext="*", pattern=None, recursive=False, show=True)
    preview_text(path, n=20, encoding=None, number=True)
    save_figure(fig, path_without_ext, formats=("pdf", "png"), dpi=200)
"""
from __future__ import annotations

import importlib
import importlib.metadata as _md
import subprocess
import sys
import urllib.request
from pathlib import Path

# 설치(PyPI) 이름과 import 이름이 다른 패키지 매핑.
_PYPI_TO_IMPORT = {
    "pillow": "PIL", "opencv-python": "cv2", "scikit-image": "skimage",
    "scikit-learn": "sklearn", "beautifulsoup4": "bs4", "pyyaml": "yaml",
    "python-dateutil": "dateutil", "netcdf4": "netCDF4", "pyserial": "serial",
    "gdal": "osgeo", "basemap": "mpl_toolkits.basemap",
}


def _split_packages(packages_str: str) -> list[str]:
    """'numpy, pandas==2.0, matplotlib' -> ['numpy', 'pandas==2.0', 'matplotlib']."""
    return [p.strip() for p in packages_str.replace("\n", ",").split(",") if p.strip()]


def _base_name(pkg: str) -> str:
    """버전 지정(==, >= 등)을 떼어낸 설치 이름."""
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
        if sep in pkg:
            pkg = pkg.split(sep)[0]
    return pkg.strip()


def _module_version(name: str) -> str:
    """설치명 또는 import명으로 버전을 최대한 알아낸다.

    1) 배포 메타데이터(importlib.metadata) → 2) 모듈 import 후 __version__ 순으로 시도.
    """
    try:
        return _md.version(name)
    except Exception:
        pass
    mod = _PYPI_TO_IMPORT.get(name.lower(), name).split(".")[0]
    try:
        m = importlib.import_module(mod)
        return getattr(m, "__version__", None) or str(getattr(m, "version", "")) or "버전 미상"
    except Exception:
        return "확인 불가"


def check_and_install(packages_str: str, install: bool = True,
                      show_versions: bool = True) -> None:
    """packages_str에 적은 패키지를 점검하고, 없으면 설치한 뒤 버전을 출력한다.

    매개변수
        packages_str  : 쉼표로 구분한 패키지 목록 문자열(노트북의 packages_str 그대로 사용)
        install       : 미설치 패키지를 pip로 설치할지 여부(기본 True)
        show_versions : 설치된 버전 표를 출력할지 여부(기본 True)
    """
    pkgs = _split_packages(packages_str)
    # 패키지 점검/설치는 '조용히' 수행한다(✓/·/✗ 진행 로그를 출력하지 않음).
    # 설치 결과는 아래 '버전 정보' 표로 확인할 수 있으며, 설치에 실패한 패키지는
    # 표에서 '확인 불가'로 표시된다.
    for spec in pkgs:
        name = _base_name(spec)
        if name in ("version_information", "pip", "setuptools", "wheel"):
            continue
        mod = _PYPI_TO_IMPORT.get(name.lower(), name).split(".")[0]
        if importlib.util.find_spec(mod) is not None:
            continue
        if not install:
            continue
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", spec],
                           check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    if show_versions:
        import platform
        print("─── 버전 정보 ───")
        print(f"  {'Python':24} {platform.python_version()}")
        print(f"  {'OS':24} {platform.platform()}")
        for spec in pkgs:
            name = _base_name(spec)
            if name in ("pip", "setuptools", "wheel"):
                continue
            print(f"  {name:24} {_module_version(name)}")
    print("패키지 확인 완료\n")


def set_korean_font() -> None:
    """matplotlib에서 한글이 깨지지 않도록 OS별 한글 글꼴과 마이너스 기호를 설정한다.

    Windows는 'Malgun Gothic', macOS는 'AppleGothic', 그 외(리눅스)는 'NanumGothic'을
    우선 적용하고, 글꼴이 없을 때를 대비해 'DejaVu Sans'를 함께 지정한다. 각 노트북에
    같은 코드를 반복해 넣지 않도록 이 함수 하나로 모은다.

        import dses_utils as du
        du.set_korean_font()
    """
    import platform
    import matplotlib.pyplot as plt

    system = platform.system()
    if system == "Windows":
        plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei", "DejaVu Sans"]
    elif system == "Darwin":  # macOS
        plt.rcParams["font.family"] = ["AppleGothic", "Helvetica", "DejaVu Sans"]
    else:  # Linux 등
        plt.rcParams["font.family"] = ["NanumGothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지


def current_notebook_name():
    """현재 실행 중인 노트북의 파일명(확장자 제외)을 자동으로 알아낸다.

    환경별로 방법이 달라 순서대로 시도하고, 모두 실패하면 None을 반환한다.
      1) VS Code: 노트북 네임스페이스의 전역 변수 __vsc_ipynb_file__
      2) JupyterLab/Notebook: ipynbname 패키지(설치돼 있으면)
      3) 자동 실행(책 빌드): 환경변수 DSES_NOTEBOOK_NAME
      4) Colab: COLAB_NOTEBOOK_ID 등은 파일명을 주지 않으므로 생략
    """
    import os
    # 1) VS Code — 노트북 사용자 네임스페이스에 전체 경로가 들어 있다.
    try:
        from IPython import get_ipython
        ns = get_ipython().user_ns
        p = ns.get("__vsc_ipynb_file__")
        if p:
            return os.path.splitext(os.path.basename(p))[0]
    except Exception:
        pass
    # 2) ipynbname (classic Jupyter / JupyterLab)
    try:
        import ipynbname
        return ipynbname.name()
    except Exception:
        pass
    # 3) 책 빌드용 일괄 실행(scripts/execute_notebooks.py)에서는 창이 없어 1·2가 모두
    #    실패한다. 실행기가 노트북 이름을 이 환경변수에 넣어 주므로 그것을 쓴다.
    name = os.environ.get("DSES_NOTEBOOK_NAME")
    if name:
        return os.path.splitext(os.path.basename(name))[0]
    return None


def make_project_dir(name=None, base: str | Path = ".") -> Path:
    """프로젝트(자료 저장) 폴더를 만들고 경로를 반환한다.

    name 을 생략(None)하면 현재 노트북 파일명(확장자 제외)을 자동으로 사용한다.
    자동 인식에 실패하면 알기 쉬운 오류를 내므로, 그때는 이름을 직접 지정한다.
    이미 있으면 그대로 두고 경로만 돌려준다.

        PROJ = du.make_project_dir()                 # 노트북 파일명 자동
        PROJ = du.make_project_dir("내_폴더이름")     # 직접 지정
    """
    if name is None:
        name = current_notebook_name()
        if not name:
            raise ValueError(
                "노트북 파일명을 자동으로 알 수 없습니다. "
                "make_project_dir(\"폴더이름\") 처럼 이름을 직접 지정하세요."
            )
    path = Path(base) / name
    if path.exists():
        print(f"{path} (이미 있음)")
    else:
        path.mkdir(parents=True, exist_ok=True)
        print(f"{path} 생성됨")
    return path


def download(url: str, dest: str | Path, overwrite: bool = False) -> Path:
    """웹에서 파일을 내려받아 dest 경로에 저장한다(wget 설치 불필요).

    dest가 이미 있고 overwrite=False면 다시 받지 않는다(큰 데이터 재다운로드 방지).
    requests가 설치돼 있으면 스트리밍으로 받고(구글 드라이브/리다이렉트에 강함),
    없으면 표준 라이브러리 urllib로 받는다. 노트북마다 download_with_requests 같은
    함수를 따로 정의하지 않아도 되도록 이 함수 하나로 모은다.

        du.download("https://.../data.csv", PROJ / "data.csv")
        du.download(url, PROJ / "img.fit", overwrite=True)   # 항상 새로 받기
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"{dest} (이미 있음 — 건너뜀)")
        return dest
    try:
        import requests  # 있으면 스트리밍 다운로드 사용
        with requests.get(url, stream=True, timeout=120,
                          headers={"User-Agent": "Mozilla/5.0"}) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
    except ImportError:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(dest, "wb") as fh:
            fh.write(resp.read())
    print(f"{dest} 다운로드 완료")
    return dest


def list_files(directory: str | Path, ext: str | list[str] = "*",
               pattern: str | None = None,
               recursive: bool = False, show: bool = True) -> list[Path]:
    """폴더 안의 파일을 확장자로 추려 정렬된 목록(list[Path])으로 돌려준다.

    각 노트북에서 반복하던 아래 코드를 한 줄로 줄이기 위한 함수다.

        fpaths = sorted(list(PROJ.glob('*.csv')))
        print(f"fpaths: {fpaths}")
        print(f"len(fpaths): {len(fpaths)}")

    매개변수
        directory : 찾을 폴더(보통 make_project_dir로 만든 PROJ)
        ext       : 확장자. 'csv', '.csv', '*.csv' 모두 같게 처리한다.
                    '*'(기본)이면 모든 파일. 'fit*'처럼 뒤에 와일드카드를 붙여도 되고,
                    ['csv', 'txt']처럼 목록으로 주면 여러 확장자를 한 번에 모은다.
        pattern   : 확장자만으로 표현하기 어려운 경우(접두어 등) glob 패턴을 직접 지정.
                    예) 'M35*.fit*', '*bias-e*.fit*'. 주면 ext는 무시된다.
        recursive : True면 하위 폴더까지 재귀(rglob)로 찾는다(기본 False).
        show      : True면 찾은 파일 목록과 개수를 화면에 출력한다(기본 True).

        fpaths = du.list_files(PROJ, "csv")              # PROJ 안의 *.csv
        fpaths = du.list_files(PROJ, "fit*")             # *.fit, *.fits ...
        fpaths = du.list_files(PROJ, ["csv", "txt"])     # 여러 확장자
        fpaths = du.list_files(PROJ, pattern="M35*.fit*")  # 접두어가 있는 패턴
    """
    directory = Path(directory)
    globber = directory.rglob if recursive else directory.glob

    if pattern is not None:
        patterns = [pattern]
    else:
        exts = [ext] if isinstance(ext, str) else list(ext)
        patterns = []
        for e in exts:
            # 'csv' / '.csv' / '*.csv' → 'csv' 로 정규화한 뒤 '*.csv' 패턴을 만든다.
            suffix = e.lstrip("*").lstrip(".").strip()
            patterns.append("*" if suffix in ("", "*") else f"*.{suffix}")

    seen: set = set()
    fpaths: list[Path] = []
    for pat in patterns:
        for p in globber(pat):
            if p.is_file() and p not in seen:
                seen.add(p)
                fpaths.append(p)
    fpaths.sort()
    if show:
        shown = pattern if pattern is not None else ", ".join(patterns)
        print(f"─── {directory}/{shown} (총 {len(fpaths)}개) ───")
        for p in fpaths:
            print(f"  {p}")
    return fpaths


def preview_text(path: str | Path, n: int = 20,
                 encoding: str | list[str] | None = None,
                 number: bool = True) -> list[str]:
    """텍스트 파일의 앞부분 n줄을 줄 번호와 함께 출력한다(OS 무관 — !head 대체).

    셸 명령 `!head -n N 파일` 은 Windows에서 동작하지 않으므로, 어디서나 같은
    결과를 얻도록 이 함수로 모은다. 한글 파일이 깨지지 않도록 여러 인코딩
    (utf-8 → cp949 → euc-kr)을 차례로 시도하며, 출력한 줄들의 리스트를 반환한다.

    매개변수
        path     : 미리볼 파일 경로(보통 fpaths[0])
        n        : 출력할 줄 수(기본 20)
        encoding : 시도할 인코딩. None(기본)이면 utf-8/cp949/euc-kr을 차례로 시도.
                   문자열 하나("utf-8") 또는 목록(["utf-8", "cp949"])도 받는다.
        number   : True면 줄 앞에 줄 번호를 붙여 출력한다(기본 True).

        du.preview_text(PROJ / "data.csv")          # 앞 20줄(인코딩 자동)
        du.preview_text(fpaths[0], n=10)            # 앞 10줄
    """
    path = Path(path)
    if encoding is None:
        encodings = ["utf-8", "cp949", "euc-kr"]
    elif isinstance(encoding, str):
        encodings = [encoding]
    else:
        encodings = list(encoding)

    lines: list[str] = []
    used: str | None = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                buf = []
                for i, line in enumerate(f):
                    if i >= n:
                        break
                    buf.append(line.rstrip("\n"))
            lines, used = buf, enc
            break
        except UnicodeDecodeError:
            continue

    if used is None:
        print(f"지원한 인코딩({', '.join(encodings)})으로 파일을 읽지 못했습니다.")
        return lines

    print(f"─── {path.name} (첫 {len(lines)}줄, 인코딩: {used}) ───")
    for i, ln in enumerate(lines, 1):
        print(f"{i:3d}: {ln}" if number else ln)
    return lines


def save_figure(fig, path_without_ext: str | Path,
                formats=("pdf", "png"), dpi: int = 200) -> list[Path]:
    """그림을 여러 형식(기본 pdf+png)으로 한 번에 저장한다.

    fig 는 matplotlib Figure 객체이며, 확장자 없는 경로를 주면 형식별로 붙여 저장한다.
    벡터(pdf)와 래스터(png)를 함께 남겨, 인쇄(책)와 화면 미리보기에 모두 쓰기 좋다.
    """
    base = Path(path_without_ext)
    base.parent.mkdir(parents=True, exist_ok=True)
    saved = []
    for ext in formats:
        out = base.with_suffix(f".{ext}")
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        saved.append(out)
        print(f"{out} 저장됨")
    return saved
