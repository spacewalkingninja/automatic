@ECHO OFF
:: Get Model path
:: %~dp0 = C:\users\[user]\Desota\Desota_Models\DeScraper\executables\Windows
for %%a in ("%~dp0..\..") do set "model_path=%%~fa"
:: Move to Model Path
call cd %model_path%
:: Delete Service Log on-start
break>%model_path%\service.log
:: Make sure every package required is installed
IF EXIST %model_path%\NSSM.flag GOTO mainloop
type nul > %model_path%\NSSM.flag
::call %model_path%\env\python -m pip install -r %model_path%\requirements.txt
:mainloop
:: Start Model Server
call %model_path%\webui.bat --docs --lowvram --ckpt .\models\Stable-diffusion\stable-diffusion-v1-5\v1-5-pruned.ckpt 
GOTO mainloop