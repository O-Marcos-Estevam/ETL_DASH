from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

router = APIRouter()

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "credentials.json"))

# Static metadata for systems
SYSTEM_METADATA = {
    "amplis_reag": {
        "nome": "AMPLIS (REAG)",
        "descricao": "Importação de dados do AMPLIS (REAG)",
        "icone": "BarChart3",
        "ordem": 1,
        "opcoes": { "csv": True, "pdf": True }
    },
    "maps": {
        "nome": "MAPS",
        "descricao": "Upload e Processamento MAPS",
        "icone": "Map",
        "ordem": 2,
        "opcoes": { "excel": True, "pdf": True, "ativo": True, "passivo": True }
    },
    "fidc": {
        "nome": "FIDC",
        "descricao": "Gestão de Direitos Creditórios",
        "icone": "FileSpreadsheet",
        "ordem": 3
    },
    "jcot": {
        "nome": "JCOT",
        "descricao": "Integração JCOT",
        "icone": "Database",
        "ordem": 4
    },
    "britech": {
        "nome": "BRITECH",
        "descricao": "Integração BRITECH",
        "icone": "Server",
        "ordem": 5
    },
    "qore": {
        "nome": "QORE",
        "descricao": "Processamento XML QORE",
        "icone": "FileCode",
        "ordem": 6,
        "opcoes": { "excel": True, "pdf": True, "lote_pdf": False, "lote_excel": False }
    }
}

@router.get("/api/config")
async def get_config():
    """
    Reads credentials.json and transforms it to the ConfiguracaoETL structure expected by Frontend V2.
    """
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=404, detail="Configuration file not found")
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            creds = json.load(f)
            
        # Transform flat credentials into ConfiguracaoETL structure
        config = {
            "versao": creds.get("version", "2.0"),
            "ultimaModificacao": datetime.now().isoformat(),
            "periodo": {
                "dataInicial": None,
                "dataFinal": None,
                "usarD1Anbima": True
            },
            "sistemas": {}
        }
        
        # Merge static metadata with credentials presence
        for sys_id, meta in SYSTEM_METADATA.items():
            # Determine if system is active (logic can be improved)
            # For now, if it exists in credentials, it's available to be active
            
            # Map legacy keys if necessary (e.g., amplis_reag might be under amplis.reag)
            legacy_key = sys_id.split('_')[0] if '_' in sys_id else sys_id
            
            config["sistemas"][sys_id] = {
                "id": sys_id,
                "nome": meta["nome"],
                "descricao": meta["descricao"],
                "icone": meta["icone"],
                "ativo": True, # Default to true in dashboard
                "ordem": meta["ordem"],
                "opcoes": meta.get("opcoes", {}),
                "status": "IDLE"
            }
            
        # Add 'paths' to config root if needed or keep it hidden?
        # Frontend might expect paths elsewhere or we can attach them to a "System" called "Config"
        # But for now, let's just return what standard frontend expects.
        # Wait, the credentials form in frontend DOES use this endpoint to load credentials too.
        # But proper extraction should be: credentials are loaded via /api/config.
        
        # We attach the raw credentials object as well so the Settings form can find it?
        # Or does Settings form assume the structure matches credentials.json?
        # The Settings form uses ConfigService.getConfig(). 
        # If we change the return structure, CredentialsForm (which expects {maps: {...}, fidel: {...}}) will BREAK.
        
        # CRITICAL: CredentialsForm expects the RAW object structure (keys like 'maps', 'fidc' at root).
        # EtlPage expects { sistemas: ... }.
        
        # Solution: Return a Hybrid Object.
        # It contains the "sistemas" key for EtlPage, AND the raw keys for SettingsPage.
        
        response = creds.copy()
        response["sistemas"] = config["sistemas"]
        response["periodo"] = config["periodo"]
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading config: {str(e)}")

@router.post("/api/config")
async def update_config(config: Dict[str, Any]):
    """
    Updates credentials.json.
    Receives the full object. We must strip the 'sistemas'/'periodo' metadata before saving 
    to avoid polluting credentials.json with frontend-only state, OR we save it if we want persistence.
    
    Legacy scripts (main.py) might ignore unknown keys, so saving 'sistemas' might be benign,
    BUT it's safer to strip it to keep the file clean for the Java app/legacy scripts.
    """
    try:
        # Create a copy to modify
        data_to_save = config.copy()
        
        # keys to exclude from saving to credentials.json
        exclude_keys = ["sistemas", "periodo", "ultimaModificacao"]
        
        for key in exclude_keys:
            if key in data_to_save:
                del data_to_save[key]
        
        # Ensure version is preserved or updated
        data_to_save["version"] = data_to_save.get("version", "2.0")

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        
        return {"status": "success", "message": "Configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving config: {str(e)}")

@router.get("/api/config/paths")
async def get_paths():
    """Helper to get just paths"""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("paths", {})
