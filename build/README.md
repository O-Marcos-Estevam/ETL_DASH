# ETL Dashboard - Build Scripts
# ==============================
# 
# Este diretório contém os scripts para gerar o executável standalone.
#
# ## Pré-requisitos
#
# ```powershell
# pip install pyinstaller
# ```
#
# ## Estrutura
#
# ```
# build/
# ├── pyinstaller/
# │   ├── backend.spec    # Spec do backend
# │   ├── launcher.spec   # Spec do launcher
# │   └── launcher.py     # Código do launcher
# ├── scripts/
# │   ├── build_all.ps1   # Build completo
# │   └── build_backend.ps1
# └── installer/
#     └── setup.iss       # Inno Setup script
# ```
#
# ## Como buildar
#
# ```powershell
# cd build/scripts
# .\build_all.ps1
# ```
#
# ## Output
#
# ```
# dist/
# └── ETL_Dashboard/
#     ├── ETL_Dashboard.exe
#     ├── runtime/backend/
#     ├── web/
#     ├── config/
#     └── ...
# ```
