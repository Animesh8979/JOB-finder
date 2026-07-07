@echo off
REM ============================================================
REM   _env_d_disk.bat - sourced by setup.bat / run.bat / build.bat
REM   Sets disk-discipline env vars so every cache lives on D:.
REM   User constraint: "no C disk usage, use only D disk".
REM   Set JOB_FINDER_DEEP_TEST=1 to enable verbose verification echoes.
REM   This file is ASCII-only on purpose - cmd.exe default codepage
REM   (437/CP-1252) mis-parses UTF-8 hyphens and em-dashes.
REM ============================================================

REM HuggingFace - model/tokenizer/dataset cache
if "%HF_HOME%"==""            set "HF_HOME=%~dp0data\hf_cache"
if "%HF_DATASETS_CACHE%"==""  set "HF_DATASETS_CACHE=%~dp0data\hf_datasets"
if "%TRANSFORMERS_CACHE%"=="" set "TRANSFORMERS_CACHE=%~dp0data\hf_cache\transformers"

REM tiktoken + fast tokenizers + sentence-transformers weights_download
if "%XDG_CACHE_HOME%"==""     set "XDG_CACHE_HOME=%~dp0data\xdg_cache"

REM PyTorch model cache (rarely used here, but set defensively)
if "%TORCH_HOME%"==""         set "TORCH_HOME=%~dp0data\torch_home"

REM Playwright browser binaries (also set in setup.bat - kept here so
REM run.bat-only invocations don't try to download Chromium to C:).
if "%PLAYWRIGHT_BROWSERS_PATH%"=="" set "PLAYWRIGHT_BROWSERS_PATH=%~dp0data\playwright_browsers"

REM pip download cache - keeps the wheel cache off C:
if "%PIP_CACHE_DIR%"==""      set "PIP_CACHE_DIR=%~dp0data\pip_cache"

REM npm cache (used by build.bat / frontend tooling) - keeps .npm off C:
if "%NPM_CONFIG_CACHE%"==""   set "NPM_CONFIG_CACHE=%~dp0data\npm_cache"

REM Create any missing dirs (idempotent - mkdir of an existing dir is OK).
if not exist "%HF_HOME%"            mkdir "%HF_HOME%"
if not exist "%HF_DATASETS_CACHE%"  mkdir "%HF_DATASETS_CACHE%"
if not exist "%TRANSFORMERS_CACHE%" mkdir "%TRANSFORMERS_CACHE%"
if not exist "%XDG_CACHE_HOME%"      mkdir "%XDG_CACHE_HOME%"
if not exist "%TORCH_HOME%"         mkdir "%TORCH_HOME%"
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" mkdir "%PLAYWRIGHT_BROWSERS_PATH%"
if not exist "%PIP_CACHE_DIR%"      mkdir "%PIP_CACHE_DIR%"
if not exist "%NPM_CONFIG_CACHE%"   mkdir "%NPM_CONFIG_CACHE%"

REM Embedder opt-in flag (see src/matcher.py docstring).
REM Default "" -> MiniLM. User can edit this to "BAAI/bge-small-en-v1.5"
REM to opt in to the higher-recall reranker once HF cache has been downloaded.
if "%JOB_FINDER_EMBEDDER%"=="" set "JOB_FINDER_EMBEDDER="

REM Ollama model storage - keeps GGUF weights off C:.
REM Ollama desktop reads OLLAMA_MODELS on startup; set it BEFORE launching the
REM the Ollama tray app. Default to D:\ollama_models (creates on first pull).
if "%OLLAMA_MODELS%"==""        set "OLLAMA_MODELS=D:\ollama_models"
if not exist "%OLLAMA_MODELS%"  mkdir "%OLLAMA_MODELS%"
REM Optional: override the default model (also settable in prefs as ollama_model).
if "%OLLAMA_MODEL%"==""         set "OLLAMA_MODEL="
REM Optional: override the Ollama server host (default http://127.0.0.1:11434).
if "%OLLAMA_HOST%"==""          set "OLLAMA_HOST="

if "%JOB_FINDER_DEEP_TEST%"=="1" (
  echo [env] HF_HOME=%HF_HOME%
  echo [env] TRANSFORMERS_CACHE=%TRANSFORMERS_CACHE%
  echo [env] XDG_CACHE_HOME=%XDG_CACHE_HOME%
  echo [env] PLAYWRIGHT_BROWSERS_PATH=%PLAYWRIGHT_BROWSERS_PATH%
  echo [env] PIP_CACHE_DIR=%PIP_CACHE_DIR%
  echo [env] NPM_CONFIG_CACHE=%NPM_CONFIG_CACHE%
  echo [env] JOB_FINDER_EMBEDDER=[%JOB_FINDER_EMBEDDER%]
)
