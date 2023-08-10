@Echo off
set OLDHOME_FOLDER=%~dp0
pushd %OLDHOME_FOLDER%
call ..\.venv\Scripts\activate


call pip freeze ^
-r venv_setup_settings\required_misc.txt ^
-r venv_setup_settings\required_gui.txt ^
--exclude-editable ^
--exclude cairosvg ^
--exclude dateparser ^
--exclude https://github.com/pyinstaller/pyinstaller/tarball/develop ^
--exclude invoke ^
--exclude line_profiler ^
--exclude matplotlib ^
--exclude memory-profiler ^
--exclude numpy ^
--exclude objbrowser ^
--exclude pipdeptree ^
--exclude pp-ez ^
--exclude pyenchant ^
--exclude pylint ^
--exclude rich ^
--exclude tomlkit ^
--exclude Faker ^
--exclude mock ^
--exclude pytest ^
--exclude pytest-html ^
--exclude flit ^
--exclude flit_core ^
--exclude pylint ^
--exclude pipdeptree > frozen_deps.txt