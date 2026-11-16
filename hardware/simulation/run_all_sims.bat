@echo off
cd /d "%~dp0"
set NG="..\..\..\tools\Spice64\bin\ngspice_con.exe"
for %%s in (dc ac tran worstcase) do (
  echo Running %%s...
  %NG% -b sim_%%s.cir -o sim_%%s.log
)
echo.
echo Done: results in the .log and .csv files
pause
