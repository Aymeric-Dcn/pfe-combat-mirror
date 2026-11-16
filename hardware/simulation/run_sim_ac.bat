@echo off
cd /d "%~dp0"
"..\..\..\tools\Spice64\bin\ngspice.exe" sim_ac.cir
