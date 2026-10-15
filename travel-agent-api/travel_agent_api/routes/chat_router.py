from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from travel_agent_api.services.agent_service import Agent

router = APIRouter()


class ChatComplentionRequest(BaseModel):
    # Lista dei messaggi che compongono la conversazione
    messages: list

    # Esempio mostrato nella schermata di test in /docs
    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Vorrei organizzare un viaggio a Roma",
                    }
                ]
            }
        }
    }


@router.post("/travel-agent")
def chat_completion(request: ChatComplentionRequest):
    """
    Endpoint per la gestione delle richieste di chat.
    Processa i messaggi ricevuti e restituisce una risposta dall'agente di viaggio.

    Args:
        request (ChatComplentionRequest): La richiesta contenente i messaggi della conversazione

    Returns:
        dict: La risposta elaborata dall'agente di viaggio

    Raises:
        HTTPException: In caso di errori durante l'elaborazione della richiesta
    """
    try:
        agent = Agent()
        response = agent.run(messages=request.messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Tracing
    print("*" * 80)
    print("chat_completion")
    print("*" * 80)

    return response
