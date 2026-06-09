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
      3) Colab: COLAB_NOTEBOOK_ID 등은 파일명을 주지 않으므로 생략
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
    """urllib.request로 파일을 내려받는다(wget 설치 불필요).

    dest가 이미 있고 overwrite=False면 다시 받지 않는다.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"{dest} (이미 있음 — 건너뜀)")
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as fh:
        fh.write(resp.read())
    print(f"{dest} 다운로드 완료")
    return dest


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
