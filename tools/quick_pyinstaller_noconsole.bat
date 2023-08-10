@rem taskarg: ${file}
@Echo off
SETLOCAL EnableDelayedExpansion




set INPATH=%~dp1
set INFILE=%~nx1
set INFILEBASE=%~n1
set ICON=%~dp0exe_icon.ico
pushd %INPATH%
mkdir %INPATH%pyinstaller_output_%INFILEBASE%

set PYTHONOPTIMIZE=1
pyinstaller --clean --noconfirm --log-level=INFO --onefile -c ^
-i %ICON% ^
-n %2 ^
--upx-dir %UPX_DIR% ^
--upx-exclude vcruntime140.dll ^
--upx-exclude ucrtbase.dll ^
--distpath %INPATH%pyinstaller_output_%INFILEBASE%/dist ^
--workpath %INPATH%pyinstaller_output_%INFILEBASE%/work ^
--specpath %INPATH%pyinstaller_output_%INFILEBASE%/spec ^
%INFILE%