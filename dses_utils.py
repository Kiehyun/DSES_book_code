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


def check_and_install(packages_str: str, install: bool = True,
                      show_versions: bool = True) -> None:
    """packages_str에 적은 패키지를 점검하고, 없으면 설치한 뒤 버전을 출력한다.

    매개변수
        packages_str  : 쉼표로 구분한 패키지 목록 문자열(노트북의 packages_str 그대로 사용)
        install       : 미설치 패키지를 pip로 설치할지 여부(기본 True)
        show_versions : 설치된 버전 표를 출력할지 여부(기본 True)
    """
    pkgs = _split_packages(packages_str)
    print("─── 패키지 확인 및 설치 ───")
    for spec in pkgs:
        name = _base_name(spec)
        if name in ("version_information", "pip", "setuptools", "wheel"):
            continue
        mod = _PYPI_TO_IMPORT.get(name.lower(), name).split(".")[0]
        if importlib.util.find_spec(mod) is not None:
            print(f"  ✓ {name} 이미 설치됨")
            continue
        if not install:
            print(f"  ✗ {name} 미설치(install=False)")
            continue
        print(f"  · {name} 설치 중...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", spec],
                           check=True)
            print(f"  ✓ {name} 설치 완료")
        except Exception as exc:
            print(f"  ✗ {name} 설치 실패: {exc}")

    if show_versions:
        print("\n─── 설치된 버전 ───")
        print(f"  {'Python':22} {sys.version.split()[0]}")
        for spec in pkgs:
            name = _base_name(spec)
            if name in ("version_information", "pip", "setuptools", "wheel"):
                continue
            try:
                print(f"  {name:22} {_md.version(name)}")
            except Exception:
                print(f"  {name:22} (버전 확인 불가)")
    print("패키지 확인 완료\n")


def make_project_dir(name: str, base: str | Path = ".") -> Path:
    """프로젝트(자료 저장) 폴더를 만들고 경로를 반환한다(보통 name=노트북 파일명).

    이미 있으면 그대로 두고 경로만 돌려준다.
    """
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
